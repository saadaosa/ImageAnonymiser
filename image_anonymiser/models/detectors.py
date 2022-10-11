import pickle
from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import detectron2.projects.deeplab
import easyocr
import numpy as np
import torch
from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog
from detectron2.engine import DefaultPredictor
from facenet_pytorch import MTCNN

DETECTRON_DEFAULT = "COCO-PanopticSegmentation/panoptic_fpn_R_50_3x.yaml"
PAR_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = PAR_DIR / "artifacts"

class DetectionModel(ABC):
    """ Abstract class for a detection model 
        Any new model added should implement the abstract methods and return the output in a unified format
    """

    def __init__(self):
        pass

    @abstractmethod
    def detect(image, **params):
        """ Detect objects in an image and store the results in self.predictions 
        
        Params:
            image: An input image in numpy format
            params: kwargs that are specific to each detection model
        Returns:
            predictions: A dict that should contain the following keys:
                - pred_classes: list[int], ids of the classes detected in the image
                - pred_labels: list[str], names corresponding to the classes detected
                - pred_scores: list[float], scores representing the model certainty about the class detected
                - boxes: list[list[int]], coordiantes of the box (x1,y1,x2,y2) for each class detected
                - masks: list[list[bool]], for each class detected the mask (same shape as the image)
                        that contains True if the pixel corresponds to the class. This output is generated by
                        segmentation models
                - class_names: list[str], name of each class that can be detected by the model
                - name2int: dict, mapping from class names to ids 
                - instance_ids: list[int], id of each instance within the class
        Notes:
            - All the keys above should be present in the output. If the model doen't produce the output 
            (e.g. doesn't support segmentation), the value should be an empty list
            - Other model specific keys can be added (e.g. text for ocr)
            - For the time being, all the outputs should be JSON serializable (to take into account web deployment) 
        """
        return None

class DetectronDetector(DetectionModel):
    """ Multi-class object detection and segmentation based on the Detectron2 library
        The model used is the Panoptic Segmentation model pre-trained on the COCO dataset
    """

    def __init__(self, cfg_name=DETECTRON_DEFAULT, weights_file_name = None, threshold=0.7, device='cpu'):
        super().__init__()
        self.cfg_name = cfg_name
        self.cfg = get_cfg()
        self.cfg.MODEL.DEVICE=device
        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = threshold
        self.cfg.merge_from_file(model_zoo.get_config_file(self.cfg_name))
        if weights_file_name is not None and Path(ARTIFACTS_DIR / weights_file_name).is_file():
            self.cfg.MODEL.WEIGHTS = str(ARTIFACTS_DIR / weights_file_name)
        else:
            self.cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(self.cfg_name)
        self.dataset = self.cfg.DATASETS.TRAIN[0]
        self.class_names = MetadataCatalog.get(self.dataset).thing_classes
        self.name2int = {self.class_names[i]:i for i in range(len(self.class_names))}
        self.threshold = threshold
        self.predictor = DefaultPredictor(self.cfg)

    def detect(self, image):
        predictions = dict()
        pred = self.predictor(image) # If no objects detected, pred will contain empty Tensors
        predictions["pred_classes"] = pred["instances"].pred_classes.cpu().numpy().tolist()
        predictions["pred_labels"] = [self.class_names[i] for i in list(set(predictions["pred_classes"]))]
        predictions["scores"] = pred["instances"].scores.cpu().numpy().tolist()
        predictions["boxes"] = pred["instances"].pred_boxes.tensor.cpu().numpy().astype(int).tolist()
        if hasattr(pred["instances"], "pred_masks"):
            predictions["masks"] = pred["instances"].pred_masks.cpu().numpy().tolist()
        else:
            predictions["masks"] = []
        predictions["class_names"] = self.class_names
        predictions["name2int"] = self.name2int
        predictions["instance_ids"] = list()
        counter = {self.name2int[label]:0 for label in predictions["pred_labels"]}
        for class_id in predictions["pred_classes"]:
            predictions["instance_ids"].append(counter[class_id])
            counter[class_id]+=1
        return predictions

class FaceNETDetector(DetectionModel):
    """ Face detection model using facenet
    """

    def __init__(self, min_face_size=20, thresholds=[0.6,0.7,0.7], device=None):
        super().__init__()
        self.min_face_size = min_face_size
        self.thresholds = thresholds
        self.device = device
        self.class_names = ['face']
        self.predictor = MTCNN(keep_all=True, min_face_size=self.min_face_size, thresholds=self.thresholds, 
                        device=self.device) 

    def detect(self, image):
        predictions = dict()
        boxes, probs = self.predictor.detect(image) #If no objects detected, boxes will be None
        if boxes is None:
            boxes = np.array([])
            probs = np.array([])
        else:
            boxes = boxes.astype(int)
            boxes[boxes < 0] = 0
            boxes[:,0][boxes[:,0] >= image.shape[1]] = image.shape[1]-1
            boxes[:,2][boxes[:,2] >= image.shape[1]] = image.shape[1]-1
            boxes[:,1][boxes[:,1] >= image.shape[0]] = image.shape[0]-1
            boxes[:,3][boxes[:,3] >= image.shape[0]] = image.shape[0]-1
        predictions["pred_classes"] = [0 for _ in range(len(probs))]
        predictions["pred_labels"] = ['face'] if len(predictions["pred_classes"]) > 0 else []
        predictions["scores"] = probs.tolist()
        predictions["boxes"] = boxes.tolist()
        predictions["masks"] = []
        predictions["class_names"] = self.class_names
        predictions["name2int"] = {'face':0}
        predictions["instance_ids"] = list(range(len(predictions["pred_classes"])))
        return predictions

class OCRDetector(DetectionModel):
    """ OCR model using easy ocr
    """

    def __init__(self, lang_list=["en"], gpu=False):
        super().__init__()
        self.lang_list = lang_list
        self.gpu = gpu
        self.model_storage_directory = ARTIFACTS_DIR
        self.class_names = ['text']
        self.reader = easyocr.Reader(self.lang_list, gpu=self.gpu, model_storage_directory=self.model_storage_directory)

    def detect(self, image):
        predictions = dict()
        pred = self.reader.readtext(image) # If no objects detected, pred be an empty list
        predictions["pred_classes"] = [0 for _ in range(len(pred))]
        predictions["pred_labels"] = ['text'] if len(predictions["pred_classes"]) > 0 else []
        predictions["scores"] = [p[2] for p in pred]
        predictions["boxes"] = np.array([[*p[0][0], *p[0][2]] for p in pred]).astype(int).tolist() # sometimes the function returns float!
        predictions["masks"] = []
        predictions["name2int"] = {'text':0}
        predictions["class_names"] = self.class_names
        predictions["instance_ids"] = list(range(len(predictions["pred_classes"])))
        predictions["text"] = [p[1] for p in pred]
        return predictions

class DetectronSingleDetector(DetectronDetector):
    """ Single-class object detection and segmentation based on the Detectron2 library
        Uses a multi-class model but returns the predictions only for a target class
    """

    def __init__(self, cfg_name=DETECTRON_DEFAULT, weights_file_name = None, threshold=0.7, device='cpu', target_id=0):
        super().__init__(cfg_name=cfg_name, weights_file_name = weights_file_name, threshold=threshold, device=device)
        self.target_id = target_id
        self.class_names = [MetadataCatalog.get(self.dataset).thing_classes[self.target_id]]

    def detect(self, image):
        predictions = dict()
        pred = self.predictor(image) # If no objects detected, pred will contain empty Tensors
        pred_classes = pred["instances"].pred_classes.cpu().numpy()
        mask = np.array([True if i == self.target_id else False for i in pred_classes]) 
        predictions["pred_classes"] = pred_classes[mask].tolist()
        predictions["pred_labels"] = [self.class_names[i] for i in list(set(predictions["pred_classes"]))]
        predictions["scores"] = pred["instances"].scores.cpu().numpy()[mask].tolist()
        predictions["boxes"] = pred["instances"].pred_boxes.tensor.cpu().numpy().astype(int)[mask].tolist()
        if hasattr(pred["instances"], "pred_masks"):
            predictions["masks"] = pred["instances"].pred_masks.cpu().numpy()[mask].tolist()
        else:
            predictions["masks"] = []
        predictions["class_names"] = self.class_names
        predictions["name2int"] = {self.class_names[0]:self.target_id}
        predictions["instance_ids"] = list(range(len(predictions["pred_classes"])))
        return predictions

class FaceDetector(DetectionModel):
    """Face Detector that performs face detection with facenet and face segmentation
    with deeplab
    """
    def __init__(self, min_face_size=20, thresholds=[0.6,0.7,0.7], expansion=20, deeplab_model="", device=None):
        """Initialises facenet mtcnn input params and creates the deeplab default predictor
        """
        self.min_face_size = min_face_size
        self.thresholds = thresholds
        self.device = device
        self.class_names = ['face']
        self.facenet = FaceNETDetector(self.min_face_size, self.thresholds, self.device)

        if deeplab_model:
            deeplab_cfg_file = ARTIFACTS_DIR/(deeplab_model+"_cfg.pkl")
            deeplab_model_file = ARTIFACTS_DIR/(deeplab_model+".pth")
            if not deeplab_cfg_file.exists() or not deeplab_model_file.exists():
                import wandb
                api = wandb.Api()
                artifact = api.artifact(f"fsdl_2022/face-seg/{deeplab_model}.pth:latest").download()
                deeplab_model_file = artifact+f"/{deeplab_model}.pth"
                artifact = api.artifact(f"fsdl_2022/face-seg/{deeplab_model}_cfg.pkl:latest").download()
                deeplab_cfg_file = artifact+f"/{deeplab_model}_cfg.pkl"
            else:
                deeplab_cfg_file = str(deeplab_cfg_file)
                deeplab_model_file = str(deeplab_model_file)
        else:
            raise Exception("deeplab_model was not supplied for the face detector, Please add this to the backend config.yml")

        self.deeplab_cfg = pickle.load(open(deeplab_cfg_file, "rb"))
        self.deeplab_cfg.defrost()
        device = device or "cpu"
        if device == "cpu":
            self.deeplab_cfg.MODEL.RESNETS.NORM = "BN"
            self.deeplab_cfg.MODEL.SEM_SEG_HEAD.NORM = "BN"
        self.deeplab_cfg.MODEL.DEVICE = device
        self.deeplab_cfg.MODEL.WEIGHTS = deeplab_model_file
        # subclass the default predictor to enable batched inferrence
        class DeepLabPredictor(DefaultPredictor):
            def __call__(self, images):
                with torch.no_grad():
                    inputs = []
                    for image in images:
                        if self.input_format == "RGB":
                            image = image[:, :, ::-1]
                        height, width = image.shape[:2]
                        image = self.aug.get_transform(image).apply_image(image)
                        image = torch.as_tensor(image.astype("float32").transpose(2, 0, 1))
                        inputs += [{"image": image, "height": height, "width": width}]
                    predictions = self.model(inputs)
                    return predictions 

        self.deeplab = DeepLabPredictor(self.deeplab_cfg)
        self.expansion  = expansion
        
    def detect(self, image):
        """Detects bounding boxes with facenet and does segmentation with deeplab
        """
        predictions = self.facenet.detect(image)
        boxes = predictions["boxes"]
        refined_boxes = []
        masks = []
        h, w = image.shape[:2]
        image_patches = []
        image_patch_sizes = []
        exp_boxes = []
        max_w, max_h = 0, 0
        for box in boxes:
            x1,y1,x2,y2 = box
            exp_x1 = max(0, x1 - self.expansion)
            exp_y1 = max(0, y1 - self.expansion)
            exp_x2 = min(w, x2 + self.expansion)
            exp_y2 = min(h, y2 + self.expansion)
            image_patch = image.copy()[exp_y1:exp_y2+1, exp_x1:exp_x2+1]
            patch_h, patch_w = image_patch.shape[:2]
            max_w, max_h = max(max_w, patch_w), max(max_h, patch_h)
            image_patches += [image_patch]
            image_patch_sizes += [(patch_w, patch_h)]
            exp_boxes += [(exp_x1, exp_y1, exp_x2, exp_y2)]
            
        # resize_image patch to max size
        for i,image_patch in enumerate(image_patches):
            image_patches[i] = cv2.resize(image_patch, (max_w, max_h))

        results = self.deeplab(image_patches)
        for res, size, exp_box in zip(results, image_patch_sizes, exp_boxes):
            sem_seg = res["sem_seg"]
            sem_seg = torch.max(sem_seg, dim=0)[1].cpu().numpy()
            skin_pixels = ((sem_seg==1)*255).astype('uint8')
            skin_pixels = cv2.erode(skin_pixels, np.ones((5,5), np.uint8), iterations=1)
            skin_pixels = cv2.resize(skin_pixels, size)
            mask = np.zeros_like(image)[:,:,0]
            exp_x1, exp_y1, exp_x2, exp_y2 = exp_box
            mask[exp_y1:exp_y2+1, exp_x1:exp_x2+1] = skin_pixels
            ys, xs = mask.nonzero()
            min_y, min_x = np.min(ys), np.min(xs)
            max_y, max_x = np.max(ys), np.max(xs)
            refined_boxes += [[min_x,min_y,max_x,max_y]]
            masks += [mask]
            
        predictions["boxes"] = refined_boxes
        predictions["masks"] = masks
        
        return predictions    