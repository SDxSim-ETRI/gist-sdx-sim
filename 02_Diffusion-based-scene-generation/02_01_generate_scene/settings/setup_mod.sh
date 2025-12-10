eval "$(conda shell.bash hook)"
conda create -n sdxgen311_test python=3.11
conda activate sdxgen311_test

pip install --upgrade pip setuptools wheel

pip install torch==2.9.0 torchvision==0.24.0 torchaudio==2.9.0 --index-url https://download.pytorch.org/whl/cu128
pip install -r ./02_01_generate_scene/settings/requirements_mod.txt

python -c "import nltk; nltk.download('cmudict')"
