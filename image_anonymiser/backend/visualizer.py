import random
from abc import ABC, abstractmethod

import cv2
import numpy as np


class Visualizer(ABC):
    """ Abstract class for a visualizer used to display prediction outputs (image with boxes) 
        Any new visualizer added should implement the abstract methods
    """

    def __init__(self):
        pass

    @abstractmethod
    def visualise_boxes(self, image, predictions, incl_user_boxes=False):
        """ Function used to visualise boxes detected 
        
        Params:
            image: An input image in numpy format
            predictions: dict, as described in DetectionModel.detect
            incl_user_boxes, bool (default False)
        
        Returns:
            output: Output image in numpy format, a copy of the original image with boxes and labels   
        """

    def get_random_colors(self, num_colors):
        colors = [(a,b,c) for a in [0,51,102] for b in [0,51,102] for c in [0,51,102]]
        if num_colors <= len(colors):
            return random.sample(colors, num_colors)
        else:
            return random.choices(colors, num_colors)

class AdaptativeVisualizer(Visualizer):

    def __init__(self):
        super().__init__()

    def visualise_boxes(self, image, predictions, incl_user_boxes=False):
        output = np.copy(image)
        if incl_user_boxes and "boxes_adj" in predictions:
            boxes = predictions["boxes_adj"]
            pred_classes = predictions["pred_classes_adj"]
            instance_ids = predictions["instance_ids_adj"]
            pred_labels = predictions["pred_labels_adj"]
            is_user_box = predictions["is_user_box"]
        else:
            boxes = predictions["boxes"]
            pred_classes = predictions["pred_classes"]
            instance_ids = predictions["instance_ids"]
            pred_labels = predictions["pred_labels"]
            is_user_box = None
        multi_class = len(predictions["pred_labels"]) > 1
        colors = self._get_colors(predictions["name2int"], pred_labels, pred_classes, is_user_box)
        labels = list()
        for i_id in instance_ids:
            labels.append(f'{i_id}')
        thick = int((output.shape[0] + output.shape[1]) // 700.0)
        for box, color, label, c_id in zip(boxes, colors, labels, pred_classes):
            x1, y1, x2, y2 = box
            cv2.rectangle(output, (x1, y1), (x2, y2), color, thick)
            cname = predictions["class_names"][c_id]
            text=f"{cname[0].upper()}{label}" if multi_class else f"{label}"
            self._draw_text(output, box, text, color, thick)
        return output

    def _get_colors(self, name2int, pred_labels, pred_classes, is_user_box):
        random_colors = self.get_random_colors(len(pred_labels))
        color_map = {name2int[name]: color for name,color in zip(pred_labels,random_colors)}
        if is_user_box is not None:
            colors = []
            for pc, is_userbox in zip(pred_classes, is_user_box):
                c = (250,0,110) if is_userbox else color_map[pc]
                colors.append(c)
            return colors
        else:
            return [color_map[pc] for pc in pred_classes]

    def _get_optimal_font_scale(self, text, width, height, thick):
        for scale in reversed(range(0, 60, 1)):
            textSize = cv2.getTextSize(text, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=scale / 10, 
                thickness=thick)
            new_width, new_height = textSize[0]
            if (new_width <= width) and (new_height <= height):
                return scale / 10
        return 1

    def _draw_text(self, image, box, text, color, thick):
        x1, y1, x2, y2 = box
        ref_width = min(0.05*image.shape[0], (x2-x1) * 0.65)
        ref_height = min(0.05*image.shape[1], (y2-y1) * 0.65)
        font_scale = self._get_optimal_font_scale(text, ref_width, ref_height, thick)
        # set the text start position
        text_offset_x = x1 
        text_offset_y = y2
        text_w, text_h = cv2.getTextSize(text, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=font_scale, 
                thickness=thick)[0]
        cv2.rectangle(image, (text_offset_x, text_offset_y), (text_offset_x+text_w, text_offset_y-text_h), 
                    (255, 255, 255), cv2.FILLED)
        cv2.putText(image, text, (text_offset_x, text_offset_y), cv2.FONT_HERSHEY_SIMPLEX, 
            fontScale=font_scale, color=color, thickness=thick)

class SimpleVisualizer(Visualizer):

    def __init__(self):
        super().__init__()

    def visualise_boxes(self, image, predictions, incl_user_boxes = False):
        output = np.copy(image)
        if incl_user_boxes and "boxes_adj" in predictions:
            boxes = predictions["boxes_adj"]
            pred_classes = predictions["pred_classes_adj"]
            instance_ids = predictions["instance_ids_adj"]
        else:
            boxes = predictions["boxes"]
            pred_classes = predictions["pred_classes"]
            instance_ids = predictions["instance_ids"]
        color_map = {predictions["name2int"][name]:(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) 
                            for name in predictions["pred_labels"]} 
        colors = [color_map[id] for id in pred_classes]
        labels = list()
        multi_class = len(predictions["pred_labels"]) > 1
        for c_id,i_id in zip(pred_classes, instance_ids):
            if multi_class:
                labels.append(f'{predictions["class_names"][c_id]}_{i_id}')
            else:
                labels.append(f'{i_id}')
        for box,color,label in zip(boxes,colors,labels):
            x1, y1, x2, y2 = box
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            cv2.putText(output, label, (x1,y1), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, 1)
        return output