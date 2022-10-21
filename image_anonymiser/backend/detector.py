import base64
import os
from importlib import import_module
from io import BytesIO
from itertools import compress
from pathlib import Path

import cv2
import numpy as np
import PIL.Image
import requests
import yaml

PAR_DIR = Path(__file__).resolve().parent
CONFIG_DIR = PAR_DIR / "configs"


class DetectorBackend():
    """ Interface to a backend that returns predictions
    """

    def __init__(self, config, force_inapp=False):
        config_file = CONFIG_DIR / config
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)
        # setup predictor 
        self.detectors_fn = list()
        self.choices = list()
        self.descriptions = list()
        self.classes = list()
        self.predictor = "inapp" if force_inapp else self.config["predictor"]["type"]
        self.predictor_url = None
        if self.predictor == "inapp":
            models_module = import_module("image_anonymiser.models.detectors")
            for d in self.config["detectors"]:
                d_class = getattr(models_module, d["class"])
                if "params" in d:
                    detector = d_class(**d["params"])
                else:
                    detector = d_class()
                self.choices.append(d["name"])
                self.descriptions.append(d["description"])
                self.classes.append(detector.class_names) 
                self.detectors_fn.append(detector.detect)
        elif self.predictor == "api":
            self.predictor_url = os.environ.get("FASTAPIURL", "http://127.0.0.1:8000")
            self.get_endpoint_info()
        else:
            raise ValueError("Incorrect predictor type, should be inapp or api")
        # setup visualizer
        viz_module = import_module("image_anonymiser.backend.visualizer")
        v_class = getattr(viz_module, self.config["visualizer"]["class"])
        self.visualise_boxes = v_class().visualise_boxes


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
            if self.predictor_url is None:
                predictions = self.detectors_fn[model_index](image, **params)
            else:
                predictions = self._predict_from_endpoint(image, model_index) # Note: params are not used in api
        return predictions

    def get_pred_types(self, predictions, incl_user_boxes=False):
        """ Returns the types of predictions returned by the Detect method
        
        Params:
            predictions: dict, as described in DetectionModel.detect
        
        Returns:
            result: list, that contains the type of predictions ("box" for bouding boxes, 
                    "mask" for segmentation result)
        """
        result = list()
        if incl_user_boxes and "boxes_adj" in predictions:
            if predictions["boxes_adj"] != []: result.append("box")
        else:
            if predictions["boxes"] != []: result.append("box")
        if predictions["masks"] != []: result.append("mask")
        return result

    def get_pred_classes(self, predictions, incl_user_boxes=False):
        """ Returns the class names returnd by the Detect method

        Params:
            predictions: dict, as described in DetectionModel.detect
            incl_user_boxes, bool (default False)
        
        Returns:
            result: list, that contains the class names (without duplicates)
        """
        if incl_user_boxes and "boxes_adj" in predictions:
            return predictions["pred_labels_adj"]
        else:
            return predictions["pred_labels"]

    def get_instance_ids(self, class_name, predictions, incl_user_boxes=False):
        """ Returns the instances ids of for a given class

        Params:
            class_name: str, name of the class
            predictions: dict, as described in DetectionModel.detect
            incl_user_boxes, bool (default False)
        
        Returns:
            result: list, that contains "all" (to represent all ids) and the instance ids
        """
        result = ["all"]
        class_id = predictions["name2int"][class_name]
        if incl_user_boxes and "boxes_adj" in predictions:
            pred_classes = predictions["pred_classes_adj"]
            i_ids = predictions["instance_ids_adj"]
        else:
            pred_classes = predictions["pred_classes"]
            i_ids = predictions["instance_ids"]
        mask = [True if i == class_id else False for i in pred_classes]
        instance_ids = list(compress(i_ids, mask))
        if len(instance_ids) > 1: result.extend(instance_ids)
        return result

    def get_target_regions(self, class_name, instance_id, target_type, predictions, incl_user_boxes=False):
        """ Returns the target regions in the image 
        
        Params:
            class_name: str, the name of the classe that the user wants to anonymise
            instance_id: str, "all" or the id of the instance within the class
            target_type: str, "box" or "mask"
            predictions: dict, as described in DetectionModel.detect
            incl_user_boxes, bool (default False)

        Returns:
            result: numpy array, indices of the target pixels in the image
        """
        class_id = predictions["name2int"][class_name]
        if target_type == "box":
            if incl_user_boxes and "boxes_adj" in predictions:
                boxes = predictions["boxes_adj"]
                pred_classes = predictions["pred_classes_adj"]
            else:
                boxes = predictions["boxes"]
                pred_classes = predictions["pred_classes"]
            mask = np.array([True if i == class_id else False for i in pred_classes])
            boxes = np.array(boxes)[mask]
            if instance_id != "all":
                boxes = np.array([boxes[int(instance_id)]])
            result = self._get_indices_from_boxes(boxes)
        elif target_type == "mask":
            mask = np.array([True if i == class_id else False for i in predictions["pred_classes"]])
            seg_masks = np.array(predictions["masks"])[mask]
            if instance_id != "all":
                seg_masks = np.array([seg_masks[int(instance_id)]])
            seg_mask = np.sum(seg_masks, axis=0)
            result = np.where(seg_mask != 0)

        return result

    def _get_indices_from_boxes(self, boxes):
        """ Helper function to convert box coordinates into pixels
        """
        tmp = list()
        box_indices_y = list()
        box_indices_x = list()
        for box in boxes:
            x1, y1, x2, y2 = box
            tmp.extend((y, x) for y in range(y1, y2) for x in range(x1, x2))
        box_indices_y = [t[0] for t in tmp]
        box_indices_x = [t[1] for t in tmp]
        return (np.array(box_indices_y), np.array(box_indices_x))

    def add_labeled_box(self, box, label, predictions):
        """ Adds a user defined box to the predictions dictionary

        Params:
            box: list, box coordinates [x1, y1, x2, y2]
            label: str, class name that the box belongs to (should already be in predictions["class_names"])
            predictions: dict, as described in DetectionModel.detect

        Returns:
            predictions: dict, this is the input dictionary with additional key/value items:
                "user_boxes": The labels provided by the user
                "pred_classes_Adj": Ids of the classes detected including the ones added by the user
                "scores_adj: The original scores including 1 (100% certainty) for each user label
                "boxes_adj": The original boxes including the ones added by the user
                "instance_ids_adj": The original instance ids including the ones of the new user objects
                "is_user_box": list[bool] used to flag if the box has been added by the user or not  
        """
        if label in predictions["class_names"]:
            label_id = predictions["name2int"][label]
            if "user_boxes" in predictions:
                predictions["user_boxes"].append(box)
            else:
                predictions["user_boxes"] = [box]
                predictions["pred_classes_adj"] = predictions["pred_classes"].copy()
                predictions["scores_adj"] = predictions["scores"].copy()
                predictions["boxes_adj"] = predictions["boxes"].copy()
                predictions["instance_ids_adj"] = predictions["instance_ids"].copy()
                predictions["pred_labels_adj"] = predictions["pred_labels"].copy()
                predictions["is_user_box"] = [False for _ in predictions["boxes"]]

            predictions["scores_adj"].append(1)
            predictions["boxes_adj"].append(box)
            predictions["is_user_box"].append(True)

            if label not in predictions["pred_labels_adj"]:
                predictions["pred_labels_adj"].append(label)
            if len(predictions["class_names"]) > 1:
                new_id = 0
                if new_id in predictions["pred_classes_adj"]:
                    new_id = sum(1 if label_id == c else 0 for c in predictions["pred_classes_adj"])
            else:
                new_id = len(predictions["instance_ids_adj"])
            predictions["pred_classes_adj"].append(label_id)
            predictions["instance_ids_adj"].append(new_id)
        return predictions

    def get_endpoint_info(self):
        response = requests.get(f"{self.predictor_url}/info")
        info = response.json()
        self.choices = info["choices"]
        self.descriptions = info["descriptions"]
        self.classes = info["classes"]

    def _predict_from_endpoint(self, image, model_index):
        pil_img = PIL.Image.fromarray(image)
        buff = BytesIO()
        pil_img.save(buff, format="JPEG")
        byte_string = base64.b64encode(buff.getvalue()).decode("utf-8")
        response = requests.post(f"{self.predictor_url}/detect", json={"image_str": byte_string, 
                                                                "model_index": model_index})
        predictions = response.json()["predictions"]
        return predictions