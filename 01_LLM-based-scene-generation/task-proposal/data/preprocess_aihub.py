import os
import glob
import argparse


def main(args):
    
    mesh_root = 'assets/aihub/3d_mesh'
    if args.unzip:
        # unzip old and new files
        old_list = glob.glob(os.path.join(mesh_root, 'zipped', 'old', '*', '*.zip'))
        for old in old_list:
            if not os.path.exists(old.replace("zipped", "unzipped").replace(".zip", "")):
                os.system(f'mkdir -p {old.replace("zipped", "unzipped").replace(".zip", "")}')
            os.system(f'sudo unzip -o {old} -d {old.replace("zipped", "unzipped").replace(".zip", "")}')
        new_list = glob.glob(os.path.join(mesh_root, 'zipped', 'new', '*', '*.zip'))
        for new in new_list:
            if not os.path.exists(new.replace("zipped", "unzipped").replace(".zip", "")):
                os.system(f'mkdir -p {new.replace("zipped", "unzipped").replace(".zip", "")}')
            os.system(f'sudo unzip -o {new} -d {new.replace("zipped", "unzipped").replace(".zip", "")}')
        print('unzip done')
    # copy files to new directory if the file only exists in old directory
    old_list = glob.glob(os.path.join(mesh_root, 'unzipped', 'old', '*', '*'))
    new_list = glob.glob(os.path.join(mesh_root, 'unzipped', 'new', '*', '*'))
    for old in old_list:
        if not os.path.exists(old.replace("old", "new")):
            print(f'copy {old} to {old.replace("old", "new")}')
            os.system(f'cp -r {old} {old.replace("old", "new")}')
    
    
            
if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--unzip', action='store_true')
    args = args.parse_args()
    main(args)