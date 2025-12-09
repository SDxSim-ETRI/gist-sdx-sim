import numpy as np
import matplotlib.pyplot as plt
import mujoco as mj
import copy

def check_collision(bbox1, bbox2, margin=0.02):
    """Check if two bounding boxes collide considering a margin."""
    bbox1_center = bbox1['center']
    bbox1_size = bbox1['size']
    bbox2_center = bbox2['center']
    bbox2_size = bbox2['size']

    vec_1_2 = np.array(bbox2_center) - np.array(bbox1_center)
    vec_1_2_abs = np.abs(vec_1_2)
    size_sum = (np.array(bbox1_size) + np.array(bbox2_size)) / 2

    if np.any(vec_1_2_abs > (size_sum + margin)):   # 최소 margin(2cm) 간격 유지
        return False, vec_1_2
    else:
        return True, vec_1_2

def resolve_collision(obj_bbox_list_, margin=0.02, check_z=False):
    obj_bbox_list = copy.deepcopy(obj_bbox_list_)
    while True:
        break_flag = True
        for i in range(len(obj_bbox_list)):
            for j in range(i + 1, len(obj_bbox_list)):
                collision, vec_1_2 = check_collision(obj_bbox_list[i], obj_bbox_list[j], margin)

                if 'delta_pos' not in obj_bbox_list[i].keys():
                    obj_bbox_list[i]['delta_pos'] = np.array([0.0, 0.0, 0.0])
                if 'delta_pos' not in obj_bbox_list[j].keys():
                    obj_bbox_list[j]['delta_pos'] = np.array([0.0, 0.0, 0.0])

                # vec_1_2: vector from bbox1 to bbox2
                if collision:
                    break_flag = False
                    # Resolve collision by shifting the second object slightly
                    if check_z:
                        bbox1_size = np.array(obj_bbox_list[i]['size'])
                        bbox2_size = np.array(obj_bbox_list[j]['size'])
                    else:
                        bbox1_size = np.array(obj_bbox_list[i]['size'][:2])
                        bbox2_size = np.array(obj_bbox_list[j]['size'][:2])
                        vec_1_2 = vec_1_2[:2]

                    non_collision_diff_each_axis = (bbox1_size + bbox2_size) / 2
                    shift_each_axis_for_non_collsion = non_collision_diff_each_axis - np.abs(vec_1_2)

                    dot_product_array = np.zeros_like(vec_1_2)
                    dot_product_array[0] = vec_1_2[0] * shift_each_axis_for_non_collsion[0] * (vec_1_2[0] / (np.linalg.norm(vec_1_2) + 1e-6))
                    dot_product_array[1] = vec_1_2[1] * shift_each_axis_for_non_collsion[1] * (vec_1_2[1] / (np.linalg.norm(vec_1_2) + 1e-6))
                    if len(dot_product_array) == 3:
                        dot_product_array[2] = vec_1_2[2] * shift_each_axis_for_non_collsion[2] * (vec_1_2[2] / (np.linalg.norm(vec_1_2) + 1e-6))

                    min_shift_axis = np.argmin(np.abs(dot_product_array))

                    target_diff = non_collision_diff_each_axis[min_shift_axis]
                    current_diff = np.abs(vec_1_2[min_shift_axis])

                    shift_diff = (target_diff-current_diff) / current_diff

                    # shift_vector = vec_1_2 * (shift_diff + margin*1.1) * 0.5
                    shift_vector = vec_1_2 * (0.05) * 0.5
                    if not check_z:
                        shift_vector = np.array([shift_vector[0], shift_vector[1], 0.0])

                    obj_bbox_list[j]['center'] += shift_vector
                    obj_bbox_list[j]['min'] += shift_vector
                    obj_bbox_list[j]['max'] += shift_vector
                    obj_bbox_list[j]['delta_pos'] += shift_vector

                    obj_bbox_list[i]['center'] -= shift_vector
                    obj_bbox_list[i]['min'] -= shift_vector
                    obj_bbox_list[i]['max'] -= shift_vector
                    obj_bbox_list[i]['delta_pos'] -= shift_vector

        if break_flag:
            break

    return obj_bbox_list, not collision

def vis_bboxes(obj_bbox_list):
    """Visualize bounding boxes using trimesh."""
    # 그래프 설정
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    for bbox in obj_bbox_list:
        min_pt = bbox['min']
        max_pt = bbox['max']

        # BBox의 x, y, z 좌표 범위
        x = [min_pt[0], max_pt[0]]
        y = [min_pt[1], max_pt[1]]
        z = [min_pt[2], max_pt[2]]
        
        # 8개의 꼭짓점 정의
        # (x_min, y_min, z_min) ... (x_max, y_max, z_max) 조합
        vertices = [
            [x[0], y[0], z[0]], [x[1], y[0], z[0]], [x[1], y[1], z[0]], [x[0], y[1], z[0]], # 바닥면
            [x[0], y[0], z[1]], [x[1], y[0], z[1]], [x[1], y[1], z[1]], [x[0], y[1], z[1]]  # 윗면
        ]
        
        # 12개의 모서리 연결 정보 (꼭짓점 인덱스)
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0], # 바닥면 테두리
            [4, 5], [5, 6], [6, 7], [7, 4], # 윗면 테두리
            [0, 4], [1, 5], [2, 6], [3, 7]  # 기둥(높이)
        ]
        
        # 모서리 그리기
        for edge in edges:
            p1 = vertices[edge[0]]
            p2 = vertices[edge[1]]
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], color='b')
            
        # 중심점 표시
        center = bbox['center']
        ax.scatter(center[0], center[1], center[2], color='r', s=50, label='Center')
        
        # 이름 텍스트 추가
        ax.text(center[0], center[1], center[2], bbox['name'], color='black')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('3D Bounding Box Visualization')

    # 비율을 맞추기 위한 설정 (Equal Aspect Ratio)
    # 축 범위를 데이터의 최대 범위에 맞춰서 정사각형 큐브 형태로 보이게 함
    all_min = np.min([b['min'] for b in obj_bbox_list], axis=0)
    all_max = np.max([b['max'] for b in obj_bbox_list], axis=0)
    max_range = (all_max - all_min).max() / 2.0
    mid = (all_max + all_min) / 2.0

    ax.set_xlim(mid[0] - max_range, mid[0] + max_range)
    ax.set_ylim(mid[1] - max_range, mid[1] + max_range)
    ax.set_zlim(mid[2] - max_range, mid[2] + max_range)

    plt.show()

def move_objects_by_prefix(model, data, positions_dict_list, disable_collision=True):
    """
    positions_dict_list: [{delta_pos: [dx,dy,dz], ...}, ...] - 상대 이동량
    disable_collision: True면 충돌 감지를 일시적으로 비활성화하여 끼여있는 물체도 이동 가능
    """
    # 충돌 설정 백업 및 비활성화
    if disable_collision:
        original_contype = model.geom_contype.copy()
        original_conaffinity = model.geom_conaffinity.copy()
        model.geom_contype[:] = 0
        model.geom_conaffinity[:] = 0

    # 모든 object body 찾기
    object_bodies = []
    for i in range(model.nbody):
        name = mj.mj_id2name(model, mj.mjtObj.mjOBJ_BODY, i)
        if name and "object" in name:
            object_bodies.append((i, name))

    for body_id, body_name in object_bodies:
        # body_name에서 인덱스 추출 (예: "objectobject_00-0" -> 0)
        idx = int(body_name.split('-')[-1])

        delta_pos = positions_dict_list[idx]['delta_pos']  # 상대 이동량

        jnt_adr = model.body_jntadr[body_id]
        if jnt_adr < 0:
            continue

        qpos_adr = model.jnt_qposadr[jnt_adr]
        qvel_adr = model.jnt_dofadr[jnt_adr]

        # 핵심 수정: 현재 위치에 delta를 더함 (= 이 아니라 +=)
        data.qpos[qpos_adr:qpos_adr+3] += delta_pos

        # velocity 초기화 (freejoint는 6 dof: 3 linear + 3 angular)
        if model.jnt_type[jnt_adr] == mj.mjtJoint.mjJNT_FREE:
            data.qvel[qvel_adr:qvel_adr+6] = 0

    # kinematics만 업데이트 (충돌 해결 없이 위치만 반영)
    mj.mj_kinematics(model, data)

    # 충돌 설정 복원
    if disable_collision:
        model.geom_contype[:] = original_contype
        model.geom_conaffinity[:] = original_conaffinity

    # 복원 후 forward로 정상 상태로
    mj.mj_forward(model, data)

def wait_until_stable(model, data, max_time=30.0, velocity_threshold=0.01):
    """물체들이 안정화될 때까지 시뮬레이션 진행"""
    while data.time < max_time:
        mj.mj_step(model, data)
        # 모든 body의 속도 체크
        max_velocity = np.max(np.abs(data.qvel))
        if max_velocity < velocity_threshold:
            print(f"안정화 완료! time={data.time:.2f}s, max_vel={max_velocity:.6f}")
            break
    else:
        print(f"최대 시간 도달. max_vel={np.max(np.abs(data.qvel)):.6f}")