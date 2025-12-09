# gist-sdx-sim

자연어 명령을 통해 MuJoCo 물리 시뮬레이션 환경에서 가구와 물체들을 자동으로 배치하는 프레임워크

## Installation

conda env create -f environment.yml

## GPT api key
You need to get your own API key from OpenAI.
```bash
And set it in utils/object_selection_prompt.py "openai.api_key"
```

## Usage
```bash
Example usage in main.py:
user_instruction = "Place 2 tables and 3 chairs, with microwave and bookcase."
```
## Generate layout
```bash
selected_furniture, selected_objects = generate_object_selection(user_instruction, 
                                                              'config/furniture_list.json', 
                                                              'config/object_list.json')
parent_furniture = select_parent_furniture(selected_furniture, user_instruction)
furniture_poses = generate_furniture_poses(selected_furniture, parent_furniture, funiture_list)
object_poses = generate_object_poses(selected_furniture, parent_furniture, selected_objects, 
                                   furniture_poses, funiture_list)
```
## Save and load scene
```bash
save_poses_to_json(furniture_poses_save_path, object_poses_save_path, 
                  furniture_poses, object_poses)    
load_objects_in_scene()
```
