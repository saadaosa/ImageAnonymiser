from pathlib import Path
import json
import cv2
import numpy as np
from argparse import ArgumentParser


LAPA_DATA_DIR = "/home/team_003/Data/LaPa"
LAPA_DATA_JSON_DIR = "/home/team_003/Data/LaPa/json"


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("--split","-S",default="train",type=str,help="Dataset split. Can be either train, val, test or all")
    parser.add_argument("--save","-s",action="store_true", help="Whether to save the prepared json file or not")
    return parser.parse_args()
    

def create_json(split="train", save=False):
    print(f"Preparing dataset json for {split} split")
    _dir = Path(LAPA_DATA_DIR)/split
    label_dir = _dir/"labels"
    images_dir = _dir/"images"
    dicts = []
    prev_file_name_length = 0 # for printing to console
    for image_file in images_dir.iterdir():
        file_name = str(image_file)
        image = cv2.imread(str(image_file))
        height, width, _ = image.shape
        image_id = image_file.stem
        sem_seg_file_name = label_dir/f"{image_id}.png"
        assert sem_seg_file_name.exists(), f"File does not exist, {str(sem_seg_file_name)}"
        sem_seg_file_name = str(sem_seg_file_name)
        seg_image = cv2.imread(sem_seg_file_name)
        seg_image = cv2.cvtColor(seg_image, cv2.COLOR_BGR2GRAY)
        # keep only hair and skin
        # hair = 10
        # skin = 1
        ones = np.ones_like(seg_image)
        zeros = np.zeros_like(seg_image)
        skin_hair_backg = ones # skin
        skin_hair_backg = np.where(seg_image == 10, zeros+2, skin_hair_backg) # hair
        skin_hair_backg = np.where(seg_image == 0, zeros, skin_hair_backg) # background
        cv2.imwrite(sem_seg_file_name, skin_hair_backg)
        
        dicts += [
            {
                "file_name":file_name,
                "height":height,
                "width":width,
                "image_id":image_id,
                "sem_seg_file_name":sem_seg_file_name,
            }
        ]
        print(f"Loaded file: {file_name if prev_file_name_length < len(file_name) else (file_name+'  '*(prev_file_name_length-len(file_name)))}", end="\r")
        prev_file_name_length = len(file_name)
        
    print("")
    
    if save:
        save_path = Path(LAPA_DATA_JSON_DIR)
        save_path.mkdir(parents=True, exist_ok=True)
        with open(save_path/f"{split}.json", "w") as f:
            json.dump(dicts, f)
        print(f"Saved json to {str(f.name)}")
        
    print("Done")
            
    return dicts


if __name__=="__main__":
    args = parse_args()
    if args.split != "all":
        create_json(args.split, save=args.save)
    else:
        for split in ["train", "val", "test"]:
            create_json(split, save=args.save)
    