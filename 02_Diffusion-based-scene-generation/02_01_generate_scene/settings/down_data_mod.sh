wget https://download.blender.org/release/Blender3.3/blender-3.3.1-linux-x64.tar.xz -P ./blender/
tar -xvf ./blender/blender-3.3.1-linux-x64.tar.xz -C ./blender/

python ./settings/get_dataset.py
python ./settings/get_ckpt.py