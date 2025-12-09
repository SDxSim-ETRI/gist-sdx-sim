import json

json_path = '/home/ailab/Workspace/ailab-InstructScene/dataset_/3D-FRONT/3D-FUTURE-model/ailab_model_info.json'
with open(json_path, 'r') as f:
    data = json.load(f)


super_category_set = set()
category_set = set()
data_dict = {
    'Cabinet/Shelf/Desk': [],
    'Pier/Stool': [],
}
for item in data:
    if '/' in item['super-category']:
    # if '/' in item['ailab_category']:
        data_dict[item['super-category']].append(item['category'])
    super_category_set.add(item['super-category'])
    category_set.add(item['category'])


ailab_category_set = set()
for item in data:
    ailab_category_set.add(item['ailab_category'])

print("Super Categories:")
for super_category in super_category_set:
    print(f" - {super_category}")

print("Categories:")
for category in category_set:
    print(f" - {category}")