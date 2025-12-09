import xml.etree.ElementTree as ET
import random

tree = ET.parse('assets/partnet-mobility/41083/mobility.urdf')
root = tree.getroot()

# Dictionary to count instances of each visual name
visual_name_count = {}

# Iterate through all 'visual' elements
for visual in root.findall(".//visual"):
    # Get the original name attribute
    original_name = visual.get('name')
    
    # Increment the count for this visual name
    if original_name not in visual_name_count:
        visual_name_count[original_name] = 1
    else:
        visual_name_count[original_name] += 1

    # Generate a new unique name
    new_name = f"{original_name}-{visual_name_count[original_name]}"
    
    # Update the 'name' attribute with the new unique name
    visual.set('name', new_name)

collision_counter = 1
for link in root.findall(".//link"):
    for collision in link.findall("collision"):
        # Add a unique name if it doesn't already have one
        if "name" not in collision.attrib:
            collision.set("name", f"collision_{link.get('name')}_{collision_counter}")
            collision_counter += 1


# Save the modified URDF to a new file
tree.write('assets/partnet-mobility/41083/urdf/modified_mobility.urdf', xml_declaration=True, encoding='utf-8')

def add_jitter(value, jitter=1e-4):
    return str(float(value) + random.uniform(-jitter, jitter))

def apply_jitter_to_urdf(urdf_path, output_path):
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    
    for origin in root.iter('origin'):
        if 'xyz' in origin.attrib:
            x, y, z = origin.attrib['xyz'].split()
            origin.attrib['xyz'] = f"{add_jitter(x)} {add_jitter(y)} {add_jitter(z)}"
    
    tree.write(output_path, xml_declaration=True, encoding='utf-8')
    print(f"Jittered URDF saved to {output_path}")


mobility_urdf = 'assets/partnet-mobility/41083/urdf/modified_mobility.urdf'
jittered_urdf = 'assets/partnet-mobility/41083/urdf/jittered_mobility.urdf'
apply_jitter_to_urdf(mobility_urdf, jittered_urdf)
