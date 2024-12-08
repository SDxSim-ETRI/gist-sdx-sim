from utils.object_selection_prompt import generate_object_selection, save_poses_to_json, select_parent_furniture, generate_furniture_poses, generate_object_poses
from utils.layout_objects import load_objects_in_scene


if __name__ == "__main__":
    
     # Paths
     funiture_list = 'config/furniture_list.json'
     object_list = 'config/small_object_list.json'
     furniture_poses_save_path = 'config/furniture_poses.json'
     object_poses_save_path = 'config/small_object_poses.json'
     
     # User instruction
     user_instruction = "Place 2 tables and 2 chairs, along with a cabinet and vanity. Then place 3 objects on the tables."     
     
     # LLM modules
     selected_furniture, selected_objects = generate_object_selection(user_instruction, funiture_list, object_list)
     parent_furniture = select_parent_furniture(selected_furniture, user_instruction)
     furniture_poses = generate_furniture_poses(selected_furniture, parent_furniture, funiture_list)
     object_poses = generate_object_poses(selected_furniture, parent_furniture, selected_objects, furniture_poses, funiture_list)

     # Save to JSON for mujoco simulation    
     save_poses_to_json(furniture_poses_save_path, object_poses_save_path, furniture_poses, object_poses)    

     # Load objects in scene
     load_objects_in_scene()