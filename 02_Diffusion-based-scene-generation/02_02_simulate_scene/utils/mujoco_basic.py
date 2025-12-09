import mujoco as mj
import numpy as np

def get_textured_arena(arena, floor_png_path):
    # 1. 사용자 정의 texture 추가
    custom_texture = arena.add_texture(
        name="custom_floor",
        type=mj.mjtTexture.mjTEXTURE_2D,
        file=floor_png_path,
    )

    # 2. material 정의
    custom_material = arena.add_material(
        name="custom_material",
        textures=["", "custom_floor"],      # texture_index = mujoco.mjtTextureRole.mjTEXROLE_RGB -> 1
        texrepeat=[8, 8],  # texture 반복 횟수
        reflectance=0.0,      # 반사율 (0-1, 0이면 반사 없음)
        shininess=0.0,        # 광택 집중도 (0-1, 0이면 확산됨)
        specular=0.0,         # 반사광 강도 (0-1, 0이면 반사광 없음)
        texuniform=True,
        rgba=[1, 1, 1, 1]  # material 색상
    )


    # 3. 바닥에 texture 적용 (마찰력 추가)
    arena.worldbody.add_geom(
        type=mj.mjtGeom.mjGEOM_PLANE,
        size=[6, 6, .1],
        material="custom_material",
        friction=[1.0, 0.5, 0.1],  # [sliding, torsional, rolling] 마찰력
        contype=1,
        conaffinity=1,
    )

    return arena

def get_default_arena(arena):       # arena is a mj.MjSpec
    if hasattr(arena, 'compiler'):
        arena.compiler.degree = False  # MuJoCo dev (next release).
    else:
        arena.degree = False  # MuJoCo release

    # Make arena with textured floor.
    chequget_textured_arenaered = arena.add_texture(
        name="chequered", type=mj.mjtTexture.mjTEXTURE_2D,
        builtin=mj.mjtBuiltin.mjBUILTIN_CHECKER,
        width=1000, height=1000, rgb1=[.2, .3, .4], rgb2=[.3, .4, .5])
        
    arena.worldbody.add_geom(
        type=mj.mjtGeom.mjGEOM_PLANE, size=[6, 6, .1], material='grid')
    for x in [-6, 6]:
        arena.worldbody.add_light(pos=[x, -1, 3], dir=[-x, 1, -2])

    return arena

def get_global_bbox(bbox_list):
    # None 제거
    bbox_list = [bbox for bbox in bbox_list if bbox is not None]

    # 모든 BBOX의 최소/최대 좌표를 하나의 배열로 모음
    all_mins = np.array([bbox['min'] for bbox in bbox_list])
    all_maxs = np.array([bbox['max'] for bbox in bbox_list])
    
    # 전체 BBOX의 최소/최대 좌표 계산
    global_min = np.min(all_mins, axis=0)
    global_max = np.max(all_maxs, axis=0)
    
    # 전체 BBOX 정보 계산
    global_bbox = {
        'min': global_min,
        'max': global_max,
        'size': global_max - global_min,
        'center': (global_max + global_min) / 2
    }
    
    return global_bbox


def make_wall(size, pos):
    xml = f"""
    <mujoco>
        <worldbody>
            <geom name="wall_unit" type="box" size="{size}" pos="{pos}" rgba="1 1 1 1"/>
        </worldbody>
    </mujoco>
    """

    return mj.MjSpec.from_string(xml)

def add_light(arena, light_bbox_list, global_bbox):

    if light_bbox_list:
        #todo: 조명 위치에 light 추가
        for light_bbox in light_bbox_list:
            x, y, z = light_bbox['center']
            z -= light_bbox['size'][2]/2
            arena.worldbody.add_light(pos=[x, y, z], dir=[0, 0, -1], diffuse=[30, 30, 30], specular=[.0, .0, .0], attenuation=[1, 1, 1], cutoff=90)
    
    else:   # default light 추가
        # add a light
        x_max, x_min = global_bbox['max'][0], global_bbox['min'][0]
        y_max, y_min = global_bbox['max'][1], global_bbox['min'][1]
        z_max, z_min = global_bbox['max'][2], global_bbox['min'][2]

        x_len = (global_bbox['max'][0]-global_bbox['min'][0])

        x_unit = x_len / 4
        x1 = x_min + x_unit
        x2 = x_max - x_unit
        y0 = global_bbox['center'][1]
        for x in [x1, x2]:
            arena.worldbody.add_light(pos=[x, y0, z_max+1.0], dir=[0, 0, -1], diffuse=[30, 30, 30], specular=[.0, .0, .0], attenuation=[1, 1, 1], cutoff=90)


def add_wall(arena, global_bbox):
    offset = 0.5
    # x_max, x_min = global_bbox['max'][0]+offset, global_bbox['min'][0]-offset
    # y_max, y_min = -global_bbox['min'][2]+offset, -global_bbox['max'][2]-offset
    # z_max, z_min = global_bbox['max'][1]+offset, global_bbox['min'][1]+0.01

    x_max, x_min = global_bbox['max'][0]+offset, global_bbox['min'][0]-offset
    y_max, y_min = global_bbox['max'][1]+offset, global_bbox['min'][1]-offset
    z_max, z_min = global_bbox['max'][2]+offset, global_bbox['min'][2]+0.01


    x_len, y_len, z_len = (x_max-x_min), (y_max-y_min), (z_max-z_min)

    size_list = [[0.1, y_len, z_len], [0.1, y_len, z_len], [x_len, 0.1, z_len], [x_len, 0.1, z_len]]
    pos_list = [(x_max, y_min+y_len/2, z_min+z_len/2), (x_min, y_min+y_len/2, z_min+z_len/2), (x_min+x_len/2, y_max, z_min+z_len/2), (x_min+x_len/2, y_min, z_min+z_len/2)]
    #* add wall
    # wall_quat = R.from_euler('xyz', [180, 0, 90], degrees=True).as_quat()
    wall_quat = [1, 0, 0, 0]
    for i in range(4):
        if i == 3:
            continue        #! temporary wall removing for vis
        wall_size = f"{size_list[i][0]/2} {size_list[i][1]/2} {size_list[i][2]/2}"
        wall_pos = "0. 0. 0."

        wall_spec = make_wall(size=wall_size, pos=wall_pos)
        spawn_site_wall = arena.worldbody.add_site(pos=np.array([pos_list[i][0], pos_list[i][1], pos_list[i][2]]), quat=wall_quat, group=3)
        # Attach to the arena at the spawn sites, with a free joint.
        spawn_site_wall.attach_body(wall_spec.worldbody, 'wall', '-' + str(i))


