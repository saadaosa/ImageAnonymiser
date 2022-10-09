import datetime
import json
import logging
import typing
from pathlib import Path

import numpy as np
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

    def store_image_with_predictions(self, image: np.array, predictions: typing.Dict) -> None:
        """ Storing Flagged Images

        Store image together with the predictions, both user-defined and model-detected.

        Args:
            image(np.array): image to store
            predictions(dict): predictions dictionary from the detector component
        """

        folder_name = self._img_root_dir / self._current_time_str()
        folder_name.mkdir()

        if image is not None:
            with open(folder_name / "predictions.json", "w") as outfile:
                json.dump(predictions, outfile)

            img = Image.fromarray(image)
            img.save(folder_name / "image.jpeg", format="JPEG")

    def load_image_with_predictions(self, folder: str) -> (np.array, typing.Dict):
        """ Get Flagged Image

        Loads image and predictions, as stored by the store_image_with_predictions method

        Args:
            folder (str): folder name containing the image and predicitons

        Returns: tuple (array, dict) with image and predictions.
        """

        folder = Path(folder)

        with open(folder / "predictions.json", "r") as infile:
            predictions = json.load(infile)

        image = Image.open(folder / "image.jpeg")

        return np.array(image), predictions

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

        filename = f"{self._current_time_str()}_{name}.txt"
        path = self._feedback_dir / filename
        path.write_text(feedback)

    def get_feedback(self, filename: Path) -> str:
        """
        Read User Feedback

        Args:
            filename: path to filename where to red from

        Returns: String with user feedback

        """

        path = filename
        feedback = path.read_text()

        return feedback

    def list_feedback_directory(self, top: int = 20) -> typing.List[Path]:
        """
        Show contents of the user feedback directory.
        Only return [top] records, sorted in reverse order
        This way, and with us having date in the folder name ensures, that
        we return the newest records.

        Args:
            top (int): Amount of records to return

        Returns: list of paths to the files - [top] items are returned in reverse order

        """

        items = [x for x in self._feedback_dir.iterdir() if x.is_file()]
        items.sort(reverse=True)

        return items[:top]
