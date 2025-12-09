# scene-gen-mujoco
SDx(Software-Defined Everything) 지능 응용 개발 지원을 위한 개방형 시뮬레이터 핵심 기술 개발

## Installation
```
conda create -n sdx_scene_generation --clone instructscene
conda activate sdx_scene_generation
pip install -r requirements.txt
```

## 1. Making a json file redefined object class(ailab_category) for our evaluation 
```
# change the variable(data_dir) to your evaulation data directory in code
python 0_object_json_post_processing.py
```

## 2. MuJoCo Scene Loading and Make a json for evaluation
```
# Change a variable 'DATA_DIR' to your data directory.
bash run_scene_load.sh
```

## 2+. MuJoCo Scene Loading and Visualize a mujoco scene
```
python 1_scene_load.py --obj_dir data_1128_new_all/0172@f877d2a1-678f-49a0-a90e-e99ff27134c7_DiningRoom-13034_cfg1.0_1.0/tmp
```