import os
import numpy as np
import re
import mujoco as mj


def load_obj_names(obj_dir: str):
    # object_* 디렉토리 수집
    cand_names = [n for n in os.listdir(obj_dir)
                  if n.startswith("object_") and os.path.isdir(os.path.join(obj_dir, n))]
    # objects.json 위치 탐색: tmp/objects.json 또는 ../objects.json
    objjson_path = os.path.join(obj_dir, "objects.json")
    if not os.path.exists(objjson_path):
        objjson_path = os.path.join(os.path.dirname(obj_dir), "objects.json")

    # local_index로 필터링
    keep = []
    for n in cand_names:
        try:
            idx = int(n.split("_")[-1])
        except Exception:
            keep.append(n); continue
        keep.append(n)

    return sorted(keep)


def _collect_object_geom_ids(model):
    """
    루트 바디명이 'objectworld-<i>' / 'objectobject_00-<i>' 등으로 되어 있는
    imported object 들에 대해, 각 object 그룹별 geom id 리스트를 만든다.
    """
    try:
        names_buf = model.names
        body_adr = np.asarray(model.name_bodyadr, dtype=int)
        body_of_geom = np.asarray(model.geom_bodyid, dtype=int)

        nbody = int(model.nbody)
        ngeom = int(model.ngeom)
        buf_len = len(names_buf)

        def _get_name(adr_array, idx):
            start = int(adr_array[idx])
            if start < 0 or start >= buf_len:
                return ""
            end = buf_len
            for j in range(idx + 1, len(adr_array)):
                nxt = int(adr_array[j])
                if 0 <= nxt < buf_len and nxt > start:
                    end = nxt
                    break
            raw = names_buf[start:end]
            raw = raw.split(b"\x00", 1)[0]
            try:
                return raw.decode() if raw else ""
            except Exception:
                return ""

        body_names = [_get_name(body_adr, b) for b in range(nbody)]
        print("nbody : ", nbody)
        print("body names : ", body_names)

        group_id = -np.ones(nbody, dtype=int)
        for b in range(nbody):
            nm = body_names[b]
            if not nm.startswith("object"):
                continue
            m = re.search(r"-(\d+)$", nm)
            if not m:
                continue
            gid = int(m.group(1))
            group_id[b] = gid

        root_for_gid = {}
        for b in range(nbody):
            gid = group_id[b]
            if gid < 0:
                continue
            nm = body_names[b]
            root_for_gid.setdefault(gid, []).append(b)

        object_roots = {}
        for gid, blist in root_for_gid.items():
            world_candidates = [b for b in blist if "world" in body_names[b]]
            if world_candidates:
                rb = world_candidates[0]
            else:
                rb = min(blist)
            object_roots[gid] = rb

        root_for_body = -np.ones(nbody, dtype=int)
        for b in range(nbody):
            gid = group_id[b]
            if gid < 0:
                continue
            rb = object_roots.get(gid, None)
            if rb is None:
                continue
            root_for_body[b] = rb

        geom_groups = {}
        for g in range(ngeom):
            b = int(body_of_geom[g])
            if b < 0 or b >= nbody:
                continue
            rb = int(root_for_body[b])
            if rb < 0:
                continue
            root_name = body_names[rb]
            if not root_name.startswith("object"):
                continue
            geom_groups.setdefault(root_name, []).append(int(g))

        print("[DEBUG] geom_groups keys:", list(geom_groups.keys()))
        return geom_groups

    except Exception as e:
        print("[ERROR] _collect_object_geom_ids failed:", repr(e))
        return {}

def _compute_tight_scene_bounds(model, data, geom_groups):
    bbox_list = []

    for obj_name, gids in geom_groups.items():
        # 이 물체에 속한 모든 geom의 월드 좌표 점들을 모을 리스트
        all_world_verts = []

        for gid in gids:
            # 1. Geom의 타입 확인 (Mesh인지 Primitive인지)
            geom_type = model.geom_type[gid]
            
            # 2. Transform Matrix 계산 (Geom -> World)
            # data.geom_xpos: 월드 상의 Geom 중심
            # data.geom_xmat: 월드 상의 Geom 회전 행렬
            pos_world = data.geom_xpos[gid]
            mat_world = data.geom_xmat[gid].reshape(3, 3)
            
            local_verts = None

            if geom_type == mj.mjtGeom.mjGEOM_MESH:
                # --- MESH인 경우: 실제 버텍스 데이터 가져오기 ---
                dataid = model.geom_dataid[gid] # mesh ID 확인
                
                # mesh_vertadr: 해당 메쉬의 버텍스 시작 주소
                # mesh_vertnum: 해당 메쉬의 버텍스 개수
                vert_adr = model.mesh_vertadr[dataid]
                vert_num = model.mesh_vertnum[dataid]
                
                # 실제 버텍스 배열 가져오기 (N, 3)
                local_verts = model.mesh_vert[vert_adr : vert_adr + vert_num]
                
            elif geom_type == mj.mjtGeom.mjGEOM_BOX:
                # --- BOX인 경우: 8개 코너 계산 ---
                size = model.geom_size[gid] # (half_x, half_y, half_z)
                dx, dy, dz = size
                local_verts = np.array([
                    [-dx, -dy, -dz], [-dx, -dy, dz], [-dx, dy, -dz], [-dx, dy, dz],
                    [dx, -dy, -dz], [dx, -dy, dz], [dx, dy, -dz], [dx, dy, dz]
                ])
                
            else:
                # Sphere, Cylinder 등 다른 타입은 근사치로 처리하거나
                # 필요시 별도 로직 추가 (여기서는 geom_size 기반 박스로 처리)
                # 대부분의 시뮬레이션 에셋은 Mesh 또는 Box임
                size = model.geom_size[gid]
                # size[0], size[1], size[2]를 이용해 박스 형태로 근사
                # (구현 생략, 위 Box 로직과 유사하게 처리 가능)
                continue 

            if local_verts is not None:
                # 3. Local Vertex -> World Vertex 변환
                # World_V = R * Local_V + T
                world_verts = (mat_world @ local_verts.T).T + pos_world
                all_world_verts.append(world_verts)

        if not all_world_verts:
            continue

        # 4. 모든 버텍스를 합쳐서 Min/Max 계산
        all_world_verts = np.vstack(all_world_verts)
        bb_min = all_world_verts.min(axis=0)
        bb_max = all_world_verts.max(axis=0)

        bbox_dict = {
            'name': obj_name,
            'min': bb_min,
            'max': bb_max,
            'center': (bb_min + bb_max) / 2.0,
            'size': bb_max - bb_min
        }
        bbox_list.append(bbox_dict)

    return bbox_list
