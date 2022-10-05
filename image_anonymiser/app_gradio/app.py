""" Perform object detection/segmnentation on an image and allow the user to perform
    several anonymisation taks based on the object classes/ids identified in the input
"""
import gradio as gr

from image_anonymiser.backend.anonymiser import AnonymiserBackend
from image_anonymiser.backend.detector import DetectorBackend

USER_GUIDE = """
- **Input image**: Enter your image by clicking on the `Input Image` frame. To upload a new image, first clear the current
one (by clicking on `x` in the input frame). Note: By clearing the image, your current work will be lost, so save your 
anonymised image first.

- **Chosing the Detection Model**: By selecting the model, the app will automatically run the detection process and update
the `Detection Output` image with the objects identified in the input. The configuration parameters for the anonymisation
will also be updated based on the model output and classes/instances identified. If no object is detected, the 
anonymisation options will not be displayed.

- **Choosing the Anonymisation Parameters**:
    * `Anonymisation type`: Can be `blur` or `color`
    * `Compound Anonymisation` flag: If selected, several anonymisations can be applied to the same image. e.g. using a face
    detector to blur faces and then using a text detector to color text
    * `Target Type`: Can be `box` (for bounding boxes), or `mask` (for segmentation masks). The choices are set automatically
    based on the model outputs. If for instance, there is only `box`, this means that the model doesn't support segmentation
    * `Blur Intensity`: Value from 0 to 100%, `0` meaning no blur and `1` meaning maximum blur. Used if the `Anonymisation Type`
    is `blur`
    * `Color`: Click to choose the color. Used if the `Anonymisation Type` is `color`
    * `Choose the class`: Object classes detected in the image. This is relevant for multi-class models. For models that detect
    only one class, the latter will be selected by default
    * `Choose the instance`: Can be `all` in which case all the class instances will be anonymised or a specific instance id
    within the class (as displayed in the `Detection Output` frame)
"""

class App():
    def __init__(self):
        self.demo = gr.Blocks(title="Image Anonymiser", css=None)
        self.detector_backend = DetectorBackend()
        self.anonymiser_backend = AnonymiserBackend()
    
    def make_ui(self):
        ''' Creates the components of the Blocks demo and adds the events flow
        '''
        with self.demo:
            self.session_cache = gr.State({})
            self.title = gr.Markdown(""" ## Image Anonymiser 👻 """)

            # create gradio components
            with gr.Tabs():
                ## Main Tab
                with gr.TabItem(label="Anonymiser"):
                    ## Input/customisation row 
                    with gr.Row():
                        with gr.Column(scale=1):
                            instr_step1 = gr.Markdown("""**Step 1**: Upload an image""")
                            self.input_img = gr.Image(label="Input Image")
                        with gr.Column(scale=1):
                            self.model_container = gr.Group(visible=False)
                            with self.model_container:
                                with gr.Row():
                                    instr_step2 = gr.Markdown("""**Step 2**: Choose the detection model""")
                                with gr.Row():
                                    self.model_choice = gr.Dropdown(label="Detection Model", choices=self.detector_backend.choices, 
                                                                    type='index')
                        with gr.Column(scale=2):
                            self.anonym_container = gr.Group(visible=False)
                            with self.anonym_container:
                                with gr.Row():
                                    instr_step3 = gr.Markdown("""**Step 3**: Change the anonymisation parameters 
                                                and click on Anonymise""")
                                with gr.Row():
                                    self.prediction_result = gr.Markdown()
                                self.anonym_config = gr.Group()
                                with self.anonym_config:
                                    with gr.Row():
                                        with gr.Column():
                                            self.anonym_type = gr.Dropdown(label="Anonymisation type", 
                                                choices=["blur", "color"], value="blur")
                                        with gr.Column():
                                            self.anonym_compound = gr.Checkbox(label="Compound Anonymisation")
                                    with gr.Row():
                                        with gr.Column(scale = 1):
                                            self.target_type = gr.Dropdown(label="Target Type")
                                        with gr.Column(scale = 2):
                                            with gr.Row():
                                                self.blur_intensity = gr.Slider(0, 1, step=0.05, value=0.2, 
                                                                label="Blur Intensity")
                                                self.anonym_color = gr.ColorPicker(label="Color")
                                    with gr.Row():
                                        with gr.Column():
                                            with gr.Row():
                                                self.anonym_class = gr.Dropdown(label="Choose the class")
                                                self.anonym_instance = gr.Dropdown(label="Choose the instance")
                                    with gr.Row():
                                        self.anonym_btn = gr.Button("Anonymise")
                    ## Output row 
                    with gr.Row():
                        with gr.Column():
                            self.detect_img = gr.Image(label="Detection Output").style(height=300)
                        with gr.Column():
                            self.anonym_img = gr.Image(label="Anonymisation Output").style(height=300)
                ## Help/User guide Tab
                with gr.TabItem(label="Help"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown(""" ### User guide """)
                            gr.Markdown(USER_GUIDE)
                        with gr.Column():
                            gr.Markdown(""" ### Model cards""")
                            for name,description,classes in zip(self.detector_backend.choices, 
                                        self.detector_backend.descriptions, self.detector_backend.classes):
                                if len(classes) == 1:
                                    gr.Markdown(f"- **{name}**: {description}. Can detect 1 class: {classes[0]}")  
                                else:
                                    gr.Markdown(f"- **{name}**: {description}. Can detect {len(classes)} classes")
                                    with gr.Accordion(label=f"{name}: Open to learn about the classes detected", open=False):
                                        gr.Markdown(f"{', '.join(sorted(classes))}")
            # Add Events
            ## Input Image changed
            def input_image_changed(image, session_cache):
                ''' Function called when the input image is changed. It re-initialises the cache and 
                    updates some components as described below. Note: image cleared triggers a gradio 
                    change event and not a clear event so it is captured here

                Params:
                    image: new input image or None if image is cleared
                    session_cache: cache used in the user session
                
                Returns:
                    Update self.detect_img value to None
                    Update self.anonym_img value to None
                    Update self.anonym_container visibility to False
                    Update self.model_container visibility (False if image is cleared and True otherwise)
                    Update self.model_choice value to None
                '''
                output = dict()
                cache = session_cache
                cache["predictions"] = [None for _ in self.detector_backend.choices]
                cache["anonym_img"] = None
                output[self.detect_img] = gr.Image.update(value = None)
                output[self.anonym_img] = gr.Image.update(value = None)
                output[self.anonym_container] = gr.Group.update(visible=False)
                output[self.model_choice] = gr.Dropdown.update(value=None)
                if image is None: 
                    cache["input_img"] = None
                    output[self.model_container] = gr.Group.update(visible=False)
                else:
                    cache["input_img"] = image
                    output[self.model_container] = gr.Group.update(visible=True)
                output[self.session_cache] = cache
                return output
            self.input_img.change(input_image_changed, [self.input_img, self.session_cache], [self.detect_img, 
                                    self.anonym_img, self.anonym_container, self.model_container, self.model_choice, 
                                    self.session_cache])

            ## New model selected
            def detect(model_index, session_cache):
                ''' Detection function called when the model is changed. It reades the input image from 
                    the cache, calls the self.detector_backend, caches the predictions, and updates 
                    some components as described below 

                Params:
                    model_index: index of the model in self.model_choice
                    session_cache: cache used in the user session
                    
                Returns:
                    Update self.detect_img value to visualize the predictions (if model_index not None)
                    Update self.anonym_container visibility to True (if model_index not None)
                    Update self.prediction_result: if no objects detected, display a message to the user and set visibility
                                to True, otherwise set visibility to False
                    Update self.anonym_config visibility to True if objects are detected and False otherwise
                    Update self.target_type choices based on whether the model supports bounding boxes and segmentation
                    Update self.anonym_class choices based on the classes predicted by the detector
                    
                '''
                output = dict()
                if model_index is not None:
                    cache = session_cache
                    image = cache["input_img"]
                    if cache["predictions"][model_index] is None: 
                        predictions = self.detector_backend.detect(image, model_index)
                        cache["predictions"][model_index] = predictions
                    else:
                        predictions = cache["predictions"][model_index]
                    pred_image = self.detector_backend.visualise_boxes(image, predictions)
                    output[self.detect_img] = pred_image
                    output[self.anonym_container] = gr.Group.update(visible=True)
                    pred_types = self.detector_backend.get_pred_types(predictions)
                    if pred_types == []: # No object detected
                        output[self.prediction_result] = gr.Markdown.update(value="""No object detected""", visible=True)
                        output[self.anonym_config] = gr.Group.update(visible=False)
                    else:
                        output[self.prediction_result] = gr.Markdown.update(visible=False)
                        output[self.anonym_config] = gr.Group.update(visible=True)
                        output[self.target_type] = gr.Dropdown.update(choices=pred_types, value=pred_types[0])
                        pred_classes = self.detector_backend.get_pred_classes(predictions)
                        output[self.anonym_class] = gr.Dropdown.update(choices=pred_classes, value=pred_classes[0])
                    output[self.session_cache] = cache
                else:
                    output[self.detect_img] = gr.Image.update(value=None)
                    output[self.anonym_container] = gr.Group.update(visible=False)
                return output        
            self.model_choice.change(detect, [self.model_choice, self.session_cache], [self.detect_img, 
                                    self.anonym_container, self.prediction_result, self.anonym_config, self.target_type, 
                                    self.anonym_class, self.session_cache])

            ## New output class selected for anonymisation
            def update_instance_ids(class_name, model_index, session_cache):
                """ Update the list of instance ids based on the class name selected

                Params:
                    class_name: Selected by the user (depends on the output of the detection model)
                    model_index: index of the model in self.model_choice
                    session_cache: cache used in the user session
                
                Return:
                    Update self.anonym_instance choices. If there is only one instance, the choice will be "all"
                        otherwise "all" and the ids of the instance within the class

                Note: If we add the user labeling in the gradio app, this function should also take as input the 
                    target_type since labeling is only available for boxes, and use it to set incl_user_boxes.
                    Also add event listener on target_type change
                """
                output = dict()
                cache = session_cache
                instance_ids = self.detector_backend.get_instance_ids(class_name, cache["predictions"][model_index])
                output[self.anonym_instance] = gr.Dropdown.update(choices=instance_ids, value=instance_ids[0])
                return output
            self.anonym_class.change(update_instance_ids, [self.anonym_class, self.model_choice, self.session_cache], 
                                    [self.anonym_instance, self.session_cache])

            ## Anonymisation requested
            def anonymise(anonym_type, anonym_compound, target_type, blur_intensity, anonym_color, 
                        anonym_class, anonym_instance, model_index, session_cache):
                ''' Anonymisation function called when the button is clicked. Performs anonymisation on the input
                    image (cached) or the previsously cached anonymised image (if the anonym_compound is True)

                Params:
                    anonym_type: "blur" or "color"
                    anonym_compound: If True, the anonymisation config is applied to the previous output
                    target_type: "box" or "mask" depending on the detector output
                    blur_intensity: value from 0 to 1 used to control the level of blur
                    anonym_color: color to be used if the anonym_type is "color"
                    anonym_class: object class to be anonymised
                    anonym_instance: specific instance id of an object to be anonymised (if "all", all instances
                                    will be anonymised)
                    model_index: index of the model in self.model_choice
                    session_cache: cache used in the user session
                    
                Returns:
                    Update self.anonym_img to be the anonymised image
                '''
                output = dict()
                cache = session_cache
                if anonym_compound and cache["anonym_img"] is not None:
                    input_img = cache["anonym_img"]
                else:
                    input_img = cache["input_img"]
                predictions = cache["predictions"][model_index]
                target_regions = self.detector_backend.get_target_regions(anonym_class, anonym_instance, target_type, 
                                predictions)
                if anonym_type == "blur":
                    intensity = self.anonymiser_backend.convert_intensity(blur_intensity)
                    kernel = (intensity, intensity)
                    anonym_img = self.anonymiser_backend.anonymise(input_img, target_regions, anonym_type=anonym_type, 
                                                    blur_kernel=kernel)
                elif anonym_type == "color":
                    color = self.anonymiser_backend.convert_color_hex_to_rgb(anonym_color)
                    anonym_img = self.anonymiser_backend.anonymise(input_img, target_regions, anonym_type=anonym_type, 
                                                    color=color)
                cache["anonym_img"] = anonym_img
                output[self.anonym_img] = anonym_img
                output[self.session_cache] = cache
                return output
            self.anonym_btn.click(anonymise, [self.anonym_type, self.anonym_compound, self.target_type, 
                            self.blur_intensity, self.anonym_color, self.anonym_class, self.anonym_instance, 
                            self.model_choice, self.session_cache], [self.anonym_img, self.session_cache])
