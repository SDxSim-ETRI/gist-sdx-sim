import mujoco
import mujoco_viewer
import os
import xml.etree.ElementTree as ET

# XML 파일 경로 설정
# output_file_path = "/home/geonhyup/Desktop/Research/pr_assets/data/furniture/table_feeding.urdf"
output_file_path = "/home/geonhyup/Desktop/Research/open-sim-mujoco/models/assets/objects/Wallpaper knife.xml"
# output_file_path = "/home/geonhyup/Desktop/Research/open-sim-mujoco/mujoco_menagerie/boston_dynamics_spot/scene.xml"
# output_file_path = "/home/geonhyup/Desktop/Research/open-sim-mujoco/models/assets/furniture_2/cabinet_bjorken_0203.xml"

# chair_bertil_0148.xml, chair_ivar_0668.xml
model = mujoco.MjModel.from_xml_path(output_file_path)

data = mujoco.MjData(model)

viewer = mujoco_viewer.MujocoViewer(model, data)

while viewer.is_alive:
    mujoco.mj_step(model, data)
    viewer.render()

# 뷰어 종료
viewer.close()