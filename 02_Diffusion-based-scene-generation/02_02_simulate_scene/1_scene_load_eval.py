import mujoco as mj
import mujoco_viewer
import os
import matplotlib.pyplot as plt
import numpy as np
import cv2
from scipy.spatial.transform import Rotation as R
from PIL import Image
import trimesh
import argparse
import shutil

import json
from scipy.spatial.transform import Rotation as R
import numpy as np, trimesh

from xml.etree import ElementTree as ET
from utils.mj_file import load_obj_names, _collect_object_geom_ids, _compute_tight_scene_bounds
from utils.mujoco_basic import get_textured_arena, add_light, add_wall, get_global_bbox
from utils.solve_collision import resolve_collision, vis_bboxes, move_objects_by_prefix, wait_until_stable

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


object_class = ['Sofa', 'Lighting', 'Bed', 'Table', 'Cabinet', 'Stool', 'Chair', 'Others']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--obj_dir', 
        type=str, 
        default='data_1128_new_all/0001@00fe8139-76e8-42b4-bb41-7f9f085ac351_DiningRoom-15534_cfg1.0_1.0/tmp',)
        # default='data_1128_new_all/0001@00fe8139-76e8-42b4-bb41-7f9f085ac351_DiningRoom-15534_cfg1.0_1.0/tmp')
    args = parser.parse_args()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROBOT_PATH = os.path.join(BASE_DIR, 'models', 'assets', 'robots', 'franka_emika_panda')

    obj_dir = os.path.join(BASE_DIR, args.obj_dir)

    obj_name_list = load_obj_names(obj_dir)
    obj_xml_list  = [os.path.join(obj_dir, obj_name, f"{obj_name}.xml") for obj_name in obj_name_list]
    obj_xml_list.sort()

    for obj_name in obj_name_list:
        obj_num = obj_name.split('_')[-1]
        if not os.path.exists(os.path.join(obj_dir, obj_name, f'material_{obj_num}.png')):
            print(f"Error: material_{obj_num}.png does not exist")
            if not os.path.exists(os.path.join(obj_dir, f'material_{obj_num}.png')):
                print(f"Error: material_{obj_num}.png does not exist -> maybe bottom plane(.jpeg)")
            else:
                shutil.copy(os.path.join(obj_dir, f'material_{obj_num}.png'), os.path.join(obj_dir, obj_name, f'material_{obj_num}.png'))

    # select bottom plane .obj
    obj_list = [os.path.join(obj_dir, obj_name, f'{obj_name}.obj') for obj_name in obj_name_list]
    obj_list.sort(reverse=False)
    light_obj_idx_list = []
    for i, obj_path in enumerate(obj_list):
        mesh = trimesh.load(obj_path)
        vertices = mesh.vertices
        # Y좌표가 모두 같은지 확인 (바닥 평면은 Y가 일정함)
        if np.allclose(vertices[:, 1], vertices[0, 1]):
            print("이 OBJ는 바닥 평면입니다.")
            bottom_obj_name = obj_path.split('/')[-1].split('.')[0]
        elif np.min(vertices[:, 1]) > 1.0:
            print("이 OBJ는 조명입니다.")
            if i == int(obj_path.split('/')[-1].split('.')[0].split('_')[-1]):
                light_obj_idx_list.append(i)
            else:
                assert False, "조명 OBJ 이름이 인덱스와 맞지 않음"
        
    objects = []
    for obj_xml in obj_xml_list:
        if bottom_obj_name in obj_xml:
            continue
        spec = mj.MjSpec.from_file(obj_xml)

        # 물리 안정화: 각 geom에 접촉/마찰 파라미터 설정
        for g in spec.worldbody.geoms:
            g.contype = 1
            g.conaffinity = 1
            g.condim = 3
            g.friction = [1.0, 0.5, 0.1]  # 마찰력
            g.margin = 0.001
            g.solref = [0.02, 1.0]        # 접촉 강성/감쇠
            g.solimp = [0.9, 0.95, 0.001]
            # 밀도 설정 (질량 자동 계산)
            try:
                g.density = 1000.0  # kg/m^3 (물 밀도 기준, 필요시 조정)
            except:
                pass

        objects.append(spec)

    #* arena
    arena = mj.MjSpec()

    # 물리 시뮬레이션 안정화 설정
    if hasattr(arena, "compiler"):
        arena.compiler.inertiafromgeom = True
        arena.compiler.boundmass = 1e-3       # 최소 질량
        arena.compiler.boundinertia = 1e-3    # 최소 관성

    bottom_material_name = f"material_{bottom_obj_name.split('_')[1]}"
    floor_png_path = os.path.join(obj_dir, f'{bottom_material_name}.png')
    if not os.path.exists(floor_png_path):
        floor_jpeg_path = os.path.join(obj_dir, f'{bottom_material_name}.jpeg')
        img = Image.open(floor_jpeg_path)
        img.save(floor_png_path)

    get_textured_arena(arena, floor_png_path=floor_png_path, )

    #* add object
    for i, spec in enumerate(objects):
        # XZ는 겹침해소 좌표, Y는 0으로 고정
        # spawn_pos = (float(dxy[i,0]), float(dxy[i,1]), 0.0)
        spawn_pos = (0, 0, 0)
        spawn_quat = R.from_euler('xyz', [180, 0, 90], degrees=True).as_quat()
        spawn_site = arena.worldbody.add_site(pos=spawn_pos, quat=spawn_quat, group=3)

        spawn_body = spawn_site.attach_body(spec.worldbody, 'object', '-' + str(i))

        if i not in light_obj_idx_list:
            spawn_body.add_freejoint()  # 자유롭게 움직임
    
    #* render
    model = arena.compile()

    # 물리 시뮬레이션 안정화 파라미터
    model.opt.gravity[:] = [0, 0, -9.81]
    model.opt.timestep = 0.002          # 더 작은 timestep (기본 0.002)
    model.opt.iterations = 50           # 솔버 반복 횟수 증가 (기본 100)
    model.opt.tolerance = 1e-8          # 수렴 허용치
    model.opt.integrator = mj.mjtIntegrator.mjINT_IMPLICITFAST  # 안정적인 적분기

    # 전역 damping 설정 (움직임 감쇠)
    model.dof_damping[:] = 5.0          # 모든 자유도에 damping 적용
    
    data = mj.MjData(model)

    # 물체 배치 적용을 위한 forward one step
    mj.mj_step(model, data)


    #* 물체 3D bbox 계산
    geom_groups = _collect_object_geom_ids(model)
    obj_bbox_list = _compute_tight_scene_bounds(model, data, geom_groups)

    light_bbox_list = []
    for light_obj_idx in light_obj_idx_list:
        light_bbox_list.append(obj_bbox_list[light_obj_idx])

    # 안정화 후 물체 3D bbox 출력
    print("\n=== 물체 3D Bounding Box ===")

    description_txt_path = os.path.join(BASE_DIR, os.path.dirname(args.obj_dir), 'description.txt')
    with open(description_txt_path, 'r', encoding='utf-8') as f:
        description = f.read().strip()
    json_dict = {
        "scene_dir": os.path.dirname(args.obj_dir),
        "scene": os.path.basename(os.path.dirname(args.obj_dir)),
        "description": description,
        "objects": {}
    }

    objects_json_path = os.path.join(BASE_DIR, os.path.dirname(args.obj_dir), 'objects_mj.json')
    with open(objects_json_path, 'r', encoding='utf-8') as f:
        objects_meta = json.load(f)
    obj_data = objects_meta['objects']

    # get obj_bbox_list and resolve collision issue
    refined_obj_bbox_list, _ = resolve_collision(obj_bbox_list, margin=0.2, check_z=False)
    # # vis_bboxes(refined_obj_bbox_list)

    #* add a lights and walls
    global_bbox = get_global_bbox(refined_obj_bbox_list)
    add_light(arena, light_bbox_list, global_bbox)
    add_wall(arena, global_bbox)
    
    for i, obj_bbox in enumerate(refined_obj_bbox_list):
    # for i, obj_bbox in enumerate(obj_bbox_list):
        i = str(i)

        name = obj_bbox['name']

        mj_obj_idx = int(name.split('-')[-1])
        for obj in obj_data:
            if obj['local_index'] == mj_obj_idx:
                ailab_category = obj['mj_class']   #.lower(),
                obj_class = obj['mj_class_id']
                obj_id = obj['local_index']
                break

        x_min, y_min, z_min = obj_bbox['min']
        x_max, y_max, z_max = obj_bbox['max']

        corners = [
            [x_min, y_min, z_min],
            [x_min, y_min, z_max],
            [x_min, y_max, z_min],
            [x_min, y_max, z_max],
            [x_max, y_min, z_min],
            [x_max, y_min, z_max],
            [x_max, y_max, z_min],
            [x_max, y_max, z_max],
        ]

        json_dict["objects"][i] = {
            "ailab_category": ailab_category,
            "class_id": obj_class,
            "corners": corners,
        }

        json_save_path = objects_json_path.replace('objects_mj.json', 'objects_mj_eval.json')
        with open(json_save_path, 'w', encoding='utf-8') as f:
            json.dump(json_dict, f, indent=4)

    # print obj_bbox_list
    for obj_bbox in refined_obj_bbox_list:
        name = obj_bbox['name']
        center = obj_bbox['center']
        size = obj_bbox['size']
        print(f"{name}:")
        print(f"  center: [{center[0]:.3f}, {center[1]:.3f}, {center[2]:.3f}]")
        print(f"  size:   [{size[0]:.3f}, {size[1]:.3f}, {size[2]:.3f}]")
        print(f"  min:    [{obj_bbox['min'][0]:.3f}, {obj_bbox['min'][1]:.3f}, {obj_bbox['min'][2]:.3f}]")
        print(f"  max:    [{obj_bbox['max'][0]:.3f}, {obj_bbox['max'][1]:.3f}, {obj_bbox['max'][2]:.3f}]")
    
    #* scene viewer 
    # create the viewer object
    model = arena.compile()
    data = mj.MjData(model)
    # 충돌 방지를 위한 기존 물체 배치 수정
    move_objects_by_prefix(model, data, refined_obj_bbox_list)
    # # 안정화 대기
    print("물체 안정화 중...")
    wait_until_stable(model, data, max_time=3.0, velocity_threshold=0.01)


    # viewer = mujoco_viewer.MujocoViewer(model, data)

    # # 또는 한번에 설정
    # viewer.cam.fixedcamid = -1  # 고정 카메라 사용 안함
    # viewer.cam.type = mj.mjtCamera.mjCAMERA_FREE  # 자유 카메라 모드
    # viewer.cam.distance = 8.0
    # viewer.cam.azimuth = 90
    # viewer.cam.elevation = -30
    # viewer.cam.lookat = [0, 0, 0]

    # # 뷰어 루프
    # while viewer.is_alive:
    #     viewer.render()
    #     mj.mj_step(model, data)

    # viewer.close()
    # cv2.waitKey(0)
