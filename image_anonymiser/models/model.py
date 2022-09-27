import numpy as np
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer

PANOPTIC_MODEL = "COCO-PanopticSegmentation/panoptic_fpn_R_50_3x.yaml"

class Model():
    def __init__(self, cfg_name=PANOPTIC_MODEL, device='cpu'):
        self.cfg_name = cfg_name
        self.cfg = get_cfg()
        self.cfg.MODEL.DEVICE='cpu'
        self.cfg.merge_from_file(model_zoo.get_config_file(self.cfg_name))
        self.cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(self.cfg_name)
        self.dataset = self.cfg.DATASETS.TRAIN[0]
        self.class_names = MetadataCatalog.get(self.dataset).thing_classes
        self.name2int = {self.class_names[i]:i for i in range(len(self.class_names))}

    def detect(self, image, threshold):
        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = threshold
        predictor = DefaultPredictor(self.cfg)
        predictions = predictor(image)
        return predictions

    def draw_predictions(self, image, predictions):
        visualizer = Visualizer(image[:, :, ::-1], MetadataCatalog.get(self.dataset), scale=1)
        pred_image = visualizer.draw_instance_predictions(predictions["instances"]).get_image()
        return pred_image

    def process_predictions(self, predictions):
        predictions_proc = dict()
        predictions_proc["pred_classes"] = predictions["instances"].pred_classes.numpy()
        predictions_proc["pred_labels"] = [self.class_names[i] for i in list(set(predictions_proc["pred_classes"]))]
        predictions_proc["scores"] = predictions["instances"].scores.numpy()
        predictions_proc["boxes"] = predictions["instances"].pred_boxes.tensor.numpy().astype(int)
        predictions_proc["masks"] = predictions["instances"].pred_masks.numpy()
        return predictions_proc
        
    def get_class_prediction(self, target_id, predictions_proc):
        mask = np.array([True if i==target_id else False for i in predictions_proc["pred_classes"]])
        target_boxes = predictions_proc["boxes"][mask]
        target_pred_mask = np.sum(predictions_proc["masks"][mask], axis=0)
        mask_indices = np.where(target_pred_mask != 0)
        return target_boxes, mask_indices

    def get_object_labels(self, predictions):
        pred_classes = predictions["instances"].pred_classes.numpy()
        pred_labels = [self.class_names[instance] for instance in pred_classes]
        return list(set(pred_classes))
    