import json
from ailab_class_cfg import problem_super_category

json_path = '/home/ailab/Workspace/ailab-InstructScene/dataset/3D-FRONT/3D-FUTURE-model/model_info.json'
with open(json_path, 'r') as f:
    data = json.load(f)

ailab_model_info_json_path = json_path.replace('model_info.json', 'ailab_model_info.json')
ailab_model_info_json = []
for item in data:
    ailab_model_info = item.copy()
    if '/' not in item['super-category']:
        ailab_category = item['super-category']
    elif 'Cabinet/Shelf/Desk' == item['super-category']: 
        ailab_category = problem_super_category['Cabinet/Shelf/Desk'][item['category']]
    elif 'Pier/Stool' == item['super-category']:
        ailab_category = problem_super_category['Pier/Stool'][item['category']]
    else:
        raise ValueError(f"Unknown super-category: {item['super-category']}")

    ailab_model_info['ailab_category'] = ailab_category
    ailab_model_info_json.append(ailab_model_info)

with open(ailab_model_info_json_path, 'w') as f:
    json.dump(ailab_model_info_json, f, indent=4)