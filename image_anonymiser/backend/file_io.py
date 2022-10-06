import datetime
import json
from pathlib import Path

import cv2
import yaml

PAR_DIR = Path(__file__).resolve().parent
CONFIG_DIR = PAR_DIR / "configs"


class FileIO():
    def __init__(self, config):
        config_file = CONFIG_DIR / config
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)
        self._img_root_dir = Path(self.config["file_io"]["path"])

    def store_image_with_predictions(self, image, predictions):
        folder_name = self._img_root_dir / datetime.datetime.now().isoformat()
        folder_name.mkdir(parents=True)

        with open(folder_name / "predictions.json", "w") as outfile:
            json.dump(predictions, outfile)

        cv2.imwrite(folder_name / "image.jpg", image)

    def load_image_with_predictions(self, folder):
        folder = Path(folder)

        with open(folder / "predictions.json", "r") as infile:
            predictions = json.load(infile)

        image = cv2.imread(folder / "image.jpg")

        return image, predictions

    def list_flagged_directory(self):
        return [x for x in self._img_root_dir.iterdir() if x.is_dir()]
