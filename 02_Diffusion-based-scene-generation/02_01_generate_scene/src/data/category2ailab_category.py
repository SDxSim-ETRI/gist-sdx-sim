import json


json_path = '/home/ailab/Workspace/ailab-InstructScene/dataset_/3D-FRONT/3D-FUTURE-model/ailab_model_info.json'
with open(json_path, 'r') as f:
    data = json.load(f)

super_category_set = set()
category_list = []
category_dict = {}
for item in data:
    if item['category'] is None:
        continue
    category_dict[item['category'].lower()] = item['ailab_category'].lower()


print(category_dict)
save_json_path = json_path.replace('ailab_model_info.json', 'ailab_model_info_category_set.json')
with open(save_json_path, 'w') as f:
    json.dump(category_dict, f, indent=4)