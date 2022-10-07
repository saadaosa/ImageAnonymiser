from functools import partial

import PIL.Image
import numpy as np
import streamlit as st
from streamlit_cropper import st_cropper

from image_anonymiser.backend.anonymiser import AnonymiserBackend
from image_anonymiser.backend.detector import DetectorBackend
from image_anonymiser.backend.file_io import FileIO

CONFIG = "config.yml"

detector = DetectorBackend(CONFIG)
anonymiser = AnonymiserBackend(CONFIG)
file_io = FileIO(CONFIG)


def _clear_predictions():
    st.session_state.pop("predictions", None)
    st.session_state.pop("image_boxes", None)


def _clear_anon_image():
    st.session_state.pop("blur_settings", None)
    st.session_state.pop("image_anon", None)


class BlurSettings():
    def __init__(self):
        self._predictions = st.session_state["predictions"]
        self._blur_type()
        self._checkboxes()
        self._blur_targets()

    def _blur_type(self):
        c = st.sidebar.columns(3)
        self.target_type = c[0].selectbox(label="Target Type", options=detector.get_pred_types(self._predictions))
        self.anonymisation = c[1].selectbox(label="Anonymisation", options=["blur", "color"])

        if self.anonymisation == "color":
            self.color = c[2].color_picker(label="Pick Color")

        if self.anonymisation == "blur":
            self.blur_strength = c[2].slider(label="Blur Strength", min_value=0.0, max_value=1.0, step=0.05, value=0.2)

    def _checkboxes(self):
        self.compound = st.sidebar.checkbox(label="Compound Anonymisation")

    def _blur_targets(self):
        c = st.sidebar.columns(2)
        self.anonym_class = c[0].selectbox("Choose the Class", options=detector.get_pred_classes(self._predictions))
        box_options = detector.get_instance_ids(self.anonym_class, self._predictions, False)  # TODO: Here
        self.anonym_instance = c[1].selectbox("Chose the Instance", options=box_options)


class UserBoxes():
    def __init__(self):
        st.session_state["image_userbox"] = st.session_state["image_boxes"]

    def _on_done_button(self, feedback, store_predictions):
        if store_predictions:
            image = st.session_state["image"]
            predictions = st.session_state["predictions"]
        else:
            image = None
            predictions = None

        file_io.store_image_with_predictions(image, predictions, feedback)

    def _on_add_button(self, box, label):
        _clear_anon_image()

        predictions = st.session_state["predictions"]
        image = st.session_state["image"]

        coords = self._get_bb_coords(box)
        predictions = detector.add_labeled_box(coords, label, predictions)

        st.session_state["predictions"] = predictions
        st.session_state["image_boxes"] = detector.visualise_boxes(image, predictions, False)  # TODO: Here

    def _get_bb_coords(self, box):
        x1 = box["left"]
        y1 = box["top"]

        x2 = box["left"] + box["width"]
        y2 = box["top"] + box["height"]

        return (x1, y1, x2, y2)

    def run(self):
        with st.expander(label="Add Custom Boxes", expanded=False):
            predictions = st.session_state["predictions"]
            image = st.session_state["image_boxes"]

            label = st.selectbox("Class to Add", options=detector.get_pred_classes(predictions))
            box = st_cropper(PIL.Image.fromarray(image), realtime_update=True, return_type="box")

            st.button(label="Add Box", on_click=partial(self._on_add_button, box=box, label=label))

            store_predictions = st.checkbox(label="Allow storing my image for model improvement", value=True)
            feedback = st.text_input(label="Experienced any trouble? Let us know!")

            st.button(label="Send us Feedback", on_click=partial(self._on_done_button, feedback=feedback, store_predictions=store_predictions))


class App():
    def run(self):
        st.markdown(" ## Image Anonymiser 👻 ")

        self._get_uploaded_image()
        self._get_predictions()
        self._get_blur()
        self._visualise()

    def _on_reupload(self):
        _clear_predictions()
        _clear_anon_image()

    def _get_uploaded_image(self):
        st.sidebar.markdown("### 1. Upload an Image")
        img_file = st.sidebar.file_uploader(label='Image Upload', type=['png', 'jpg', 'jpeg'], on_change=partial(self._on_reupload))

        if img_file:
            image = PIL.Image.open(img_file)
            st.session_state["image"] = np.array(image)

    def _on_detect_button(self, model_choice):
        _clear_anon_image()

        image = st.session_state["image"]
        st.session_state["predictions"] = detector.detect(image, model_choice)

        img_to_vis = st.session_state.get("image_keep", st.session_state["image"])
        st.session_state["image_boxes"] = detector.visualise_boxes(img_to_vis, st.session_state["predictions"], False)  # TODO: Here

    def _get_predictions(self):
        if "image" not in st.session_state.keys(): return

        st.sidebar.markdown("### 2. Detect Objects")
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

        st.sidebar.markdown("### 3. Anonymise")
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
            UserBoxes().run()
        else:
            st.image(st.session_state["image_anon"])
            UserBoxes.run()


App().run()
