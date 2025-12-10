# wget https://download.blender.org/release/Blender3.3/blender-3.3.1-linux-x64.tar.xz -P ./02_01_generate_scene/blender/
# tar -xvf ./02_01_generate_scene/blender/blender-3.3.1-linux-x64.tar.xz -C ./02_01_generate_scene/blender/

eval "$(conda shell.bash hook)"
conda activate sdxgen311_test

python ./02_01_generate_scene/settings/get_dataset.py
python ./02_01_generate_scene/settings/get_ckpt.py