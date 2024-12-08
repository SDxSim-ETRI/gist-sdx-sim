import os
import glob

# change object name korean to englist
def change_aihub_object_name():
    aihub_object_dir = 'models/assets/objects/aihub_objects/xmls'
    object_list = os.listdir(aihub_object_dir)
    indust_obj_dict = {
                        "1": "가스디퓨저",
                        "2": "가스토치",
                        "3": "간극게이지",
                        "4": "구리스건",
                        "5": "그랩훅",
                        "6": "기어풀러",
                        "7": "스크레퍼",
                        "8": "납흡입기",
                        "9": "니퍼",
                        "10": "대패",
                        "11": "덕트테이프",
                        "12": "도르레",
                        "13": "도배칼",
                        "14": "드라이버",
                        "15": "드릴_지그",
                        "16": "레이저거리측정기",
                        "17": "리베터기",
                        "18": "만력기",
                        "19": "망치",
                        "20": "멀티미터",
                        "21": "몽키스패너",
                        "22": "미장칼",
                        "23": "바이스그립",
                        "24": "밴드쏘",
                        "25": "버니어_캘리퍼스",
                        "26": "볼트커터",
                        "27": "분도기",
                        "28": "분사기",
                        "29": "브러쉬",
                        "30": "삼각자",
                        "31": "삽",
                        }
    indust_obj_eng_dict = {
                            '1': 'Gas diffuser',
                            '2': 'Gas torch',
                            '3': 'Gap gauge',
                            '4': 'Grease gun',
                            '5': 'Grab hook',
                            '6': 'Gear puller',
                            '7': 'Scraper',
                            '8': 'Solder sucker',
                            '9': 'Nipper',
                            '10': 'Plane',
                            '11': 'Duct tape',
                            '12': 'Pulley',
                            '13': 'Wallpaper knife',
                            '14': 'Screwdriver',
                            '15': 'Drill jig',
                            '16': 'Laser distance meter',
                            '17': 'Rivet gun',
                            '18': 'Clamp',
                            '19': 'Hammer',
                            '20': 'Multimeter',
                            '21': 'Monkey wrench',
                            '22': 'Trowel',
                            '23': 'Vise grip',
                            '24': 'Band saw',
                            '25': 'Vernier caliper',
                            '26': 'Bolt cutter',
                            '27': 'Protractor',
                            '28': 'Sprayer',
                            '29': 'Brush',
                            '30': 'Triangle ruler',
                            '31': 'Shovel',
                        }
    
    for object_file in object_list:
        # remove m***_ from object_file
        object_name = object_file.split("_", 1)[1]
        object_path = os.path.join(aihub_object_dir, object_file)
        # change object_file name to object_name in english version
        # get key from object_name
        object_name_idx = list(indust_obj_dict.keys())[list(indust_obj_dict.values()).index(object_name)]
        object_name_eng = indust_obj_eng_dict[object_name_idx]
        
        file_list = os.listdir(object_path)
        #* rename file name
        # for file in file_list:
        #     if file.endswith(".mtl"):
        #         continue

        #     if file.endswith(".xml"):
        #         with open(os.path.join(object_path, file), "r") as f:
        #             data = f.read()
        #         data = data.replace(object_file, object_name_eng)
        #         with open(os.path.join(object_path, file), "w") as f:
        #             f.write(data)
        #     # rename object_file to object_name_eng
        #     os.rename(os.path.join(object_path, file), os.path.join(object_path, file.replace(object_file, object_name_eng)))
        #* rename folder name
        new_path = os.path.join(aihub_object_dir, object_name_eng)
        if os.path.exists(object_path):
            os.rename(object_path, new_path)
        
                                    
change_aihub_object_name()