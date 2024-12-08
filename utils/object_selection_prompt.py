import json
import openai
import re
import os
import shutil
import random
from collections import OrderedDict

openai.api_key = # Insert your API key here

def duplicate_xml(original_file, num_copies, tmp_storage_path):
    """
    Duplicate an XML file multiple times with unique names.
    
    Parameters:
    - original_file (str): The original XML file to duplicate.
    - num_copies (int): Number of copies to create.
    - tmp_storage_path (str): Path to store duplicated files.
    
    Returns:
    - duplicated_files (list): List of duplicated file names.
    """
    duplicated_files = []
    base, ext = os.path.splitext(os.path.basename(original_file))
    for i in range(1, num_copies + 1):
        new_file = f"{base}_copy_{i}{ext}"
        new_file_path = os.path.join(tmp_storage_path, new_file)
        shutil.copyfile(original_file, new_file_path)
        duplicated_files.append(new_file)
    return duplicated_files


def generate_object_selection(user_instruction, furniture_json_path='furniture_list.json', object_json_path='small_object.json', tmp_storage_path='models/assets/objects'):
     with open(furniture_json_path, 'r') as f:
          furniture_names = json.load(f)
     with open(object_json_path, 'r') as f:
          object_names = json.load(f)     

     # Pre-filter furniture by type
     furniture_by_type = {}
     for name in furniture_names:
          furniture_type = next((t for t in ['table', 'chair', 'shelf', 'cabinet', 'microwave', 'bookcase'] if t in name.lower()), 'other')
          if furniture_type not in furniture_by_type:
               furniture_by_type[furniture_type] = []
          furniture_by_type[furniture_type].append(name)

     # Randomly pre-select more furniture options to present to GPT
     filtered_furniture = {}
     for ftype, items in furniture_by_type.items():
          if items:
               # Increase the number of items selected for each type
               num_to_select = min(len(items), 20)  # Increased from 3 to 5
               # Add randomization weight to favor less frequently selected items
               weighted_items = [(item, random.random()) for item in items]
               weighted_items.sort(key=lambda x: x[1])
               filtered_furniture[ftype] = [item[0] for item in weighted_items[:num_to_select]]

     # Add temperature parameter to increase variety
     temperature = 0.8  # Increased from 0 to add more randomness

     # Randomly pre-select objects to present to GPT
     num_objects_to_present = min(len(object_names), 15)  # Present only 15 random objects
     filtered_objects = random.sample(list(object_names), num_objects_to_present)

     # Create the prompt with filtered lists
     prompt = f"""
          User Instruction:
          \"\"\"
          {user_instruction}
          \"\"\"

          **⚠️ CRITICAL NAME MATCHING RULE - ABSOLUTELY MUST FOLLOW:**
          - You MUST select names EXACTLY as they appear in the lists below
          - DO NOT add any prefixes (like 'table_') to the names
          - DO NOT modify the names in any way
          - Any modified names will cause system errors
          - The selection must match the available options CHARACTER BY CHARACTER

          **Available Furniture Options:**
          {json.dumps(filtered_furniture, indent=4)}

          **Available Object Options:**
          {json.dumps(filtered_objects, indent=4)}

          Based on the user instruction above, select furniture and objects EXACTLY as they appear in the lists above.
          ⚠️ WARNING: DO NOT modify names - copy and paste them exactly as shown.

          **CRITICAL RULES - MUST FOLLOW:**
          1. **Supporting Table Rule (MANDATORY)**:
               - For EVERY cabinet and microwave selected, you MUST include a corresponding supporting table
               - Rules for Cabinets:
                    - If you select "cabinet_1.xml", you MUST also select "cabinet_table_1.xml"
                    - If you select multiple cabinets, you need a supporting table for each one
               - Rules for Microwaves:
                    - If you select "microwave.xml", you MUST also select "microwave_table.xml"
                    - If you select multiple microwaves, you need a supporting table for each one
               - ⚠️ NEVER select a cabinet or microwave without its supporting table
               - ⚠️ Cabinet and microwave must have SEPARATE supporting tables
               - ⚠️ Cabinet and microwave cannot be place on the 

          2. **Maximum Count Rule**:
               - Each type of furniture is limited to a maximum of 3 items
               - Supporting tables for cabinets and microwaves do NOT count toward this limit

          3. **Variety and Logical Placement Rules**:
               - Try to select different items each time
               - Ensure selections make sense with the user's instruction

          **Examples of CORRECT Selections:**

          Example 1 - Single Cabinet:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",
                    "cabinet_1.xml",
                    "cabinet_table_1.xml"  // Required for cabinet
               ]
          }}

          Example 2 - Single Microwave:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",
                    "microwave.xml",
                    "microwave_table.xml"  // Required for microwave
               ]
          }}

          Example 3 - Both Cabinet and Microwave:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",
                    "cabinet_1.xml",
                    "cabinet_table_1.xml",    // Required for cabinet
                    "microwave.xml",
                    "microwave_table.xml"     // Required for microwave
               ]
          }}

          Example 4 - Multiple Cabinets:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",
                    "cabinet_1.xml",
                    "cabinet_table_1.xml",    // Required for cabinet_1
                    "cabinet_2.xml",
                    "cabinet_table_2.xml"     // Required for cabinet_2
               ]
          }}

          Example 5 - Multiple Cabinets and Microwave:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",        // Main table
                    "cabinet_1.xml",              // First cabinet
                    "cabinet_table_1.xml",        // Required supporting table for cabinet_1
                    "cabinet_2.xml",              // Second cabinet
                    "cabinet_table_2.xml",        // Required supporting table for cabinet_2
                    "microwave.xml",              // Microwave
                    "microwave_table.xml"         // Required supporting table for microwave
               ]
          }}

          Example 6 - Study Setup:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",        // Main desk
                    "chair_ingolf_0650.xml",      // Study chair
                    "shelf_ivar_0615.xml",        // Bookshelf
                    "cabinet_1.xml",              // Storage cabinet
                    "cabinet_table_1.xml",        // Required supporting table for cabinet
                    "microwave.xml",              // For coffee/snacks
                    "microwave_table.xml"         // Required supporting table for microwave
               ],
               "selected_objects": [
                    "book.xml",
                    "laptop.xml",
                    "lamp.xml",
                    "cup.xml"
               ]
          }}

          Example 7 - Kitchen Setup:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",        // Dining table
                    "chair_ingolf_0650.xml",      // Dining chair
                    "chair_ingolf_0650.xml",      // Second dining chair
                    "microwave.xml",              // Kitchen appliance
                    "microwave_table.xml",        // Required supporting table for microwave
                    "cabinet_1.xml",              // Kitchen storage
                    "cabinet_table_1.xml",        // Required supporting table for cabinet
                    "cabinet_2.xml",              // Additional storage
                    "cabinet_table_2.xml"         // Required supporting table for cabinet_2
               ],
               "selected_objects": [
                    "plate.xml",
                    "cup.xml",
                    "kettle.xml",
                    "bowl.xml"
               ]
          }}

          Example 8 - Living Room Scene:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",        // Coffee table
                    "chair_ingolf_0650.xml",      // Armchair
                    "shelf_ivar_0615.xml",        // Display shelf
                    "cabinet_1.xml",              // Media cabinet
                    "cabinet_table_1.xml",        // Required supporting table for cabinet
                    "microwave.xml",              // For snacks
                    "microwave_table.xml"         // Required supporting table for microwave
               ],
               "selected_objects": [
                    "book.xml",
                    "remote.xml",
                    "vase.xml",
                    "lamp.xml"
               ]
          }}

          Example 8 - Example with Bins
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",        // Coffee table
                    "chair_ingolf_0650.xml",      // Armchair
                    "shelf_ivar_0615.xml",        // Display shelf
                    "bin_1.xml",                  // Bin
                    "bin_2.xml"                  // Bin
               ],
               "selected_objects": [
                    "lemon.xml",
                    "bottle.xml",
                    "cereal.xml"
               ]
          }}


          **Examples of INCORRECT Selections:**

          Example 1 - Missing Supporting Table:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",
                    "cabinet_1.xml"        // ERROR: Missing cabinet table!
               ]
          }}

          Example 2 - Missing Multiple Supporting Tables:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",
                    "cabinet_1.xml",       // ERROR: Missing cabinet table!
                    "microwave.xml"        // ERROR: Missing microwave table!
               ]
          }}

          Example 3 - Incomplete Supporting Tables:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",
                    "cabinet_1.xml",
                    "cabinet_2.xml",
                    "cabinet_table_1.xml"  // ERROR: cabinet_2 needs its own table!
               ]
          }}

          Example 4 - Sharing Supporting Tables:
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",
                    "cabinet_1.xml",
                    "microwave.xml",
                    "cabinet_table_1.xml"  // ERROR: Microwave needs its own table!
               ]
          }}

          **Output Format:**
          {{
               "selected_furniture": [
                    "table_lack_0825.xml",
                    "cabinet_1.xml",
                    "cabinet_table_1.xml",
                    "microwave.xml",
                    "microwave_table.xml"
               ],
               "selected_objects": [
                    "can.xml",
                    "book.xml",
                    "lamp.xml"
               ]
          }}
     """

     # Call the OpenAI API with increased temperature
     response = openai.ChatCompletion.create(
          model="gpt-4",
          messages=[
               {"role": "system", "content": "You are an assistant that selects varied and contextually appropriate items from lists based on the user's instruction."},
               {"role": "user", "content": prompt}
          ],
          temperature=temperature  # Using higher temperature for more variety
     )
    
     # Extract the assistant's response
     assistant_response = response['choices'][0]['message']['content']
     
     # Extract JSON part using regex
     json_like_response = re.search(r"{.*}", assistant_response, re.DOTALL)
     if json_like_response:
          json_string = json_like_response.group(0)
          try:
               # Parse the JSON string
               result = json.loads(json_string)
               print(result)
               selected_furniture = result.get("selected_furniture", [])
               selected_objects = result.get("selected_objects", [])
               return selected_furniture, selected_objects
          except json.JSONDecodeError as e:
               print("Error parsing JSON. Raw JSON string:")
               print(json_string)
               raise e
     else:
          raise ValueError("Expected JSON output was not found in the assistant response.")

     return selected_furniture, selected_objects

def select_parent_furniture(selected_furniture, user_instruction):
     # Prompt creation
     prompt = f"""
     Based on the selected furniture list:
     {selected_furniture}

     And the user instruction:
     \"\"\"
     {user_instruction}
     \"\"\"

     Select the most appropriate furniture to be placed at the center of the room (Parent Furniture) based on its function or user needs. 
     Parent furniture is just a single furniture piece
     Provide the result in JSON format:
     {{
          "parent_furniture": "furniture1.xml"
     }}
     """
     
     # OpenAI API call
     response = openai.ChatCompletion.create(
          model="gpt-4",
          messages=[
               {"role": "system", "content": "You are an assistant that helps identify the most suitable central furniture based on user instructions."},
               {"role": "user", "content": prompt}
          ],
          temperature=0
     )
     
     # Parse response
     assistant_response = response['choices'][0]['message']['content']
     json_like_response = re.search(r"{.*}", assistant_response, re.DOTALL)

     if json_like_response:
          return json.loads(json_like_response.group(0))['parent_furniture']
     else:
          raise ValueError("No valid JSON response found.")
     

def generate_furniture_poses(selected_furniture, parent_furniture, furniture_json_path='furniture_list.json'):
     # Load furniture size data
     with open(furniture_json_path, 'r') as f:
          furniture_list = json.load(f)
     
     # Extract size data for selected furniture
     furniture_size_data = {furniture: furniture_list[furniture]["size"] for furniture in selected_furniture}
     
     # Handle multiple parent furniture candidates
     if isinstance(parent_furniture, list):
          # Use the first item as the parent furniture (customize as needed)
          selected_parent_furniture = parent_furniture[0]
     else:
          selected_parent_furniture = parent_furniture
     
     # Extract parent furniture height
     if parent_furniture not in furniture_size_data:
          raise ValueError(f"Parent furniture '{parent_furniture}' not found in the furniture list.")
     parent_furniture_height = furniture_size_data[parent_furniture][2]
     
     # Prompt creation
     prompt = f"""
     You are an assistant that determines furniture positions and orientations.

     Based on the selected furniture list:
     {selected_furniture}

     The parent furniture is:
     {parent_furniture}

     And their corresponding size data:
     {json.dumps(furniture_size_data, indent=4)}

     ### **Furniture Placement Rules:**

     1. **Parent Furniture Position**:
          - Place at [0, 0, 0]
          - Orientation: [1, 0, 0, 0] (facing negative y-axis)

     2. **Other Furniture Rules**:
          - Minimum spacing: 0.8 meter from parent furniture
          - Room boundaries: -2.5 ≤ x,y ≤ 2.5
          Probability-based placement:
               Near parent furniture (40%): within 1.5 meters.
               Random elsewhere (60%): between 1.5 and 2.5 meters.
          - Z-coordinate: 0 (except microwaves)
          - Orientation options when facing parent:
               - Behind (+y): [1, 0, 0, 0]
               - Front (-y): [0, 0, 0, 1]    
               - Right (+x): [0.707, 0, 0, -0.707]
               - Left (-x): [0.707, 0, 0, 0.707]
          - Default orientation (not facing): [1, 0, 0, 0]

     3. **Object Supporting Table Rules**:
          - Required for microwaves and cabinets.
          - Cannot share tables between microwave and cabinet.
          - Position: Absolute coordinates in room.
          - Z-coordinate: Always 0.
          - Orientation: Same rules as other furniture.

     4. **Special Cases - Microwaves & Cabinets**:
          - Require dedicated supporting tables
          - Tables are **required only for microwaves and cabinets**.
          - **Other furniture items (e.g., bookcase, shelf, chair) must not be placed on any table.**
          - Microwave and cabinet cannot share the same table.
          - Position must be specified relative to their supporting table:
               - Must include "object_placing_furniture" field pointing to their supporting table
               - x, y coordinates must be within the object_placing_furniture table's size range
               - z coordinate must be exactly the object_placing_furniture table's height
               Example: If supporting table size is (0.4, 0.2, 0.5):
                    - x: must be within ±0.2 of table center
                    - y: must be within ±0.1 of table center
                    - z: must be exactly 0.5 (table height)
          - Orientation: Always same as the object_placing_furniture

     5. **Randomization Parameters**:
          - Add variability to the placement:
          - Position and orientation randomness applied to non-critical objects like chairs and bins.

     ### **Example Scenarios and Their Expected Outputs:**

     # Example 1: Chairs facing parent furniture (table) - front and side placement
     {{\n
          "furniture_poses": {{\n
               "table_dining.xml": {{"pos": [0, 0, 0], "quat": [1, 0, 0, 0]}},
               "chair_1.xml": {{"pos": [0.5, -1.2, 0], "quat": [0, 0, 0, 1]}},
               "chair_2.xml": {{"pos": [-1.4, 1.1, 0], "quat": [0.707, 0, 0, 0.707]}}
          }}
     }}

     # Example 2: Chair and bookshelf facing parent furniture (desk) - front and back placement
         {{
         "furniture_poses": {{
              "table_lack_0825.xml": {{"pos": [0, 0, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": true}},  # Parent furniture
              "chair_ingolf_0650.xml": {{"pos": [1.5, -0.8, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": true}},  # Facing from behind
              "shelf_ivar_0615.xml": {{"pos": [0, 1.5, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": true}}  # Facing from back
              "bookcase_besta_0170.xml": {{"pos": [0, 1.5, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": true}}  # Facing from back
         }}
         }}

         # Example 3: Typical living room arrangement (table-centered)
         {{
         "furniture_poses": {{
              "table_lack_0825.xml": {{"pos": [0, 0, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": true}},  # Parent furniture
              "chair_ingolf_0650.xml": {{"pos": [1.4, -1.2, 0], "quat": [0.707, 0, 0, 0.707], "face_to_parent_furniture": false}},  # Left diagonal
              "shelf_ivar_0615.xml": {{"pos": [-2.0, 2.0, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": false}}  # Back corner
          }}
          }}

         # Example 4: Cabinet and table combination
         {{
         "furniture_poses": {{
              "table_lack_0825.xml": {{"pos": [0, 0, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": true}},  # Main table
              "cabinet_table_1.xml": {{"pos": [1.0, 1.2, 0], "quat": [0.707, 0, 0, -0.707], "face_to_parent_furniture": true}},  # Supporting table, size: (0.4, 0.2, 0.5)
              "cabinet_1.xml": {{
                   "pos": [0, 0, 0.5],  # x within ±0.2, y within ±0.1, z = table height
                   "quat": same as cabinet_table_1.xml,
                   "face_to_parent_furniture": true,
                   "object_placing_furniture": "cabinet_table_1.xml"
              }}
          }}
          }}

         # Example 5: Complex arrangement with cabinet and microwave
         {{
         "furniture_poses": {{
              "table_lack_0825.xml": {{"pos": [0, 0, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": true}},  # Main table
              "cabinet_table_1.xml": {{"pos": [2.0, 0, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": true}},  # Cabinet table, size: (0.4, 0.2, 0.5)
              "cabinet_1.xml": {{
                   "pos": [0, 0, 0.5],  # x within ±0.2, y within ±0.1, z = table height
                   "quat": same as cabinet_table_1.xml,
                   "face_to_parent_furniture": true,
                   "object_placing_furniture": "cabinet_table_1.xml"
              }},
              "microwave_table.xml": {{"pos": [-2.0, -1.5, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": true}},  # Microwave table, size: (0.3, 0.15, 0.4)
              "microwave.xml": {{
                   "pos": [0, 0, 0.4],  # x within ±0.15, y within ±0.075, z = table height
                   "quat": same as microwave_table.xml,
                   "face_to_parent_furniture": true,
                   "object_placing_furniture": "microwave_table.xml"
              }}
         }}
         }}

     ### **Output Format**:
         {{\n
              "furniture_poses": {{\n
                   "parent_furniture.xml": {{"pos": [0, 0, 0], "quat": [1, 0, 0, 0], "face_to_parent_furniture": true}},
                   "furniture1.xml": {{"pos": [x, y, 0], "quat": [w, x, y, z], "face_to_parent_furniture": true}},
                   "cabinet_table_1.xml": {{"pos": [x, y, 0], "quat": [w, x, y, z], "face_to_parent_furniture": true}},
                   "cabinet_1.xml": {{
                        "pos": [0, 0, table_height],
                        "quat": same as cabinet_table_1.xml,
                        "face_to_parent_furniture": true,
                        "object_placing_furniture": "cabinet_table_1.xml"
                   }},
                   "microwave_table.xml": {{"pos": [x, y, 0], "quat": [w, x, y, z], "face_to_parent_furniture": true}},
                   "microwave.xml": {{
                        "pos": [0, 0, table_height],
                        "quat": same as microwave_table.xml,
                        "face_to_parent_furniture": true,
                        "object_placing_furniture": "microwave_table.xml"
                   }}
              }}
         }}
     """

     # OpenAI API call
     response = openai.ChatCompletion.create(
          model="gpt-4",
          messages=[
               {"role": "system", "content": "You are an assistant that determines furniture positions and orientations."},
               {"role": "user", "content": prompt}
          ],
          temperature=0.3
     )
     
     # Parse response
     assistant_response = response['choices'][0]['message']['content']
    
     # Parse response and get initial furniture poses
     furniture_poses = parse_gpt_response(assistant_response)  # Assume this extracts the JSON response
    
     # Post-process the poses to set correct heights for supported objects
     for furniture_name, pose in furniture_poses.items():
        if "object_placing_furniture" in pose:
          supporting_furniture = pose["object_placing_furniture"]
          # Get the supporting furniture's height from furniture_list
          if supporting_furniture in furniture_list:
               supporting_height = furniture_list[supporting_furniture]["size"][2]
               # Update the z-coordinate of the supported furniture
               pose["pos"][2] = supporting_height
     return furniture_poses

# Helper function to parse GPT response
def parse_gpt_response(assistant_response):
    json_like_response = re.search(r"```json\s*([\s\S]*?)\s*```", assistant_response)
    if not json_like_response:
        raise ValueError("No valid JSON response found.")
    
    try:
        json_str = json_like_response.group(1)
        json_data = json.loads(json_str)
        return json_data.get("furniture_poses", {})
    except json.JSONDecodeError as e:
        print("Error decoding JSON from the assistant's response.")
        raise e

def generate_object_poses(selected_furniture, parent_furniture, selected_objects, furniture_poses, furniture_json_path='furniture_list.json'):
     # Load furniture size data
     with open(furniture_json_path, 'r') as f:
          furniture_list = json.load(f)
     
     # Extract size data for selected furniture
     furniture_size_data = {furniture: furniture_list[furniture]["size"] for furniture in selected_furniture}
     
     # Handle multiple parent furniture candidates
     if isinstance(parent_furniture, list):
          # Use the first item as the parent furniture (customize as needed)
          selected_parent_furniture = parent_furniture[0]
     else:
          selected_parent_furniture = parent_furniture
     
     # Extract parent furniture height
     if parent_furniture not in furniture_size_data:
          raise ValueError(f"Parent furniture '{parent_furniture}' not found in the furniture list.")
     parent_furniture_height = furniture_size_data[parent_furniture][2]
     
     # Find tables that are supporting cabinets or microwaves
     occupied_tables = set()
     for furniture, pose in furniture_poses.items():
          if "object_placing_furniture" in pose:
               occupied_tables.add(pose["object_placing_furniture"])
     
     # Find available tables for object placement
     available_tables = []
     for furniture in furniture_poses:
          if ("table" in furniture.lower() and 
              furniture not in occupied_tables):
               available_tables.append(furniture)
     
     # Add available tables to the prompt
     prompt = f"""
     Based on the selected objects:
     {selected_objects}

     And the furniture positions:
     {furniture_poses}

     And their corresponding size data:
     {json.dumps(furniture_size_data, indent=4)}

     Available tables for object placement:
     {available_tables}

          1. **Object Placement Rules**:
               - All objects must be placed on a table
               - Objects can ONLY be placed on these available tables: {available_tables}
               - DO NOT place objects on tables that have cabinets or microwaves on them
               - DO NOT place objects on cabinet_table or microwave_table

          2. **Position Coordinates**:
               - Height (Z-axis):
                    - Z = table_surface_height + 0.1 meters
               
               - Horizontal Position (X,Y axes):
                    - Objects must be placed within table surface boundaries
                    - Positions are relative to table center coordinates
                    Example for table at (1,0,0) with size (0.4, 0.2, 0.5):
                         - X range: table_center ± 0.2
                         - Y range: table_center ± 0.1

         3. **Collision Prevention**:
               - CRITICAL: Objects MUST maintain minimum separation in BOTH x and y axes:
                    - Minimum X-axis separation: 0.1 meters
                    - Minimum Y-axis separation: 0.1 meters
               - Example: If object1 is at (0,0,z), the next object cannot be placed within:
                    - X range: -0.1 to +0.1 of object1's x position
                    - Y range: -0.1 to +0.1 of object1's y position
               - This creates a 0.1m x 0.1m "exclusion zone" around each object
               - Consider object dimensions when calculating positions
               - Objects should be placed at least 0.05 meters from table edges

          4. **Distribution Guidelines**:
               - Distribute objects WIDELY across available table surfaces
               - Use the ENTIRE table surface area
               - Place objects near table corners and edges when possible
               - When multiple tables are available:
                    - Distribute objects evenly among ALL tables
               - Avoid placing objects in straight lines or grid patterns
               - Use diagonal or scattered arrangements for natural placement

     # Examples:
     
     Example 1 - Simple Table with Multiple Objects:
     {{
          "object_poses": {{
               "book.xml": {{
                    "pos": [0.15, 0.05, 0.6],  # table_height(0.5) + 0.1
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_lack_0825.xml"
               }},
               "cup.xml": {{
                    "pos": [-0.15, -0.05, 0.6],
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_lack_0825.xml"
               }},
               "lamp.xml": {{
                    "pos": [0, 0.05, 0.6],
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_lack_0825.xml"
               }}
          }}
     }}

     Example 2 - Multiple Tables with Distributed Objects:
     {{
          "object_poses": {{
               "book.xml": {{
                    "pos": [0.1, 0, 0.6],
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_lack_0825.xml"  # Main table
               }},
               "laptop.xml": {{
                    "pos": [-0.1, 0, 0.6],
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_lack_0825.xml"  # Main table
               }},
               "cup.xml": {{
                    "pos": [0.1, 0, 0.55],
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_benno_0141.xml"  # Second table
               }},
               "plate.xml": {{
                    "pos": [-0.1, 0, 0.55],
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_benno_0141.xml"  # Second table
               }}
          }}
     }}

     Example 3 - Complex Setup with Multiple Tables (Avoiding Cabinet/Microwave Tables):
     {{
          "object_poses": {{
               # Objects on main table (table_lack_0825.xml)
               "book.xml": {{
                    "pos": [0.15, 0.05, 0.6],
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_lack_0825.xml"
               }},
               "laptop.xml": {{
                    "pos": [-0.15, -0.05, 0.6],
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_lack_0825.xml"
               }},
               # Objects on side table (table_benno_0141.xml)
               "cup.xml": {{
                    "pos": [0.1, 0, 0.55],
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_benno_0141.xml"
               }},
               "lamp.xml": {{
                    "pos": [-0.1, 0, 0.55],
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_benno_0141.xml"
               }}
               # Note: No objects placed on cabinet_table_1.xml or microwave_table.xml
          }}
     }}

     Example 4 - Study Setup with Evenly Distributed Objects:
     {{
          "object_poses": {{
               # Study materials on main desk
               "laptop.xml": {{
                    "pos": [0, 0, 0.6],  # Centered on desk
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_lack_0825.xml"
               }},
               "book.xml": {{
                    "pos": [0.15, 0.05, 0.6],  # Right side
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_lack_0825.xml"
               }},
               # Accessories on side table
               "lamp.xml": {{
                    "pos": [0, 0, 0.55],  # Centered on side table
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_benno_0141.xml"
               }},
               "cup.xml": {{
                    "pos": [0.1, 0.05, 0.55],  # Corner of side table
                    "quat": [1, 0, 0, 0],
                    "object_placing_furniture": "table_benno_0141.xml"
               }}
          }}
     }}

     **Output Format:**
     {{
          "object_poses": {{
               "object1.xml": {{"pos": [x, y, z], "quat": [w, x, y, z], "object_parent_furniture": "furniture1.xml"}},
               "object2.xml": {{"pos": [x, y, z], "quat": [w, x, y, z], "object_parent_furniture": "furniture2.xml"}},
               ...
          }}
     }}
     """
     
     # OpenAI API call
     response = openai.ChatCompletion.create(
          model="gpt-4",
          messages=[
               {"role": "system", "content": "You are an assistant that assigns objects to furniture and positions them appropriately. Always respond with JSON inside a code block."},
               {"role": "user", "content": prompt}
          ],
          temperature=0.2
     )
     
     assistant_response = response['choices'][0]['message']['content']
     
     # Try multiple JSON extraction methods
     try:
          # Method 1: Try to find JSON in code block
          json_block_match = re.search(r'```(?:json)?\s*({\s*".*?}\s*)```', assistant_response, re.DOTALL)
          if json_block_match:
               json_str = json_block_match.group(1)
          else:
               # Method 2: Try to find the largest JSON-like structure
               json_matches = re.finditer(r'({(?:[^{}]|(?R))*})', assistant_response)
               json_candidates = [m.group(0) for m in json_matches]
               if json_candidates:
                    # Select the largest JSON structure
                    json_str = max(json_candidates, key=len)
               else:
                    # Method 3: Find outermost braces
                    start = assistant_response.find('{')
                    end = assistant_response.rfind('}')
                    if start != -1 and end != -1:
                         json_str = assistant_response[start:end + 1]
                    else:
                         raise ValueError("No valid JSON structure found in response")

          # Clean the JSON string
          json_str = re.sub(r'//.*?(?:\n|$)', '', json_str, flags=re.MULTILINE)  # Remove inline comments
          json_str = re.sub(r'#.*?(?:\n|$)', '', json_str, flags=re.MULTILINE)   # Remove # comments
          json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)         # Remove block comments
          json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)                     # Remove trailing commas
          json_str = re.sub(r'\s+', ' ', json_str.strip())                       # Cleanup whitespace

          # Parse JSON
          json_data = json.loads(json_str)

          # Process and validate positions
          final_poses = {"object_poses": {}}
          furniture_object_positions = {}

          # Load furniture list if not already loaded
          if isinstance(furniture_json_path, str):
               with open(furniture_json_path, 'r') as f:
                    furniture_list = json.load(f)
          else:
               furniture_list = furniture_json_path  # Assume it's already loaded

          for obj_name, obj_pose in json_data.get("object_poses", {}).items():
               supporting_furniture = obj_pose.get("object_placing_furniture")

               # Validate supporting furniture
               if not supporting_furniture or supporting_furniture not in furniture_list:
                    print(f"Warning: Invalid or missing supporting furniture for {obj_name}")
                    continue

               # Get supporting furniture dimensions
               furniture_size = furniture_list[supporting_furniture]["size"]
               supporting_furniture_height = furniture_size[2]

               # Track positions for collision avoidance
               if supporting_furniture not in furniture_object_positions:
                    furniture_object_positions[supporting_furniture] = []

               proposed_pos = [obj_pose["pos"][0], obj_pose["pos"][1]]

               # Find a valid position
               valid_pos = find_valid_position(
                    proposed_pos,
                    furniture_size,
                    furniture_object_positions[supporting_furniture],
                    min_distance=0.8
               )

               # Add to final poses
               furniture_object_positions[supporting_furniture].append(valid_pos)
               final_poses["object_poses"][obj_name] = {
                    "pos": [
                         valid_pos[0],
                         valid_pos[1],
                         supporting_furniture_height + 0.2  # Offset for height
                    ],
                    "quat": [0, 0, 0.707, 0.707],  # Force this specific quaternion for all objects
                    "object_placing_furniture": supporting_furniture
               }

          return final_poses

     except json.JSONDecodeError as e:
          print(f"JSON parsing error: {e}")
          print("Raw JSON string:", json_str)
          print("Full response:", assistant_response)
          return {"object_poses": {}}  # Return empty poses instead of failing
     except Exception as e:
          print(f"Unexpected error: {e}")
          print("Full response:", assistant_response)
          return {"object_poses": {}}  # Return empty poses instead of failing

def save_poses_to_json(furniture_json_path, object_json_path, furniture_poses, object_poses):
     """
     Save furniture poses and object poses to separate JSON files.

     Parameters:
     - furniture_json_path (str): Path to save furniture poses JSON.
     - object_json_path (str): Path to save object poses JSON.
     - furniture_poses (dict): Dictionary containing furniture poses.
     - object_poses (dict): Dictionary containing object poses.
     """
     # Save furniture poses
     with open(furniture_json_path, 'w') as f:
          json.dump(furniture_poses, f, indent=4)
     print(f"Furniture poses saved to {furniture_json_path}")
          
     # Save object poses
     with open(object_json_path, 'w') as f:
          json.dump(object_poses, f, indent=4)
     print(f"Object poses saved to {object_json_path}")

def check_collision(pos1, pos2, min_distance=0.6):
    """Check if two positions are too close to each other"""
    dx = abs(pos1[0] - pos2[0])
    dy = abs(pos1[1] - pos2[1])
    distance = (dx**2 + dy**2)**0.5
    return distance < min_distance

def find_valid_position(pos, table_size, existing_positions, min_distance=0.8, max_attempts=100):
    """Find a valid position that doesn't collide with existing objects"""
    edge_margin = 0.1  # Margin from table edges
    max_x = (table_size[0] / 2) - edge_margin
    max_y = (table_size[1] / 2) - edge_margin
    original_x = max(min(pos[0], max_x), -max_x)
    original_y = max(min(pos[1], max_y), -max_y)

    # Try the original position
    if not any(check_collision([original_x, original_y], existing_pos, min_distance)
               for existing_pos in existing_positions):
        return [original_x, original_y]

    # Generate random valid positions
    for _ in range(max_attempts):
        x = random.uniform(-max_x, max_x)
        y = random.uniform(-max_y, max_y)
        if not any(check_collision([x, y], existing_pos, min_distance) for existing_pos in existing_positions):
            return [x, y]

    # If no valid position found, find the furthest position
    best_pos = [original_x, original_y]
    max_distance = 0

    for _ in range(50):  # Try more random positions for the furthest one
        x = random.uniform(-max_x, max_x)
        y = random.uniform(-max_y, max_y)
        min_distance_to_existing = min(
            (abs(x - existing_pos[0])**2 + abs(y - existing_pos[1])**2)**0.5
            for existing_pos in existing_positions
        )
        if min_distance_to_existing > max_distance:
            max_distance = min_distance_to_existing
            best_pos = [x, y]

    return best_pos

def extract_json_from_response(assistant_response):
    try:
        # Attempt to match JSON block in markdown format
        json_block_match = re.search(r'```json\n(.*?)\n```', assistant_response, re.DOTALL)

        if not json_block_match:
            print("No JSON block detected. Attempting to parse inline JSON.")
            
            # Fallback: Look for a JSON-like structure
            possible_json_start = assistant_response.find('{')
            possible_json_end = assistant_response.rfind('}')
            if possible_json_start != -1 and possible_json_end != -1:
                json_str = assistant_response[possible_json_start:possible_json_end + 1]
            else:
                raise ValueError("No valid JSON structure found in assistant response.")
        else:
            # Extract JSON string
            json_str = json_block_match.group(1)

        # Remove inline comments (if present)
        json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)  # Remove // comments
        json_str = re.sub(r'#.*$', '', json_str, flags=re.MULTILINE)  # Remove # comments
        json_str = re.sub(r'\s+', ' ', json_str.strip())  # Cleanup extra whitespace

        # Debugging: Print cleaned JSON string
        print("Cleaned JSON String:", json_str)

        # Parse the cleaned JSON string
        json_data = json.loads(json_str)
        return json_data

    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        print("Failed JSON String:", json_str)
        return {}
    except Exception as e:
        print(f"Error extracting JSON: {e}")
        print("Assistant Response:", assistant_response)
        return {}
