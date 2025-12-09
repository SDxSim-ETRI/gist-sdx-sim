import json
import os

object_class = ['Sofa', 'Lighting', 'Bed', 'Table', 'Cabinet', 'Stool', 'Chair', 'Others']

data_dir = '/home/ailab/Workspace/scene-gen-mujoco/data_1128_new_all'
scene_list = os.listdir(data_dir)

ailab_model_info_path = 'ailab_model_info.json'
with open(ailab_model_info_path, 'r', encoding='utf-8') as f:
    ailab_model_info = json.load(f)

for scene in scene_list:
    if '.json' in scene:
        continue
    json_path = os.path.join(data_dir, scene, 'objects.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        objects_json = json.load(f)

    for i, obj_dict in enumerate(objects_json['objects']):
        for model_info in ailab_model_info:
            if obj_dict['model_id'] == model_info['model_id']:
                objects_json['objects'][i]['model_info'] = model_info
                objects_json['objects'][i]['mj_class'] = model_info['ailab_category']
                objects_json['objects'][i]['mj_class_id'] = object_class.index(model_info['ailab_category'])
                break
    save_json_path = json_path.replace('objects.json', 'objects_mj.json')
    with open(save_json_path, 'w', encoding='utf-8') as f:
        json.dump(objects_json, f, ensure_ascii=False, indent=4)