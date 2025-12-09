#!/bin/bash

DATA_DIR="/home/ailab/Workspace/scene-gen-mujoco/data_1128_new_all"

# data_1128_new_00 아래의 모든 디렉토리를 순회
for dir in "$DATA_DIR"/*/; do
    # tmp 폴더가 존재하는지 확인
    if [ -d "${dir}tmp" ]; then
        obj_dir="${dir}tmp"
        echo "=========================================="
        echo "Processing: $obj_dir"
        echo "=========================================="
        python 1_scene_load_eval.py --obj_dir "$obj_dir"
        echo ""
    else
        echo "Skipping (no tmp folder): $dir"
    fi
done

echo "All done!"
