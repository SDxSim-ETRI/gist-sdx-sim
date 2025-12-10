import os
from huggingface_hub import hf_hub_url

#
os.system("mkdir -p ./02_01_generate_scene/out/threedfront_objfeat_vqvae/checkpoints")
url = hf_hub_url(repo_id="chenguolin/InstructScene_dataset", filename="threedfront_objfeat_vqvae_epoch_01999.pth", repo_type="dataset")
os.system(f"wget {url} -O ./02_01_generate_scene/out/threedfront_objfeat_vqvae/checkpoints/epoch_01999.pth")
url = hf_hub_url(repo_id="chenguolin/InstructScene_dataset", filename="objfeat_bounds.pkl", repo_type="dataset")
os.system(f"wget {url} -O ./02_01_generate_scene/out/threedfront_objfeat_vqvae/objfeat_bounds.pkl")

#
os.system("mkdir -p ./02_01_generate_scene/out/diningroom_sg2scdiffusion_objfeat/checkpoints")
url = hf_hub_url(repo_id="chenguolin/InstructScene_dataset", filename="diningroom_sg2scdiffusion_objfeat_epoch_01999.pth", repo_type="dataset")
os.system(f"wget {url} -O ./02_01_generate_scene/out/diningroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth")

#
os.system("mkdir -p ./02_01_generate_scene/out/diningroom_sgdiffusion_vq_objfeat/checkpoints")
url = hf_hub_url(repo_id="chenguolin/InstructScene_dataset", filename="diningroom_sgdiffusion_vq_objfeat_epoch_01239.pth", repo_type="dataset")
os.system(f"wget {url} -O ./02_01_generate_scene/out/diningroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01239.pth")