import datetime
import json
import logging
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

PAR_DIR = Path(__file__).resolve().parent
CONFIG_DIR = PAR_DIR / "configs"


class FileIO():
    def __init__(self, config):
        config_file = CONFIG_DIR / config
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)

        self._img_root_dir = Path(self.config["file_io"]["path"])
        self._logdir = Path(self.config["file_io"]["logdir"])

    def store_exception(self, exception):
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        self._logdir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(self._logdir / "logs.log", mode="a")

        FORMAT = '%(asctime)s: %(message)s'

        logging.basicConfig(level=logging.DEBUG, format=FORMAT, handlers=[handler])
        logging.error("Error in Streamlit App", exc_info=exception)

    def store_image_with_predictions(self, image, predictions):
        folder_name = self._img_root_dir / datetime.datetime.now().isoformat()
        folder_name.mkdir(parents=True)

        if image is not None:
            with open(folder_name / "predictions.json", "w") as outfile:
                json.dump(predictions, outfile)

            img = Image.fromarray(image)
            img.save(folder_name / "image.jpg", format="JPEG")

    def load_image_with_predictions(self, folder):
        folder = Path(folder)

        with open(folder / "predictions.json", "r") as infile:
            predictions = json.load(infile)

        image = Image.open(folder / "image.jpeg")

        return np.array(image), predictions

    def list_flagged_directory(self):
        return [x for x in self._img_root_dir.iterdir() if x.is_dir()]
