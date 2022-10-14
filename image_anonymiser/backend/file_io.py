import datetime
import json
import logging
import typing
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from PIL import Image

PAR_DIR = Path(__file__).resolve().parent
CONFIG_DIR = PAR_DIR / "configs"


class FileIO():
    """ File-Based outputs of the application
    """

    def __init__(self, config):
        self._load_config(config)

        self._img_root_dir = Path(self.config["file_io"]["flagged_path"])
        self._feedback_dir = Path(self.config["file_io"]["feedback_path"])
        self._logdir = Path(self.config["file_io"]["logdir"])

        self._ensure_dirs_exist()

    def _load_config(self, config: str):
        config_file = CONFIG_DIR / config
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)

    def _ensure_dirs_exist(self):
        self._img_root_dir.mkdir(parents=True, exist_ok=True)
        self._feedback_dir.mkdir(parents=True, exist_ok=True)
        self._logdir.mkdir(parents=True, exist_ok=True)

    def _current_time_str(self):
        return datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

    def store_exception(self, exception: Exception) -> None:
        """ Exception Logging
        Logs an exception from the application into the logs.log file
        in the logdir specified by the config
        Args:
            exception: Exception to log
        """

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        handler = logging.FileHandler(self._logdir / "logs.log", mode="a")
        FORMAT = '%(asctime)s: %(message)s'

        logging.basicConfig(level=logging.DEBUG, format=FORMAT, handlers=[handler])
        logging.error("Error in Streamlit App", exc_info=exception)

    def store_image_with_predictions(self, image: np.array, additional_info: typing.Dict, predictions: typing.Dict) -> None:
        """ Storing Flagged Images
        Store image together with the predictions, both user-defined and model-detected.
        Args:
            image(np.array): image to store
            additional_info(dict): additional information for the anonymiser
            predictions(dict): predictions dictionary from the detector component
        """

        folder_name = self._img_root_dir / self._current_time_str()
        folder_name.mkdir()

        if image is not None:
            with open(folder_name / "predictions.json", "w") as outfile:
                json.dump(predictions, outfile)

            with open(folder_name / "additional_info.json", "w") as outfile:
                json.dump(additional_info, outfile)

            img = Image.fromarray(image)
            img.save(folder_name / "image.jpeg", format="JPEG")

    def load_image_with_predictions(self, folder: str) -> (np.array, typing.Dict, typing.Dict):
        """ Get Flagged Image
        Loads image and predictions, as stored by the store_image_with_predictions method
        Args:
            folder (str): folder name containing the image and predicitons
        Returns:
            tuple (array, dict, dict)
                image
                predictions
                additional info.
        """

        folder = Path(folder)

        if Path(folder / "predictions.json").exists():
            with open(folder / "predictions.json", "r") as infile:
                predictions = json.load(infile)
        else:
            predictions = None

        if Path(folder / "additional_info.json").exists():
            with open(folder / "additional_info.json", "r") as infile:
                additional_info = json.load(infile)
        else:
            additional_info = None

        if Path(folder / "image.jpeg").exists():
            image = Image.open(folder / "image.jpeg")
            image = np.array(image)
        else:
            image = None

        return image, predictions, additional_info

    def list_flagged_directory(self, top: int = 20) -> typing.List[Path]:
        """
        Show contents of the user-flagged image directory.
        Only return [top] records, sorted in reverse order
        This way, and with us having date in the folder name ensures, that
        we return the newest records.
        Args:
            top (int): Amount of records to return
        Returns: list of list of paths to the files - [top] items are returned in reverse order
        """

        items = [x for x in self._img_root_dir.iterdir() if x.is_dir()]
        items.sort(reverse=True)

        return items[:top]

    def store_feedback(self, name: str, feedback: str) -> None:
        """
        Store User Feedback into a file
        Args:
            name: Username, if supplied by the user
            feedback: String Feedback
        """

        with open(self._feedback_dir / "feedback.csv", "a") as f:
            f.write(f"{name},{self._current_time_str()},{feedback}\n")

    def get_feedback(self) -> pd.DataFrame:
        """
        Read User Feedback
        Args:
            filename: path to filename where to red from
        Returns: pandas Dataframe of user feedbacks
        """
        if not Path(self._feedback_dir / "feedback.csv").exists():
            return pd.DataFrame(columns=["User", "Date", "Feedback"])
        else:
            return pd.read_csv(self._feedback_dir / "feedback.csv", names=["User", "Date", "Feedback"])
