from pathlib import Path

import yaml

from image_anonymiser.models.detectors import *

PAR_DIR = Path(__file__).resolve().parent 
CONFIG_DIR = PAR_DIR.parent / "configs"

class DetectorBackend():
    """ Interface to a backend that returns predictions
    """

    def __init__(self, config):
        config_file = CONFIG_DIR / config
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)
        self.choices = list()
        self.descriptions = list()
        self.classes = list()
        self.detectors_fn = list()
        for d in self.config["detectors"]:
            detector = globals()[d["class"]](**d["params"])
            self.choices.append(d["name"])
            self.descriptions.append(d["description"])
            self.classes.append(detector.class_names) 
            self.detectors_fn.append(detector.detect)

    def detect(self, image, model_index, **params):
        """ Runs a detection model
        
        Params:
            image: numpy array, input image
            model_index: int, index of the dector model in self.detectors_fn
            params: model parameters

        Returns:
            predictions: dict, predictions as returned by the dection models
        """
        if model_index not in range(len(self.choices)):
            raise ValueError("Incorrect model index")
        else:
            predictions = self.detectors_fn[model_index](image, **params)
        return predictions