conda create -n instructgen311 python=3.11
conda activate instructgen311

pip install --upgrade pip setuptools wheel

pip install torch==2.9.0 torchvision==0.24.0 torchaudio==2.9.0 --index-url https://download.pytorch.org/whl/cu128
pip install -r settings/requirements_mod.txt

python -c "import nltk; nltk.download('cmudict')"
