import argparse
import sys
from functools import partial

import numpy as np
import PIL.Image
import streamlit as st
from streamlit_cropper import st_cropper

from image_anonymiser.backend.anonymiser import AnonymiserBackend
from image_anonymiser.backend.detector import DetectorBackend
from image_anonymiser.backend.file_io import FileIO


@st.experimental_singleton(show_spinner=False)
def init_backend(args):
    ''' Retrieves the arguments passed to the stript and returns the backend objects
        This function is called only once
    '''
    def parse_args(args):
        parser = argparse.ArgumentParser()
        parser.add_argument("--bconfig", 
                        default="config.yml", 
                        type=str, 
                        help=f"Name of the backend config file")
        parsed_args = parser.parse_args()
            
        return parsed_args
    parsed_args = parse_args(args)
    config_name = parsed_args.bconfig
    return DetectorBackend(config_name), AnonymiserBackend(config_name), FileIO(config_name)

# Initialise Backend
detector, anonymiser, file_io =  init_backend(sys.argv[1:])

# Functions called when the user interacts with specific streamlit components
def input_image_changed():
    ''' Function called when a new image is uploaded or the current one is removed
        It saves the new image as a numpy array in the session state (or clears the state if the image is removed)
        It clears the session state for predictions, model_index, pred_image and anonym_image and clears the cache 
    '''
    if st.session_state["image_uploader"] is not None:
        st.session_state["input_image"] = np.array(PIL.Image.open(st.session_state["image_uploader"]))
    else:
        clear_session_state(["input_image"])
    clear_session_state(["predictions", "model_index", "pred_image", "anonym_image"])
    #get_predictions.clear()
    #get_pred_image.clear()

def btn_detect(image, model_index):
    ''' Function called when the user clicks on the detect button
        It calls the detect backend fct and updates the session state for predictions, model_index and anonym_image
    '''
    if in_session_state("model_index") and st.session_state["model_index"] == model_index:
        # Do nothing as the predictions for this model/image are already in session_state
        pass
    else:
        # Call the backend to get the predictions
        predictions = detector.detect(image, model_index)
        st.session_state["predictions"] = predictions ##todo: store by model_index?
        st.session_state["model_index"] = model_index
        st.session_state["pred_image"] = detector.visualise_boxes(image, predictions, True)
    # Clear the anonym_image if no compounding
    if "compound" in st.session_state and st.session_state["compound"] is False:
        if "anonym_image" in st.session_state:
            clear_session_state(["anonym_image"])

def btn_add_user_box(image, box, label, predictions):
    """ Function called to add the annotations from the user
        It calls the backend to update the predictions and store them in session_state 
        since the predictions are updated, it refreshes pred_image
    """
    x1 = box["left"]
    y1 = box["top"]
    x2 = box["left"] + box["width"]
    y2 = box["top"] + box["height"]
    coords = [x1, y1, x2, y2]
    predictions = detector.add_labeled_box(coords, label, predictions)
    st.session_state["predictions"] = predictions
    st.session_state["pred_image"] = detector.visualise_boxes(image, predictions, True)

def btn_annotations(image, predictions, allow_save):
    """ Send the input image and the predictions (including the user annotations) to the backend
    """
    if allow_save:
        file_io.store_image_with_predictions(image, predictions)
        with st.columns(3)[0]:
            st.success("**Thank you 🙏**") ## todo: change location where this is displayed?

def btn_anonymise(image, predictions, anonym_type, compound, target_type, blur_strength, color, 
                anonym_class, anonym_instance):
    ''' Function called when the user clicks on the anonymise button
        If the compound parameter is True, it loads the previous anonym_image (if it exists) from session_state
        It then calls the anonymise function
        ##todo Change anonymise to do conversions in the backend 
    '''
    if compound and "anonym_image" in st.session_state:
        input_img = st.session_state["anonym_image"]
    else:
        input_img = image
    target_regions = detector.get_target_regions(anonym_class, anonym_instance, target_type, predictions, True)
    if anonym_type == "blur":
        strength = anonymiser.convert_intensity(blur_strength)
        kernel = (strength, strength)
        anonym_img = anonymiser.anonymise(input_img, target_regions, anonym_type=anonym_type, blur_kernel=kernel)
    elif anonym_type == "color":
        anonym_color = anonymiser.convert_color_hex_to_rgb(color)
        anonym_img = anonymiser.anonymise(input_img, target_regions, anonym_type=anonym_type, color=anonym_color)
    st.session_state["anonym_image"] = anonym_img  

# Functions originally used as a wrapper around the backend calls in order to cache the results
# Not used due to performance issues when reading from cache
# @st.experimental_memo(show_spinner=False, ttl=120)
# def get_predictions(image, model_index):
#     ''' Function call to the detect method in the detector backend
#         The result is cached  
#     '''
#     return detector.detect(image, model_index)
# @st.experimental_memo(show_spinner=False, ttl=120)
# def get_pred_image(_detector, image, predictions, incl_user_boxes):
#     ''' Function call to the visualise_boxes method in the detector backend
#         The result is cached  
#     '''
#     return detector.visualise_boxes(image, predictions, incl_user_boxes)

# Functions used to create certain components of the app and define their call backs
def crearte_detect_params():
    ''' Creates the selectbox to choose the model and the detect button
    '''
    st.sidebar.markdown("### 2. Choose detection model")
    model_choice = st.sidebar.selectbox(label="Detection Model", options=detector.choices, 
                    label_visibility="collapsed")
    model_index = detector.choices.index(model_choice)
    st.sidebar.button(label="Detect", on_click=partial(btn_detect, image=image, model_index=model_index))

def create_output(image, predictions, pred_types, pred_classes, col1, col2):
    ''' Contains the logic of the components created if there are predictions in session_state
        It visualises the boxes detected in the image (if any)
        It creates the input parameters for the anonymisation in the sidebar
        It displays the anonymised image (if it has been saved in the session state) 
    '''
    with col1:
        img_display = image
        if pred_types == []: # A prediction has been done but the result is empty (display the input image)
            st.markdown("### No object detected")
        else:
            if in_session_state("pred_image"): # this check shouldn't be needed
                model_choice = detector.choices[st.session_state["model_index"]]
                st.markdown(f"### Detection output: {model_choice}")
                pred_image = st.session_state["pred_image"]
                img_display = pred_image
        st.image(img_display)
        create_user_boxes(image, predictions)
    if pred_types != []:
        create_anonym_params(image, predictions, pred_classes, pred_types)
        if "anonym_image" in st.session_state:
            with col2:
                st.markdown("### Image Anonymised")
                st.image(st.session_state["anonym_image"])

def create_user_boxes(image, predictions):
    """ Add the component for the user to draw and save any objects missed
    """
    with st.expander(label="Did we miss something?", expanded=False):
        image_pil = PIL.Image.fromarray(image)
        model_index = st.session_state["model_index"]
        class_names = detector.classes[model_index] #
        label = st.selectbox("Class to Add", options=class_names)
        box = st_cropper(image_pil, realtime_update=True, return_type="box")
        st.button(label="Add Box", on_click=partial(btn_add_user_box, image, box, label, predictions))
        store_annotations = st.checkbox(label="Allow storing my image for model improvement", value=True)
        if store_annotations:
            st.button(label="Send your annotations", on_click=partial(btn_annotations, image, predictions, 
                                            store_annotations))

def create_anonym_params(image, predictions, pred_classes, pred_types):
    ''' Creates the anonymisation input parameters
    '''
    c1 = st.sidebar.columns(3)
    target_type = c1[0].selectbox(label="Target Type", options=pred_types)
    anonym_type = c1[1].selectbox(label="Anonymisation", options=["blur", "color"])
    if anonym_type == "color": 
        blur_strength = None
        color = c1[2].color_picker(label="Pick Color")
    if anonym_type == "blur":
        color = None
        blur_strength = c1[2].slider(label="Blur Strength", min_value=0.0, max_value=1.0, step=0.05, value=0.2)
    compound = st.sidebar.checkbox(label="Compound Anonymisation", key="compound")
    c2 = st.sidebar.columns(2)
    anonym_class = c2[0].selectbox("Choose the Class", options=pred_classes)
    instance_ids = detector.get_instance_ids(anonym_class, predictions, True)
    anonym_instance = c2[1].selectbox("Chose the Instance", options=instance_ids)
    st.sidebar.button(label="Anonymise", on_click=partial(btn_anonymise, image, predictions, anonym_type, compound,
                        target_type, blur_strength, color, anonym_class, anonym_instance))

# Utilities
def clear_session_state(keys):
    for key in keys:
        if key in st.session_state: del st.session_state[key]

def in_session_state(key, index=None):
    if index is None:
        return key in st.session_state
    else:
        return key in st.session_state and index in st.session_state[key]

# Create the components for the App
try:
    # Set page config
    st.set_page_config(layout="wide", page_title="Image Anonymiser - Home", page_icon="👻")

    # Image uploader
    st.sidebar.markdown("### 1. Upload an Image")
    image_uploader = st.sidebar.file_uploader(label='Image Upload', type=['png', 'jpg', 'jpeg'], 
                on_change=input_image_changed, key="image_uploader", label_visibility="collapsed")

    st.markdown(" ## 👻 Image Anonymiser")
    if "input_image" in st.session_state: # The user has uploaded an image
        # Load input image from cache
        image = st.session_state["input_image"]
        # Display detection params
        crearte_detect_params()
        col1, col2 = st.columns(2) # Split the screen in two parts for the display
        if "predictions" in st.session_state: # A detection model has already been used
            predictions = st.session_state["predictions"]
            pred_types = detector.get_pred_types(predictions, True)
            pred_classes = detector.get_pred_classes(predictions, True)
        # Display output (both detection and anonymisation) 
            create_output(image, predictions, pred_types, pred_classes, col1, col2)
        else: # No model used yet so display the input image
            with col1:
                st.markdown("### Input image")    
                st.image(image)

except Exception as e:
    st.error(f"Something went wrong. Please refresh and try again.")
    file_io.store_exception(e)
