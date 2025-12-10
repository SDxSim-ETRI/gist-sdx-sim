import os
from huggingface_hub import hf_hub_url

url = hf_hub_url(repo_id="chenguolin/InstructScene_dataset", filename="InstructScene.zip", repo_type="dataset")
os.system(f"wget {url} -P ./02_01_generate_scene/dataset/ && unzip ./02_01_generate_scene/dataset/InstructScene.zip -d ./02_01_generate_scene/dataset/")
url = hf_hub_url(repo_id="chenguolin/InstructScene_dataset", filename="3D-FRONT.zip", repo_type="dataset")
os.system(f"wget {url} -P ./02_01_generate_scene/dataset/ && unzip ./02_01_generate_scene/dataset/3D-FRONT.zip -d ./02_01_generate_scene/dataset/")