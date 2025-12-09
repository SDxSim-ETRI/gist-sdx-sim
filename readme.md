
# gist-sdx-sim

**SDx 연구과제 진행 결과물**

각 장소에 따라, 지시된 명령어 속에 등장하는 가구와 물체들을 자동으로 배치하는 프레임워크

## 구성
- file tree
    - 01_LLM-based-scene-generation
        - 2024년도 SDx 결과물 입니다.
    - 02_Diffusion-based-scene-generation
        - 2025년도 SDx 결과물 입니다.
        - 02_01_generate_scene
            - InstructScene을 baseline으로 하는 Diffusion 기반 가상환경 생성 프레임 워크 입니다.
        - 02_02_simulate_scene
            - 02_01_generate_scene의 결과물을 MuJoCo환경으로 porting 및 세부 조정을 하는 시스템 입니다.

<br>

<br>

- 요구사항
    - ubuntu 20.04 이상
    - Nvidia GPU VRAM 10GB 이상
    - CUDA driver 12 이상
    - python 3.11
    - 150GB 이상 (train / inference 에 필요한 Dataset 및 ckpt 용량)

    - tested on : 
        - ubuntu22.04 / RTX 3090 / cuda 12.1 / python3.11 / torch 2.1.0+cu121
        - ubuntu22.04 / RTX 4080 super / cuda 12.8 / python3.11 / 


### Installation
- 설치 및 이용
    - 각 폴더 내 readme를 따라 진행해야합니다.
        - [01_LLM-based-scene-generation/readme.md](01_LLM-based-scene-generation/readme.md)
        - [02_Diffusion-based-scene-generation/readme.md](02_Diffusion-based-scene-generation/readme.md)

