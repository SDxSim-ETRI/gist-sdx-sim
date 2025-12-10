
# gist-sdx-sim
## 02_Diffusion-based-scene-generation

**2025년도 SDx 연구과제 진행 결과물**

각 장소에 따라, Diffusion 모델을 이용해 지시된 명령어 속에 등장하는 가구와 물체들로 Scene Graph를 생성하고 가상환경에서 Scene Graph가 나타내는 관계에 따라 가구와 물체들을 자동으로 배치하는 프레임워크

<br>

### Installation

- 요구사항
    - ubuntu 20.04 이상
    - Nvidia GPU VRAM 10GB 이상
    - CUDA driver 12 이상
    - python 3.11
    - 150GB 이상 (train / inference 에 필요한 Dataset 및 ckpt 용량)
    - tested on : 
        - ubuntu22.04 / RTX 3090 / cuda 12.1 / python3.11 / torch 2.1.0+cu121
        - ubuntu22.04 / RTX 4080 super / cuda 12.8 / python3.11 / 

- 설치
    - 레포 내 bash 파일 실행으로 데이터 다운로드 및 체크포인트 다운로드, conda 환경 설정을 마칩니다. 
        ```bash
        git clone https://github.com/SDxSim-ETRI/gist-sdx-sim
        cd 02_Diffusion-based-scene-generation
        sh ./02_01_generate_scene/settings/setup_mod.sh
        ```
    - 이후 코드 실행시, 스크립트로 부터 생성된 가상환경을 이용합니다.
        ```bash
        conda activate sdxgen311
        ```

<br>

### Code Description & Run
- 진행 순서
    - [asset 다운] 스크립트로 부터 dataset과 ckpt 파일을 다운 받습니다.
        - 1. blender 세팅 및 asset 다운로드 스크립트 실행
            - 이후 ckpt 파일이 존재하므로 [모델 학습] 순서는 건너뛰고 5를 수행하면됩니다.
    - [모델 학습] ckpt 파일을 다운받으면 아래 2-4까지는 skip합니다.
        - 2. (ckpt 존재, 학습 및 inference skip) 가구 피쳐 임베딩 모델 학습 (`objfeatvqvae`)
        - 3. (ckpt 존재, 학습 및 inference skip) 장면 내 가구간 관계 scene graph 생성 모델 학습 (`sg2sc`, scene graph -> scene coordinates)
        - 4. (ckpt 존재, 학습 skip) floor plan에 맞도록 장면 모델 학습  (`generate_sg`)
    - [scene obj 생성] 학습된 ckpt파일을 이용하여 inference 후 가상환경을 생성합니다.
        - 5. floor plan에 맞도록 장면 모델활용 배치 생성 (`generate_sg`, obj 배치 + blender 생성)
        - 6. MuJoCo 내 환경 생성

- 실행 (scene) 생성용 
    - Debug mode 시에는 하위 폴더를 (02_01_generate_scene/02_02_simulate_scene)workspace로 열어야합니다.
    - 1. asset 다운로드 스크립트 실행
        ```bash
        sh ./02_01_generate_scene/settings/down_data_mod.sh
        ```
    - 5. 텍스트에서 Scene Graph 모델 테스트
        ```bash
        cd 01_generate_scene
        python ./src/02_6_inference_generate_sg_mod.py
        ```
    - 6. 


- reference 
    - InstructScene 