""" Perform object detection/segmnentation on an image and allow the user to perform
    several anonymisation taks based on the object classes identified in the input
"""
import argparse
from collections import defaultdict

import gradio as gr
import numpy as np

from ..anonymiser.blur import blur_boxes, blur_pixels
from ..models.model import Model
from .anonymiserui import AnonymiserUI
from .modelui import ModelUI

DEFAULT_PORT = 7861

class App():
    def __init__(self):
        self.demo = gr.Blocks()
        self.model = Model()
        self.modelui = ModelUI()
        self.anonymiserui = AnonymiserUI(self.model.class_names)
    
    def make_ui(self):
        with self.demo:
            cache = defaultdict(int)
            self.title = gr.Markdown(""" # Image Anonymiser """)
            self.modelui.make_image_ui()
            self.modelui.make_model_ui()
            self.anonymiserui.make_anonymiser_ui()

            # Add Events
            def input_image_changed(image):
                #todo restore defaults for model params and blurring params
                cache["threshold"] = None
                cache["predictions"] = None
                if image is None: # Note: image cleared triggeres a change event and not a clear event
                    cache["input_img"] = None
                    return (gr.Image.update(value = None), gr.Group.update(visible=False), 
                            gr.Accordion.update(open=True), gr.Slider.update(value=self.modelui.default_threshold),
                            gr.Image.update(value = None), gr.Row.update(visible=False))
                else:
                    cache["input_img"] = image
                    return (None, gr.Group.update(visible=True), 
                            gr.Accordion.update(open=True), gr.Slider.update(value=self.modelui.default_threshold),
                            None, gr.Group.update(visible=False))

            self.modelui.input_img.change(input_image_changed, self.modelui.input_img, 
                                    [self.modelui.detect_img, self.modelui.container, self.modelui.accordion, 
                                    self.modelui.threshold, self.anonymiserui.anonymise_image, self.anonymiserui.container])

            def detector(threshold):
                image = cache["input_img"]
                if image is None:
                    return None, gr.Row.update(visible=False)
                else:
                    if cache["threshold"] == threshold:
                        return {self.anonymiserui.container: gr.Group.update(visible=True)} #todo if we can return empty dict
                    else:
                        predictions = self.model.detect(image, threshold)
                        pred_image = self.model.draw_predictions(image, predictions)
                        cache["predictions"] = self.model.process_predictions(predictions)
                        cache["threshold"] = threshold
                        pred_labels = cache["predictions"]["pred_labels"] if cache["predictions"]["pred_labels"] else []
                        blur_type = list()
                        if cache["predictions"]["boxes"] is not None: blur_type.append("Box") 
                        if cache["predictions"]["masks"] is not None: blur_type.append("Mask")
                        if blur_type == []: blur_type.append("None") 
                        return (pred_image, gr.Group.update(visible=True), gr.Accordion.update(open=False),
                                gr.CheckboxGroup.update(choices=pred_labels), 
                                gr.Dropdown.update(choices=blur_type, value=blur_type[0]))

            self.modelui.detect_btn.click(detector, self.modelui.threshold, 
                                        [self.modelui.detect_img, self.anonymiserui.container, self.modelui.accordion, 
                                        self.anonymiserui.target, self.anonymiserui.type])
            # uncomment to have the change in threshold trigger an auto detection
            # self.modelui.threshold.change(detector, self.modelui.threshold, 
            #                             [self.modelui.detect_img, self.anonymiserui.container, self.modelui.accordion, 
            #                             self.anonymiserui.target, self.anonymiserui.type])

            def anonymiser(targets, blur_intensity, blur_type):
                image = np.copy(cache["input_img"])
                if targets != []:
                    target_ids = [self.model.name2int[target] for target in targets]
                    intensity = self.anonymiserui.convert_intensity(blur_intensity)
                    kernel = (intensity, intensity)
                    boxes, mask_indices = self.model.get_class_prediction(target_ids, cache["predictions"])
                    if blur_type == "Box":
                        blur_boxes(image, boxes, kernel=kernel)
                    elif blur_type == "Mask":
                        blur_pixels(image, mask_indices, kernel=kernel)
                    else:
                        pass
                return image

            self.anonymiserui.anonymise_btn.click(anonymiser, [self.anonymiserui.target, self.anonymiserui.intensity, 
                                                self.anonymiserui.type], [self.anonymiserui.anonymise_image],
                                                show_progress=True)
            # Uncomment to have the change in anonymisation params trigger an auto anonymisation
            # Need to take into account latency once model is deployed
            # self.anonymiserui.intensity.change(anonymiser, [self.anonymiserui.target, self.anonymiserui.intensity, 
            #                                     self.anonymiserui.type], [self.anonymiserui.anonymise_image],
            #                                     show_progress=False)
            # self.anonymiserui.target.change(anonymiser, [self.anonymiserui.target, self.anonymiserui.intensity, 
            #                                     self.anonymiserui.type], [self.anonymiserui.anonymise_image],
            #                                     show_progress=False)
            # self.anonymiserui.type.change(anonymiser, [self.anonymiserui.target, self.anonymiserui.intensity, 
            #                                     self.anonymiserui.type], [self.anonymiserui.anonymise_image],
            #                                     show_progress=False)

def main(args):
    app = App()
    app.make_ui()
    app.demo.launch(server_name = args.server, server_port= args.port, share=args.share, debug=args.debug, show_api=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--detectorurl", 
                        default=None, 
                        type=str, 
                        help=f"URL for the lambda funtion running the detection algo. Default (None) uses a local model")
    parser.add_argument("--anonymiserurl", 
                        default=None, 
                        type=str, 
                        help=f"URL for the lambda funtion running the anonymisation algo. Default (None) uses a local model")
    parser.add_argument("--port", 
                        default=DEFAULT_PORT, 
                        type=int, 
                        help=f"Port for the gradio server. Default is {DEFAULT_PORT}")
    parser.add_argument("--server", 
                        default=None, 
                        type=str, 
                        help=f"Server name, to make app accessible on local network, set this to 0.0.0.0. Default is None")
    parser.add_argument("--share", 
                        default=False, 
                        type=bool, 
                        help=f"If True creates a 72h shareable link on gradio domain. Default is False")
    parser.add_argument("--debug", 
                        default=False, 
                        type=bool, 
                        help=f"Used for gradio debug mode. Default is False")
    args = parser.parse_args()
    main(args)
