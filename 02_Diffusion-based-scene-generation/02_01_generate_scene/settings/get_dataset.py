import os
from huggingface_hub import hf_hub_url

url = hf_hub_url(repo_id="chenguolin/InstructScene_dataset", filename="InstructScene.zip", repo_type="dataset")
os.system(f"wget {url} -P ./dataset/ && unzip ./dataset/InstructScene.zip -d ./dataset/")
url = hf_hub_url(repo_id="chenguolin/InstructScene_dataset", filename="3D-FRONT.zip", repo_type="dataset")
os.system(f"wget {url} -P ./dataset/ && unzip ./dataset/3D-FRONT.zip -d ./dataset/")