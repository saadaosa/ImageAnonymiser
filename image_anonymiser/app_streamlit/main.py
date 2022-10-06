from functools import partial

import PIL.Image
import numpy as np
import streamlit as st

from image_anonymiser.backend.anonymiser import AnonymiserBackend
from image_anonymiser.backend.detector import DetectorBackend
from image_anonymiser.backend.file_io import FileIO

CONFIG = "config.yml"

detector = DetectorBackend(CONFIG)
anonymiser = AnonymiserBackend(CONFIG)
file_io = FileIO(CONFIG)


class BlurSettings():
    def __init__(self):
        self._predictions = st.session_state["predictions"]
        self._blur_type()
        self._checkboxes()
        self._blur_targets()

    def _blur_strength(self):
        if self.anonymisation != "blur": return
        self.blur_strength = st.sidebar.slider(label="Chose Blur Strength", min_value=0.0, max_value=1.0, step=0.05, value=0.2)

    def _color(self):
        if self.anonymisation != "color": return
        self.color = st.sidebar.color_picker(label="Chose Anonymisation Color")

    def _blur_type(self):
        self.anonymisation = st.sidebar.selectbox(label="Select Anonymisation Type", options=["blur", "color"])
        self._blur_strength()
        self._color()
        self.target_type = st.sidebar.selectbox(label="Select Target Type", options=detector.get_pred_types(self._predictions))

    def _on_user_boxes_checked(self):
        if "image" not in st.session_state: return

        img_to_vis = st.session_state.get("image_keep", st.session_state["image"])
        st.session_state["image_boxes"] = detector.visualise_boxes(
            img_to_vis,
            st.session_state["predictions"],
            ~self.include_user_boxes
        )

    def _checkboxes(self):
        self.compound = st.sidebar.checkbox(label="Compound Anonymisation")
        self.include_user_boxes = st.sidebar.checkbox("Include User Boxes", value=False, on_change=partial(self._on_user_boxes_checked))

    def _blur_targets(self):
        c = st.sidebar.columns(2)
        self.anonym_class = c[0].selectbox("Choose the Class", options=detector.get_pred_classes(self._predictions))
        box_options = detector.get_instance_ids(self.anonym_class, self._predictions, self.include_user_boxes)
        self.anonym_instance = c[1].selectbox("Chose the Instance", options=box_options)


class App():
    def run(self):
        st.markdown(" ## Image Anonymiser 👻 ")

        self._get_uploaded_image()
        self._get_predictions()
        self._get_blur()
        self._visualise()

    def _on_reupload(self):
        st.session_state.clear()

    def _get_uploaded_image(self):
        st.sidebar.markdown("**Step 1**: Upload an image")
        img_file = st.sidebar.file_uploader(label='Image Upload', type=['png', 'jpg', 'jpeg'], on_change=partial(self._on_reupload))

        if img_file:
            image = PIL.Image.open(img_file)
            st.session_state["image"] = np.array(image)

    def _on_detect_button(self, model_choice):
        image = st.session_state["image"]
        st.session_state["predictions"] = detector.detect(image, model_choice)

        img_to_vis = st.session_state.get("image_keep", st.session_state["image"])
        st.session_state["image_boxes"] = detector.visualise_boxes(img_to_vis, st.session_state["predictions"])

        st.session_state.pop("blur_settings", None)
        st.session_state.pop("image_anon", None)

    def _get_predictions(self):
        if "image" not in st.session_state.keys(): return

        st.sidebar.markdown("**Step 2**: Choose the detection model")
        model_choice = st.sidebar.selectbox(label="Detection Model", options=detector.choices)
        model_choice = detector.choices.index(model_choice)
        st.sidebar.button(label="Detect", on_click=partial(self._on_detect_button, model_choice=model_choice))

    def _on_blur_button(self, blur_settings):
        if blur_settings.compound:
            image = st.session_state.get("image_keep", st.session_state["image"])
        else:
            image = st.session_state["image"]

        predictions = st.session_state["predictions"]
        target_regions = detector.get_target_regions(
            class_name=blur_settings.anonym_class,
            instance_id=blur_settings.anonym_instance,
            target_type=blur_settings.target_type,
            predictions=predictions,
            incl_user_boxes=blur_settings.include_user_boxes
        )

        if blur_settings.anonymisation == "blur":
            intensity = anonymiser.convert_intensity(blur_settings.blur_strength)
            st.session_state["image_anon"] = anonymiser.anonymise(
                image=image,
                targets=target_regions,
                anonym_type="blur",
                blur_kernel=(intensity, intensity)
            )

        if blur_settings.anonymisation == "color":
            color = anonymiser.convert_color_hex_to_rgb(blur_settings.color)
            st.session_state["image_anon"] = anonymiser.anonymise(
                image=image,
                targets=target_regions,
                anonym_type="color",
                color=color
            )

        if blur_settings.compound:
            st.session_state["image_keep"] = st.session_state["image_anon"]
        else:
            st.session_state.pop("image_keep", None)

    def _get_blur(self):
        if "predictions" not in st.session_state.keys(): return

        st.sidebar.markdown("**Step 3**: Change the anonymisation parameters")
        blur_settings = BlurSettings()

        st.sidebar.button(label="Anonymise", on_click=partial(self._on_blur_button, blur_settings=blur_settings))

    def _visualise(self):
        k = st.session_state.keys()

        if "image" not in k:
            return

        elif "image_boxes" not in k:
            st.image(st.session_state["image"])

        elif "image_anon" not in k:
            st.image(st.session_state["image_boxes"])

        else:
            st.image(st.session_state["image_anon"])


App().run()
