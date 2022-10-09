import typing
from functools import partial

import PIL.Image
import streamlit as st
from streamlit_cropper import st_cropper

from image_anonymiser.app_streamlit.components.utils import clear_anon_image
from image_anonymiser.backend.detector import DetectorBackend
from image_anonymiser.backend.file_io import FileIO


class Detection:
    """
    Component that responsible for detecting of the images.
    Handles generating Step 2. in the sidebar and left part of the main screen.
    Also takes care of adding user-defined boxes.
    """

    def __init__(self, detector: DetectorBackend, file_io: FileIO):
        self._detector = detector
        self._file_io = file_io

    def _on_feedback_button(self, store_predictions: bool) -> None:
        """ Feedback on Button Press event

        Called when user decides to send us feedback with his custom bounding boxes defined.
        Decides, whether we are allowed to store the image and predictions, and proceeds to store it on disk
        for further processing.

        Args:
            store_predictions (bool): switch determining whether the user is OK with us storing his image.
        """

        if store_predictions:
            image = st.session_state["image"]
            predictions = st.session_state["predictions"]
        else:
            image = None
            predictions = None

        self._file_io.store_image_with_predictions(image, predictions)
        with st.columns(3)[0]:
            st.success("**Thank you <3**")

    def _on_add_button(self, box: typing.Dict, label: str) -> None:
        """ Add a Custom Bounding Box on Button Press event

        Called when user clicks on "Add" during adding a custom bounding box.

        Integrates the box coordinates into the model's predictions

        Args:
            box (dict): Dictionary with bounding box coordinates
            label (str): String name of the label class that user is adding
        """

        clear_anon_image()

        predictions = st.session_state["predictions"]
        image = st.session_state["image"]

        coords = self._get_bb_coords(box)
        predictions = self._detector.add_labeled_box(coords, label, predictions)

        st.session_state["predictions"] = predictions
        st.session_state["image_boxes"] = self._detector.visualise_boxes(image, predictions, True)

    def _get_bb_coords(self, box: typing.Dict) -> typing.Tuple[int, int, int, int]:
        """ Convert bounding box dictionary to tuple
        Args:
            box (dict): Bounding box coordinates dictionary
                "left", "top", "width", "height

        Returns:
            Tuple (x1, y1, x2, y2) bounding box coordinates

        """

        x1 = box["left"]
        y1 = box["top"]

        x2 = box["left"] + box["width"]
        y2 = box["top"] + box["height"]

        return (x1, y1, x2, y2)

    def _get_image(self) -> PIL.Image:
        """
        Retrieve image with bounding boxes from the session state

        Returns: PIL Image for visualising

        """

        image = st.session_state["image_boxes"]
        return PIL.Image.fromarray(image)

    def _user_boxes(self) -> None:
        """ Expander with option to add user-defined boxes

        Users can select:
        - which label to add
        - where is the object, via specifying a bounding box

        Furthermore, users can elect to send us Feedback, and optionally allow us to store their image with custom boxes.
        """

        with st.expander(label="Did we miss something?"):
            predictions = st.session_state["predictions"]
            image = self._get_image()

            label = st.selectbox("Class to Add", options=self._detector.get_pred_classes(predictions))
            box = st_cropper(image, realtime_update=True, return_type="box")

            st.button(label="Add Box", on_click=partial(self._on_add_button, box=box, label=label))

            store_predictions = st.checkbox(label="Allow storing my image for model improvement", value=True)
            st.button(label="Send us Feedback", on_click=partial(self._on_feedback_button, store_predictions=store_predictions))

    def _on_detect_button(self, model_choice: int) -> None:
        """ Detect on Button Press event

        User has selected the model. Run detector, and prepare to visualise the results.
        Also store the predictions in the session state for further use.

        Args:
            model_choice (int): Index of the selected model
        """

        clear_anon_image()

        image = st.session_state["image"]
        predictions = self._detector.detect(image, model_choice)

        if len(predictions["boxes"]) == 0:
            st.warning("No objects detected. Please try again.")
            return

        st.session_state["predictions"] = predictions

        img_to_vis = st.session_state.get("image_keep", st.session_state["image"])
        st.session_state["image_boxes"] = self._detector.visualise_boxes(img_to_vis, st.session_state["predictions"], True)

    def _predictions(self) -> None:
        """ Sidebar Predictions Step Options

        Renders the Step 2 in the sidebar, allowing user to select which model to use for detection
        And then click the detect button to launch the model itself.
        """

        if "image" not in st.session_state.keys(): return

        st.sidebar.markdown("### 2. Detect Objects")
        model_choice = st.sidebar.selectbox(label="Detection Model", options=self._detector.choices)
        model_choice = self._detector.choices.index(model_choice)
        st.sidebar.button(label="Detect", on_click=partial(self._on_detect_button, model_choice=model_choice))

    def run(self):
        """ Main Run method of the Class

        Renders the sidebar options for detecting objects.
        Initially, render the uploaded image.

        Once the detection has succeeded, renders the detection results
        and offers user to add his custom boxes / send us feedback.
        """

        self._predictions()

        if "image_boxes" in st.session_state.keys():
            st.markdown("### Detected Objects:")
            st.image(st.session_state["image_boxes"])
            self._user_boxes()

        else:
            st.image(st.session_state["image"])
