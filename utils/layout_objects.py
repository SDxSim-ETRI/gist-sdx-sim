import mujoco
import mujoco_viewer
import os
import xml.etree.ElementTree as ET
import json
from simple_pid import PID
import math


# base dir is the root directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUNITURE_ROOT = os.path.join(BASE_DIR, 'models', 'assets', 'furniture')
FUNITURE_LIST_PATH = os.path.join(BASE_DIR, 'config', 'furniture_list.json')
FUNITURE_POSE_PATH = os.path.join(BASE_DIR, 'config', 'furniture_poses.json')

OBJECT_ROOT = os.path.join(BASE_DIR, 'models', 'assets', 'objects')
TEXTURES_PATH = os.path.join(BASE_DIR, 'models', 'assets', 'textures')
ARENAS_PATH = os.path.join(BASE_DIR, 'models', 'assets', 'arenas', 'ground.xml') #room.xml
ROBOT_PATH = os.path.join(BASE_DIR, 'models', 'assets', 'robots', 'franka_emika_panda')

class Models:
    assets_root = OBJECT_ROOT

models = Models()

def xml_path_completion(xml_path, base_dir=Models.assets_root):
    if os.path.isabs(xml_path):
        full_path = xml_path
    else:
        full_path = os.path.join(base_dir, xml_path)
    
    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"XML 파일을 찾을 수 없습니다: {full_path}")
    
    return full_path

def load_base_scene(base_scene_path):
    tree = ET.parse(base_scene_path)
    return tree.getroot()


def add_freejoint_to_body(body_element):
    if body_element.find('joint') is None:
        body_name = body_element.get('name', 'unnamed_body')
        joint_name = f"{body_name}_freejoint"
        free_joint = ET.SubElement(body_element, 'joint', attrib={
            'type': 'free',
            'name': joint_name
        })
        
def add_actuator(base_root, joint_name, object_file):
    """
    Add an actuator to control the specified joint in the object with unique names.
    """
    base_actuator = base_root.find('actuator')
    if base_actuator is None:
        # Create <actuator> element if it doesn't exist
        base_actuator = ET.SubElement(base_root, 'actuator')

    # Generate a unique actuator name
    actuator_name = f"{object_file.split('.')[0]}_{joint_name}_motor"
    actuator = ET.Element('motor', attrib={
        'joint': f"{object_file.split('.')[0]}_{joint_name}",
        'ctrlrange': '-5.0 5.0',
        'gear': '30',
        'name': actuator_name
    })

    # Add the actuator to the base model
    base_actuator.append(actuator)
    # print(f"Added actuator: {actuator_name} for joint: {joint_name} in object: {object_file}")


def update_default_element(default_element, object_file):
    
    # Update class attribute
    if 'class' in default_element.attrib:
        original_class_name = default_element.attrib['class']
        new_class_name = f"{object_file.split('.')[0]}_{original_class_name}"
        default_element.attrib['class'] = new_class_name

    # Update childclass attribute
    if 'childclass' in default_element.attrib:
        original_childclass = default_element.attrib['childclass']
        new_childclass = f"{object_file.split('.')[0]}_{original_childclass}"
        default_element.attrib['childclass'] = new_childclass

    # Update nested elements recursively
    for child in default_element:
        if child.tag == 'default':
            # Recursively update nested <default> elements
            update_default_element(child, object_file)

        else:
            # Update class attributes in other elements
            if 'class' in child.attrib:
                original_class = child.attrib['class']
                new_class = f"{object_file.split('.')[0]}_{original_class}"
                child.attrib['class'] = new_class
            # Update material references if any
            if 'material' in child.attrib:
                original_material = child.attrib['material']
                new_material = f"{object_file.split('.')[0]}_{original_material}"
                child.attrib['material'] = new_material

    

def update_body_element(body_element, object_file):
    # Update names and references in body element
    if 'name' in body_element.attrib:
        original_body_name = body_element.attrib['name']
        new_body_name = f"{object_file.split('.')[0]}_{original_body_name}"
        body_element.attrib['name'] = new_body_name

    # Update childclass
    if 'childclass' in body_element.attrib:
        original_childclass = body_element.attrib['childclass']
        new_childclass = f"{object_file.split('.')[0]}_{original_childclass}"
        body_element.attrib['childclass'] = new_childclass

    if 'class' in body_element.attrib:
        original_class = body_element.attrib['class']
        new_class = f"{object_file.split('.')[0]}_{original_class}"
        body_element.attrib['class'] = new_class

    # Recursive update for nested bodies
    for nested_body in body_element.findall('body'):
        update_body_element(nested_body, object_file)

    # Update joints
    for joint in body_element.findall('joint'):
        if 'name' in joint.attrib:
            original_joint_name = joint.attrib['name']
            new_joint_name = f"{object_file.split('.')[0]}_{original_joint_name}"
            joint.attrib['name'] = new_joint_name

        if 'class' in joint.attrib:
            original_class = joint.attrib['class']
            new_class = f"{object_file.split('.')[0]}_{original_class}"
            joint.attrib['class'] = new_class

    # Update actuators (for actuators related to joints in this body)
    base_actuator = body_element.find('actuator')
    if base_actuator is not None:
        for motor in base_actuator.findall('motor'):
            if 'joint' in motor.attrib:
                original_joint_name = motor.attrib['joint']
                new_joint_name = f"{object_file.split('.')[0]}_{original_joint_name}"
                motor.attrib['joint'] = new_joint_name
            if 'name' in motor.attrib:
                original_motor_name = motor.attrib['name']
                new_motor_name = f"{object_file.split('.')[0]}_{original_motor_name}"
                motor.attrib['name'] = new_motor_name

    for sensor in body_element.findall('sensor'):
        if 'name' in sensor.attrib:
            original_sensor_name = sensor.attrib['name']
            new_sensor_name = f"{object_file.split('.')[0]}_{original_sensor_name}"
            sensor.attrib['name'] = new_sensor_name

        # Update joint reference in sensor
        if 'joint' in sensor.attrib:
            original_joint_ref = sensor.attrib['joint']
            new_joint_ref = f"{object_file.split('.')[0]}_{original_joint_ref}"
            sensor.attrib['joint'] = new_joint_ref

    # Update sites
    for site in body_element.findall('site'):
        if 'name' in site.attrib:
            original_site_name = site.attrib['name']
            site.attrib['name'] = f"{object_file.split('.')[0]}_{original_site_name}"

    # Update geoms
    for geom in body_element.findall('geom'):
        if 'name' in geom.attrib:
            original_geom_name = geom.attrib['name']
            geom.attrib['name'] = f"{object_file.split('.')[0]}_{original_geom_name}"

        # Update material reference
        if 'material' in geom.attrib:
            original_material = geom.attrib['material']
            new_material = f"{object_file.split('.')[0]}_{original_material}"
            geom.attrib['material'] = new_material

        # Update mesh reference
        if 'mesh' in geom.attrib:
            original_mesh = geom.attrib['mesh']
            new_mesh = f"{object_file.split('.')[0]}_{original_mesh}"
            geom.attrib['mesh'] = new_mesh

        # **Update class reference**
        if 'class' in geom.attrib:
            original_class = geom.attrib['class']
            new_class = f"{object_file.split('.')[0]}_{original_class}"
            geom.attrib['class'] = new_class

    # Update any child elements recursively
    for child in body_element:
        if child.tag not in ['body', 'geom', 'joint', 'site']:
            update_body_element(child, object_file)



def add_object_to_scene(base_root, object_file, pose, assets_dir, parent_furniture=None):
    
    object_path = os.path.join(assets_dir, object_file)
    if not os.path.exists(object_path):
        # If the object is not found in the main directory, try the temporary directory
        object_path = os.path.join(OBJECT_ROOT, object_file)
        if not os.path.exists(object_path):
            raise FileNotFoundError(f"Object file {object_file} not found in both {assets_dir}")
    object_tree = ET.parse(object_path)
    object_root = object_tree.getroot()
    
    # Apply scaling based on object_file
    scale_factor = get_scale_factor(object_file)
    scale_model(object_root, scale_factor)

    # Merge <compiler> elements
    object_compiler = object_root.find('compiler')
    if object_compiler is not None:
        base_compiler = base_root.find('compiler')
        if base_compiler is None:
            # Create a new <compiler> element and insert it at the top
            base_root.insert(0, object_compiler)
        else:
            # Merge compiler attributes
            for key, value in object_compiler.attrib.items():
                base_compiler.set(key, value)

    # Merge <asset> elements
    base_assets = base_root.find('asset')
    object_assets = object_root.find('asset')
    if object_assets is not None:
        if base_assets is None:
            # Create a new <asset> element and insert it before <worldbody>
            base_assets = ET.Element('asset')
            # Find the index of <worldbody> to insert before it
            worldbody_index = list(base_root).index(base_root.find('worldbody'))
            base_root.insert(worldbody_index, base_assets)
            
        base_material_names = {mat.get('name') for mat in base_assets.findall('material')}
        base_texture_names = {tex.get('name') for tex in base_assets.findall('texture')}
        base_mesh_names = {mesh.get('name') for mesh in base_assets.findall('mesh')}
            
        # Process materials, textures, and meshes
        for asset in list(object_assets):
            if asset.tag == 'material':
                original_name = asset.get('name')
                new_name = f"{object_file.split('.')[0]}_{original_name}"
                asset.set('name', new_name)
                # Update material's texture reference if any
                if 'texture' in asset.attrib:
                    texture_ref = asset.get('texture')
                    new_texture_ref = f"{object_file.split('.')[0]}_{texture_ref}"
                    asset.set('texture', new_texture_ref)
                # Check for duplicates
                if new_name not in base_material_names:
                    base_assets.append(asset)
                    base_material_names.add(new_name)

                # class 업데이트
                if 'class' in asset.attrib:
                    original_class = asset.attrib['class']
                    new_class = f"{object_file.split('.')[0]}_{original_class}"
                    asset.set('class', new_class)

            elif asset.tag == 'texture':
                original_name = asset.get('name')
                new_name = f"{object_file.split('.')[0]}_{original_name}"
                asset.set('name', new_name)
                if 'file' in asset.attrib:
                    relative_path = asset.get('file')
                    # Adjust the texture path to be relative to the current working directory
                    absolute_texture_path = os.path.abspath(os.path.join(os.path.dirname(object_path), relative_path))
                    relative_texture_path = os.path.relpath(absolute_texture_path, start=os.getcwd())
                    asset.set('file', relative_texture_path)
                # Check for duplicates
                if new_name not in base_texture_names:
                    base_assets.append(asset)
                    base_texture_names.add(new_name)

            elif asset.tag == 'mesh':
                # Ensure the file path exists and is correct
                if 'file' in asset.attrib:
                    relative_path = asset.get('file')
                    absolute_mesh_path = os.path.abspath(os.path.join(os.path.dirname(object_path), relative_path))
                    relative_mesh_path = os.path.relpath(absolute_mesh_path, start=os.getcwd())
                    asset.set('file', relative_mesh_path)

                # Process mesh naming
                original_name = asset.get('name')
                if not original_name:
                    original_name = os.path.splitext(asset.get('file'))[0]
                new_name = f"{object_file.split('.')[0]}_{original_name}"
                asset.set('name', new_name)

                # Check for duplicates
                if new_name not in base_mesh_names:
                    base_assets.append(asset)
                    base_mesh_names.add(new_name)

                if 'class' in asset.attrib:
                    original_class = asset.attrib['class']
                    new_class = f"{object_file.split('.')[0]}_{original_class}"
                    asset.set('class', new_class)

            else:
                # For other asset types, handle them similarly if needed
                base_assets.append(asset)

    # Merge <default> elements
    base_default = base_root.find('default')
    object_default = object_root.find('default')
    if object_default is not None:
        if base_default is None:
            # Create a new <default> element and insert it before <worldbody>
            base_default = ET.Element('default')
            # Find the index of <worldbody> to insert before it
            worldbody_index = list(base_root).index(base_root.find('worldbody'))
            base_root.insert(worldbody_index, base_default)
        else:
            pass

        for default in list(object_default):
            # Update the class and childclass in default elements
            update_default_element(default, object_file)
            base_default.append(default)
    
    # Merge <actuator> elements
    base_actuator = base_root.find('actuator')
    object_actuator = object_root.find('actuator')
    if object_actuator is not None:
        if base_actuator is None:
            # Create a new <actuator> element and insert it before <worldbody>
            base_actuator = ET.Element('actuator')
            # Find the index of <worldbody> to insert before it
            worldbody_index = list(base_root).index(base_root.find('worldbody'))
            base_root.insert(worldbody_index, base_actuator)
        else:
            # Use existing base_actuator
            pass

        for actuator in list(object_actuator):
            # Update actuator names and joint references
            if 'name' in actuator.attrib:
                original_actuator_name = actuator.attrib['name']
                new_actuator_name = f"{object_file.split('.')[0]}_{original_actuator_name}"
                actuator.attrib['name'] = new_actuator_name
            if 'joint' in actuator.attrib:
                original_joint_name = actuator.attrib['joint']
                new_joint_name = f"{object_file.split('.')[0]}_{original_joint_name}"
                actuator.attrib['joint'] = new_joint_name

            if 'class' in actuator.attrib:
                original_actuator_name = actuator.attrib['class']
                new_actuator_name = f"{object_file.split('.')[0]}_{original_actuator_name}"
                actuator.attrib['class'] = new_actuator_name

            base_actuator.append(actuator)

    # Merge <sensor> elements
    base_sensor = base_root.find('sensor')
    object_sensor = object_root.find('sensor')
    if object_sensor is not None:
        if base_sensor is None:
            # Create a new <sensor> element and insert it before <worldbody>
            base_sensor = ET.Element('sensor')
            # Find the index of <worldbody> to insert before it
            worldbody_index = list(base_root).index(base_root.find('worldbody'))
            base_root.insert(worldbody_index, base_sensor)
        else:
            # Use existing base_sensor
            pass

        for sensor in list(object_sensor):
            # Update sensor names and joint references
            if 'name' in sensor.attrib:
                original_sensor_name = sensor.attrib['name']
                new_sensor_name = f"{object_file.split('.')[0]}_{original_sensor_name}"
                sensor.attrib['name'] = new_sensor_name

            if 'joint' in sensor.attrib:
                original_joint_name = sensor.attrib['joint']
                new_joint_name = f"{object_file.split('.')[0]}_{original_joint_name}"
                sensor.attrib['joint'] = new_joint_name

            base_sensor.append(sensor)

    # Merge <tendon> elements
    base_tendon = base_root.find('tendon')
    object_tendon = object_root.find('tendon')
    if object_tendon is not None:
        if base_tendon is None:
            # Create a new <tendon> element and insert it before <worldbody>
            base_tendon = ET.Element('tendon')
            # Find the index of <worldbody> to insert before it
            worldbody_index = list(base_root).index(base_root.find('worldbody'))
            base_root.insert(worldbody_index, base_tendon)
        else:
            # Use existing base_tendon
            pass

        for tendon in list(object_tendon):
            # Update tendon names and joint references
            if 'name' in tendon.attrib:
                original_tendon_name = tendon.attrib['name']
                new_tendon_name = f"{object_file.split('.')[0]}_{original_tendon_name}"
                tendon.attrib['name'] = new_tendon_name

            if 'joint' in tendon.attrib:
                original_joint_name = tendon.attrib['joint']
                new_joint_name = f"{object_file.split('.')[0]}_{original_joint_name}"
                tendon.attrib['joint'] = new_joint_name

            base_tendon.append(tendon)

    # Merge <worldbody> elements
    base_worldbody = base_root.find('worldbody')
    object_worldbody = object_root.find('worldbody')

    if object_worldbody is not None:
        root_bodies = list(object_worldbody)
        if not root_bodies:
            print(f"No bodies found in {object_file}")
            return

        wrapper_body = ET.Element('body', attrib={
            'name': f"{object_file.split('.')[0]}_body"
        })

        for child in root_bodies:
            wrapper_body.append(child)

        if parent_furniture:

            furniture_size = get_furniture_size(parent_furniture)
            furniture_scale = get_scale_factor(parent_furniture)
            furniture_center = get_furniture_center(parent_furniture)
            # change the object's position relative position to absolute position
            absolute_pos = [
                furniture_center[i] + (pose['pos'][i] * furniture_size[i] / 2)
                for i in range(2)
            ]
            if 'assets/objects' in assets_dir:
                absolute_pos.append(pose['pos'][2]*furniture_scale)
            else:
                absolute_pos.append(pose['pos'][2]*furniture_scale)

            wrapper_body.set('pos', ' '.join(map(str, absolute_pos)))
        else:
            
            # 위치와 자세 설정
            if 'pos' in pose:
                wrapper_body.set('pos', ' '.join(map(str, pose['pos'])))
            if 'quat' in pose:
                wrapper_body.set('quat', ' '.join(map(str, pose['quat'])))

        update_body_element(wrapper_body, object_file)
            
        # Apply freejoint only if the object is not furniture
        if 'furniture' not in object_path.lower() and 'robot' not in object_path.lower():
            add_freejoint_to_body(wrapper_body)

        # add_freejoint_to_body(wrapper_body)

        base_worldbody.append(wrapper_body)
    print(f"{object_file} added to the scene")

def get_furniture_size(furniture_name):
    with open(FUNITURE_LIST_PATH, 'r') as f:
        furniture_data = json.load(f)
    return furniture_data[furniture_name]['size']


def get_furniture_center(furniture_name):
    with open(FUNITURE_POSE_PATH, 'r') as f:
        furniture_poses = json.load(f)
    return furniture_poses[furniture_name]['pos']


def get_furniture_com(furniture_name):
    with open(FUNITURE_LIST_PATH, 'r') as f:
        furniture_data = json.load(f)
    return furniture_data[furniture_name]['com']



def get_scale_factor(object_file):
    """
    Returns the scale factor based on the object_file name.

    Parameters:
    - object_file (str): The filename of the object.

    Returns:
    - float: The scale factor to be applied.
    """
    # Define scaling mappings first
    scale_mapping = {
        'bin_1.xml': 1,
        'bin_2.xml': 1,
        'cabinet_1.xml': 0.7,
        'cabinet_2.xml': 0.7,
        'kettle_1.xml': 1,
        'kettle_2.xml': 1,
        'kettle_3.xml': 1,
        'kettle_4.xml': 1,
        'microwave_1.xml': 0.7,
        'microwave_2.xml': 0.7,
        'microwave_3.xml': 0.7,
        'simpleTable_marble.xml': 0.8,
        'simpleTable_wood.xml': 0.8,
        'vanity.xml': 0.9,
        'ventionTable.xml': 0.8,
        'counters.xml': 0.5,
        'dishwasher.xml': 0.8,
        'oven.xml': 0.8,
        'custom_cylinder.xml': 0.6,
        "can.xml": 1,
        "bottle.xml": 1,
        "bread.xml": 1,
        "cereal.xml": 1,
        "milk.xml": 1,
        "arch_box.xml": 1,
        "lemon.xml": 1,
        "Trowel.xml": 0.8,
        "table_billsta_round_0189.xml": 1.5,
        "door.xml": 1.7
    }

    if object_file in scale_mapping:
        return scale_mapping[object_file]

    # Check other cases
    if "chair" in object_file.lower():
        return 1.2
    if "shelf" in object_file.lower() or "bookcase" in object_file.lower():
        return 1.7
    if "table" in object_file.lower():
        return 1.8
    if object_file in os.listdir(OBJECT_ROOT):
        return 0.001

    return 1

def scale_model(root_element, scale_factor):
    mjMINVAL = 1e-8
    # Scale meshes in <asset>
    for mesh in root_element.findall('.//asset/mesh'):
        # Update scale attribute
        if 'scale' in mesh.attrib:
            scales = [float(s) * scale_factor for s in mesh.get('scale').split()]
        else:
            scales = [scale_factor, scale_factor, scale_factor]
        mesh.set('scale', ' '.join(map(str, scales)))

    # Scale geoms
    for geom in root_element.findall('.//geom'):
        # Scale size
        if 'size' in geom.attrib:
            sizes = [float(s) * scale_factor for s in geom.get('size').split()]
            geom.set('size', ' '.join(map(str, sizes)))
        # Scale position
        if 'pos' in geom.attrib:
            positions = [float(p) * scale_factor for p in geom.get('pos').split()]
            geom.set('pos', ' '.join(map(str, positions)))
        # Scale mass (mass scales with volume)
        if 'mass' in geom.attrib:
            mass = float(geom.get('mass')) * (scale_factor ** 3)
            if mass < mjMINVAL:  # mjMINVAL보다 작은 경우
                mass = mjMINVAL  # 최소값으로 설정
            geom.set('mass', str(mass))

    # Scale bodies
    for body in root_element.findall('.//body'):
        # Scale position
        if 'pos' in body.attrib:
            positions = [float(p) * scale_factor for p in body.get('pos').split()]
            body.set('pos', ' '.join(map(str, positions)))
        # Scale body mass
        if 'mass' in body.attrib:
            mass = float(body.get('mass')) * (scale_factor ** 3)
            mass = max(mass, mjMINVAL)
            body.set('mass', str(mass))
    # Scale joints (if any position attributes)
    for joint in root_element.findall('.//joint'):
        if 'pos' in joint.attrib:
            positions = [float(p) * scale_factor for p in joint.get('pos').split()]
            joint.set('pos', ' '.join(map(str, positions)))

    # Scale sites
    for site in root_element.findall('.//site'):
        # Scale size
        if 'size' in site.attrib:
            sizes = [float(s) * scale_factor for s in site.get('size').split()]
            site.set('size', ' '.join(map(str, sizes)))
        # Scale position
        if 'pos' in site.attrib:
            positions = [float(p) * scale_factor for p in site.get('pos').split()]
            site.set('pos', ' '.join(map(str, positions)))

    # Scale cameras
    for camera in root_element.findall('.//camera'):
        if 'pos' in camera.attrib:
            positions = [float(p) * scale_factor for p in camera.get('pos').split()]
            camera.set('pos', ' '.join(map(str, positions)))


def load_object_poses_from_json(json_path):
    with open(json_path, 'r') as f:
        object_poses = json.load(f)
    return object_poses


def add_robot_to_scene(base_root, robot_file, pose, assets_dir):
    add_object_to_scene(base_root, robot_file, pose, assets_dir)


def get_all_joints(model):
    """
    Retrieve all joint names from the model.
    Args:
        model: MjModel object.
    Returns:
        List of joint names.
    """
    joint_names = []
    for i in range(model.njnt):
        joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        if joint_name:
            joint_names.append(joint_name)
    return joint_names

def find_valid_robot_pose(furniture_poses):
    """
    Finds a valid robot position that avoids furniture positions but stays close to them
    
    Args:
        furniture_poses (dict): Dictionary of furniture positions
        
    Returns:
        dict: Robot pose with valid position and orientation
    """
    min_distance = 1  # Minimum distance from furniture
    max_distance = 1.5  # Maximum desired distance from furniture center
    room_bounds = (-3, 3)  # Room boundaries for x and y
    
    # Calculate center point of all furniture
    if not furniture_poses:
        return {"pos": [0, 0, 0], "quat": [1, 0, 0, 0]}
    
    furniture_positions = [f['pos'] for f in furniture_poses.values()]
    center_x = sum(p[0] for p in furniture_positions) / len(furniture_positions)
    center_y = sum(p[1] for p in furniture_positions) / len(furniture_positions)
    
    # Search in expanding circles from the center
    for radius in [r/10 for r in range(5, int(max_distance*10))]:  # 0.5 to max_distance in 0.1 increments
        # Test points around the circle
        for angle in range(0, 360, 20):  # Check every 10 degrees
            x = center_x + radius * math.cos(math.radians(angle))
            y = center_y + radius * math.sin(math.radians(angle))
            
            # Check if position is within room bounds
            if not (room_bounds[0] <= x <= room_bounds[1] and 
                   room_bounds[0] <= y <= room_bounds[1]):
                continue
                
            pos = [x, y, 0]
            is_valid = True
            
            # Check distance from each furniture
            for furniture in furniture_poses.values():
                furniture_pos = furniture['pos']
                distance = ((pos[0] - furniture_pos[0])**2 + 
                          (pos[1] - furniture_pos[1])**2)**0.5
                if distance < min_distance:
                    is_valid = False
                    break
            
            if is_valid:
                # Calculate orientation to face the center of furniture
                angle_to_center = math.atan2(center_y - y, center_x - x)
                # Convert angle to quaternion (rotating around z-axis)
                quat = [math.cos(angle_to_center/2), 0, 0, math.sin(angle_to_center/2)]
                return {"pos": pos, "quat": quat}
    
    # If no valid position found, return default pose
    return {"pos": [-1, 2, 0], "quat": [1, 0, 0, 0]}

def load_objects_in_scene():
    furniture_json_path = 'config/furniture_poses.json'
    object_json_path = 'config/small_object_poses.json'
    
    furniture_poses = load_object_poses_from_json(furniture_json_path)
    object_poses = load_object_poses_from_json(object_json_path)
    arena_root = ET.parse(ARENAS_PATH).getroot()

    # Load Furniture first
    for furniture_file, pose in furniture_poses.items():
        if 'object_placing_furniture' in pose:
            parent_furniture = pose['object_placing_furniture']
            add_object_to_scene(arena_root, furniture_file, pose, FUNITURE_ROOT, parent_furniture)
        else:
            add_object_to_scene(arena_root, furniture_file, pose, FUNITURE_ROOT)

    # Load Small Objects next
    for object_file, pose_data in object_poses['object_poses'].items():
        parent_furniture = pose_data['object_placing_furniture']
        add_object_to_scene(arena_root, object_file, pose_data, OBJECT_ROOT, parent_furniture)

    # Find valid robot pose and add robot to scene
    robot_pose = find_valid_robot_pose(furniture_poses)
    add_robot_to_scene(arena_root, "robot.xml", robot_pose, ROBOT_PATH)

    main_xml_str = ET.tostring(arena_root, encoding='unicode')
    model = mujoco.MjModel.from_xml_string(main_xml_str)

    # Set gravity
    model.opt.gravity = (0, 0, -9.8)

    data = mujoco.MjData(model)
    viewer = mujoco_viewer.MujocoViewer(model, data)

    # Get joint names
    joints_names = get_all_joints(model)
    control_joint = []
    for joint_name in joints_names:
        if 'freejoint' not in joint_name:
            joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
            control_joint.append(joint_name)

    robot_name = "panda"
    actuator_id_list = []
    robot_actuator_id_list = []

    for joint_name in control_joint:
        if "robot" not in joint_name:
            actuator_name = f"{joint_name}_j"
            actuator_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_name)
            actuator_id_list.append(actuator_id)
        elif "robot" in joint_name:
            joint_number = joint_name.split("_")[-1]
            actuator_name = f"robot_{robot_name}_torq_j{joint_number}"
            actuator_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_name)
            robot_actuator_id_list.append(actuator_id)
        else:
            print(f"joint_name: {joint_name}")

    actuator_ctrl_ranges = []
    for actuator_id in actuator_id_list:
        ctrl_min, ctrl_max = model.actuator_ctrlrange[actuator_id]
        actuator_ctrl_ranges.append((actuator_id, ctrl_min, ctrl_max))

    initial_target = []
    for actuator_id, ctrl_min, ctrl_max in actuator_ctrl_ranges:
        if ctrl_min != 0 or ctrl_max != 0:
            initial_target.append((actuator_id, ctrl_min if ctrl_min != 0 else ctrl_max))

    # Define parameters for each joint including timing
    joint_params = {
        0: {
            "amplitude": 0.5, "frequency": 0.5, "offset": -1.57,
            "start_time": 200, "end_time": 300
        },  # Joint 1 - starts first, ends last
        1: {
            "amplitude": 0.5, "frequency": 0.5, "offset": 1.57,
            "start_time": 200, "end_time": 300
        },  # Joint 2 - starts later, ends even later
        2: {
            "amplitude": 0.2, "frequency": 1.0, "offset": -0.48,
            "start_time": 500, "end_time": 600
        },  # Joint 3 - starts and ends last
        3: {
            "amplitude": 0.4, "frequency": 0.3, "offset": 0.6,
            "start_time": 600, "end_time": 700
        },   # Joint 4 - starts second, ends second
        4: {
            "amplitude": 0.4, "frequency": 0.3, "offset": -1.57,
            "start_time": 300, "end_time": 400
        }   # Joint 5 - starts second, ends second
    }

    while viewer.is_alive:
        joint_positions = data.sensordata
        current_time = data.time / model.opt.timestep

        # Calculate motion for each joint based on its timing
        for actuator_id, _, _ in actuator_ctrl_ranges:
            if actuator_id in joint_params:
                params = joint_params[actuator_id]
                
                # Check if we're within this joint's active time window
                if current_time >= params["start_time"] and current_time < params["end_time"]:
                    # Calculate progress through the motion (0 to 1)
                    progress = (current_time - params["start_time"]) / (params["end_time"] - params["start_time"])
                    position = params["offset"]

                    # Add smooth start and end transitions
                    data.ctrl[actuator_id] = position

                elif current_time >= params["end_time"]:
                    # Gradually return to initial position
                    data.ctrl[actuator_id] = 0

        mujoco.mj_step(model, data)
        viewer.render()

    viewer.close()    

if __name__ == "__main__":
    load_objects_in_scene()