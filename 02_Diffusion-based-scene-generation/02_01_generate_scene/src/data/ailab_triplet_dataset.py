import os
import glob
import re
import json

relation = ['left of', 'behind', 'right of', 'in front of', 'above', 'below']
closely_relation = ['closely left of', 'closely behind', 'closely right of', 'closely in front of']
all_relations = sorted(closely_relation + relation, key=len, reverse=True)

category_json = '/home/ailab/Workspace/ailab-InstructScene/dataset_/3D-FRONT/3D-FUTURE-model/ailab_model_info_category_set.json'
with open(category_json, 'r') as f:
    category_dict = json.load(f)
category_key_list = list(category_dict.keys())

#! class idx: list index
object_class = ['Sofa', 'Lighting', 'Bed', 'Table', 'Cabinet', 'Stool', 'Chair', 'Others']
object_class = [obj.lower() for obj in object_class]
#! class idx: list index
relation_class = ['above', 'left of', 'in front of', 'closely left of', 'closely in front of', 'below', 'right of', 'behind', 'closely right of', 'closely behind']
                  

def get_class_index(subject_part, object_class=object_class, category_key_list=category_key_list):
    # category_key_list 기준으로 ailab_category 찾아서 class idx 결정
    for idx, cls in enumerate(category_key_list):
        # object_class에 '/'가 있는 경우 분리해서 검사
        for sub_cls in cls.split('/'):
            sub_cls = sub_cls.strip()
            if sub_cls in subject_part:
                ailab_category = category_dict[cls]
                for obj_idx, obj_cls in enumerate(object_class):
                    if ailab_category in obj_cls:
                        return obj_idx

    
    # ailab_category 기준으로 먼저 class idx 결정
    for idx, cls in enumerate(object_class):
        # object_class에 '/'가 있는 경우 분리해서 검사
        for sub_cls in cls.split('/'):
            sub_cls = sub_cls.strip()
            if sub_cls in subject_part:
                return idx
    
    if 'chandelier' in subject_part:
        return object_class.index('lighting')

    assert False, f"Cannot find class for subject/object part: {subject_part}"          
    # 못찾으면 others로
    return object_class.index('others')

def make_triplet(description, all_relations=all_relations, object_class=object_class):
    """
    Splits a sentence into a (subject, relation, object) triplet.
    """
    # clean description(erase leading/trailing spaces, under bar, dash, etc and convert to lower case)
    description = re.sub(r'[_-]', ' ', description).strip().lower()

    pattern = '(' + '|'.join(map(re.escape, all_relations)) + ')'

    split_result = re.split(pattern, description)

    cleaned_result = [part.strip() for part in split_result if part.strip()]

    if len(cleaned_result) == 3:
        subject_part, relation_part, object_part = cleaned_result
    else:
        print(cleaned_result)
        assert False, "Failed to parse triplet. Need a exception handling here."

    # each part to class
    subject_class_id = get_class_index(subject_part)
    object_class_id = get_class_index(object_part)
    relation_class_id = relation_class.index(relation_part)

    triplet_class_id = [subject_class_id, relation_class_id, object_class_id]
    triplet_str = [subject_part, relation_part, object_part]
    triplet_class = [object_class[subject_class_id], relation_part, object_class[object_class_id]]
    
    return triplet_class_id, triplet_str, triplet_class

data_dir = '/home/ailab/Workspace/scene-gen-mujoco'
scene_type = 'data_1128_new_03'

scene_list = os.listdir(os.path.join(data_dir, scene_type))

for scene in scene_list:
    json_dict = {
        "original_path": None,
        "scene": None,
        "description": None,
        "triplet": None
    }

    if '.txt' in scene:
        continue

    scene_dir = os.path.join(data_dir, scene_type, scene)
    description_path = os.path.join(scene_dir, 'description.txt')
    with open(description_path, 'r') as f:
        description = f.read()
        print(f"----- Scene: {scene} -----")
        print(description)
    
    sentences = description.split('. ')
    if len(sentences) > 1:
        # gray print
        print(f'\033[90mMore than 1 sentence description: #{len(sentences)}\033[0m')

    triplet_dict = {}
    for i, sentence in enumerate(sentences):
        triplet_class_id, triplet_str, triplet_class = make_triplet(sentence)
        triplet_dict[i] = {
            "triplet_class_id": triplet_class_id,
            "triplet_str": triplet_str,
            "triplet_class": triplet_class
        }
        print(triplet_class)
    print()

    json_dict["original_path"] = os.path.join(scene_type, scene)
    json_dict["scene"] = scene
    json_dict["description"] = description
    json_dict["triplet"] = triplet_dict

    json_save_path = os.path.join(scene_dir, 'ailab_eval.json')
    with open(json_save_path, 'w') as f:
        json.dump(json_dict, f, indent=4)
