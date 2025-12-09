import os
import sys
from pathlib import Path
CURRENT_FILE_PARENT_0 = Path(__file__).parents[0]
sys.path.append(str(CURRENT_FILE_PARENT_0))
CURRENT_FILE_PARENT_1 = Path(__file__).parents[1]
sys.path.append(str(CURRENT_FILE_PARENT_1))

import argparse
import random
import pickle
import copy
import glob

from tqdm import tqdm
import numpy as np
import torch
from torch.utils.data import DataLoader
import torch.nn.functional as F
from diffusers.training_utils import EMAModel

from src.utils.util import *
from src.utils.visualize import *
from src.data import filter_function, get_encoded_dataset, get_dataset_raw_and_encoded
from src.data.threed_future_dataset import ThreedFutureDataset
from src.data.threed_front_dataset_base import trs_to_corners
from src.data.utils_text import compute_loc_rel, reverse_rel
from src.models import model_from_config, ObjectFeatureVQVAE

relation_class = ['above', 'left of', 'in front of', 'closely left of', 'closely in front of', 'below', 'right of', 'behind', 'closely right of', 'closely behind', None]
object_class = ['Sofa', 'Lighting', 'Bed', 'Table', 'Cabinet', 'Stool', 'Chair', 'Others']


def mj2instructscene(corners):
    new_corners = []
    for corner in corners:
        new_corner = corner.copy()
        new_corner[1] = corner[2]

        new_corner[2] = -corner[1]
        new_corners.append(new_corner)
    return np.array(new_corners)

        
def main():
    # /home/ailab/Workspace/ailab-InstructScene/out/diningroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_00109/0003@0419bc7b-5bd0-47fc-802a-69c21ee0c80b_LivingDiningRoom-33368_cfg1.0_1.0/tmp
    mj_data_dir_list = [
        '/home/ailab/Workspace/scene-gen-mujoco/data_1128_new_00',
        '/home/ailab/Workspace/scene-gen-mujoco/data_1128_new_01',
        '/home/ailab/Workspace/scene-gen-mujoco/data_1128_new_02',
        '/home/ailab/Workspace/scene-gen-mujoco/data_1128_new_03',
    ]

    eval_scene_list = []
    for mj_data_dir in mj_data_dir_list:
        eval_scene_list_part = os.listdir(mj_data_dir)
        eval_scene_list.extend(eval_scene_list_part)

    eval_scene_list.sort()

    score_dict={}

    all_compare_results = {}
    for i, scene in enumerate(eval_scene_list):
        rel_counts, rel_counts_correct, rel_counts_obj_class = 0, 0, 0
        scene_num = scene.split('@')[0]
        if scene_num == "0101":
            pass

            # if not os.path.isdir(os.path.join(mj_data_dir, scene)):
            #     continue
            #! gt
            json_dir = glob.glob(f'{os.path.join(os.path.dirname(mj_data_dir_list[0]), "*", scene)}')[0]
            gt_json_path = os.path.join(json_dir, 'ailab_eval.json')
            with open(gt_json_path, 'r') as f:
                gt_json = json.load(f)
            
            triplet_gt_list = []
            triplet_gt_list_nat = []
            all_compare_results[f'{int(scene_num)}'] = {}
            all_compare_results[f'{int(scene_num)}']['description'] = gt_json['description']
            all_compare_results[f'{int(scene_num)}']['num'] = scene.split('@')[0]
            all_compare_results[f'{int(scene_num)}']['GT_triplet'] = []
            for idx in gt_json['triplet']:
                triplet_gt_list.append(gt_json['triplet'][idx]['triplet_class_id'])
                triplet_gt_list_nat.append(gt_json['triplet'][idx]['triplet_class'])
                all_compare_results[f'{int(scene_num)}']['GT_triplet'].append(gt_json['triplet'][idx]['triplet_class'])

            #! pred
            # todo: load new json from mujoco object position
            pred_json_path = gt_json_path.replace('ailab_eval.json', 'objects_mj_eval.json')
            with open(pred_json_path, 'r') as f:
                pred_json = json.load(f)

            #1. 물체들 위치 좌표 얻기
            triplet_pred_list = []
            triplet_pred_list_nat = []
            for idx_1 in pred_json['objects']:
                for idx_2 in pred_json['objects']:
                    if idx_1 == idx_2:
                        continue
                    corners1 = np.array(pred_json['objects'][idx_1]['corners'])
                    corners2 = np.array(pred_json['objects'][idx_2]['corners'])
                    # corners1 = mj2instructscene(corners1)
                    # corners2 = mj2instructscene(corners2)
                    name1 = pred_json['objects'][idx_1]['ailab_category'].lower()
                    name2 = pred_json['objects'][idx_2]['ailab_category'].lower()

                    if name1 == 'lighting':
                        name1 = 'lamp'
                    if name2 == 'lighting':
                        name2 = 'lamp'

                    loc_rel = compute_loc_rel(corners1, corners2,
                                                    name1=name1,
                                                    name2=name2)
                    loc_rel_class = relation_class.index(loc_rel)
                    
                    class_1 = pred_json['objects'][idx_1]['class_id']
                    class_1_name = pred_json['objects'][idx_1]['ailab_category']
                    class_2 = pred_json['objects'][idx_2]['class_id']
                    class_2_name = pred_json['objects'][idx_2]['ailab_category']

                    triplet_pred_list.append([class_1, loc_rel_class, class_2])
                    triplet_pred_list_nat.append([class_1_name, loc_rel, class_2_name])

            all_compare_results[f'{int(scene_num)}']['Pred_triplet'] = triplet_pred_list_nat

            before_rel_counts_obj_class = copy.deepcopy(rel_counts_obj_class)
            if len(triplet_gt_list) == 0:
                continue

            temp_match = []
            temp_match_nat = []
            temp_match_semi = []
            temp_match_semi_nat = []
            for gt_idx, triplet_gt in enumerate(triplet_gt_list):
                if triplet_gt in triplet_pred_list:
                    rel_counts_correct += 1  # 완전 일치
                    temp_match.append((gt_idx, triplet_gt))
                    temp_match_nat.append((gt_idx, triplet_gt_list_nat[gt_idx]))
                # 0번, 2번 인덱스만 비교 (subject, object 클래스만 일치)
                for j, triplet_pred in enumerate(triplet_pred_list):
                    if triplet_gt[0] == triplet_pred[0] and triplet_gt[2] == triplet_pred[2]:
                        rel_counts_obj_class += 1
                        temp_match_semi.append((gt_idx, triplet_gt))
                        temp_match_semi_nat.append((gt_idx, triplet_gt_list_nat[gt_idx]))
                        break
                rel_counts += 1
                before_rel_counts_obj_class +=1
            if before_rel_counts_obj_class != rel_counts_obj_class:
                print(f'No object class match for scene: {scene}')

            all_compare_results[f'{int(scene_num)}']['Correct_Full_Match'] = temp_match        
            all_compare_results[f'{int(scene_num)}']['Correct_Full_Match_Nat'] = temp_match_nat
            all_compare_results[f'{int(scene_num)}']['Correct_ObjectClass_Match'] = temp_match_semi
            all_compare_results[f'{int(scene_num)}']['Correct_ObjectClass_Match_Nat'] = temp_match_semi_nat
            score_dict[scene_num] = {
                'total': rel_counts,
                'rel_correct_counts': rel_counts_correct,
                'obj_class_correct_counts': rel_counts_obj_class
            }



            # for triplet_gt in triplet_gt_list:
            #     if triplet_gt in triplet_pred_list:
            #         rel_counts_correct += 1
            #     else:
            #         print(f'Incorrect triplet: {triplet_gt}')
            #     rel_counts += 1

            # rel_counts, rel_counts_correct 계산
            print(f'Relation Accuracy: {rel_counts_correct} / {rel_counts} = {rel_counts_correct/rel_counts:.4f}')
            print(f'Object Class Accuracy: {rel_counts_obj_class} / {rel_counts} = {rel_counts_obj_class/rel_counts:.4f}')
            print(f'Final Accuracy Mean: {(rel_counts_correct + rel_counts_obj_class) / (2 * rel_counts):.4f}')

    print_list = [
        
        0, 
        4, 
        12, 
        16,
        25,
        28,
        60,
        89,
        93,

        101,
        112,
        113,
        114,
        119,
        121,
        122,
        123,
        130,
        132,
        136,
        139,
        140,
        141,
        152,
        154,
        155,
        156,
        158,
        161,
        168,
        170,
        173,
        175,
        176,

    ]
    # for idx in print_list:
    for idx in list(all_compare_results.keys()):
        if int(idx) in print_list:
            print(f"Scene {all_compare_results[f'{idx}']['num']}: {all_compare_results[f'{idx}']['description']}")
            print(f"GT Triplets: {all_compare_results[f'{idx}']['GT_triplet']}")
            # print(f"Pred Triplets: {all_compare_results[f'{idx}']['Pred_triplet']}")
            print(f"Correct Full Match: {all_compare_results[f'{idx}']['Correct_Full_Match_Nat']}")
            print(f"Correct Object Class Match: {all_compare_results[f'{idx}']['Correct_ObjectClass_Match_Nat']}")
            print('---')

    score_json_save_path = os.path.join('/home/ailab/Workspace/scene-gen-mujoco/eval_ailab', 'each_scene_eval_score.json')
    with open(score_json_save_path, 'w') as f:
        json.dump(score_dict, f, indent=4)

if __name__ == '__main__':
    main()