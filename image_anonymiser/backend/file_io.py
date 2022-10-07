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

    def store_image_with_predictions(self, image, predictions, feedback):
        folder_name = self._img_root_dir / datetime.datetime.now().isoformat()
        folder_name.mkdir(parents=True)

        if image is not None:
            with open(folder_name / "predictions.json", "w") as outfile:
                json.dump(predictions, outfile)

            cv2.imwrite(str(folder_name / "image.jpg"), image)

        if feedback is not None:
            with open(folder_name / "feedback.txt", "w") as outfile:
                outfile.write(feedback)

    def load_image_with_predictions(self, folder):
        folder = Path(folder)

        with open(folder / "predictions.json", "r") as infile:
            predictions = json.load(infile)

        image = cv2.imread(folder / "image.jpg")

        return image, predictions

    def list_flagged_directory(self):
        return [x for x in self._img_root_dir.iterdir() if x.is_dir()]
