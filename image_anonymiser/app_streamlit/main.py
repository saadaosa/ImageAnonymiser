from functools import partial

import PIL.Image
import numpy as np
import streamlit as st

from image_anonymiser.app_streamlit.components.blurring import Blurring
from image_anonymiser.app_streamlit.components.detection import Detection
from image_anonymiser.app_streamlit.components.utils import clear_anon_image, clear_predictions
from image_anonymiser.backend.anonymiser import AnonymiserBackend
from image_anonymiser.backend.detector import DetectorBackend
from image_anonymiser.backend.file_io import FileIO

CONFIG = "config.yml"

st.set_page_config(layout="wide")


class App():
    """Main application Component.

    Takes care of the initial file upload and rendering of the sub-components.
    Handles generating Step 1. in the sidebar and left part of the main screen.

    """

    def __init__(self):
        self._detector = DetectorBackend(CONFIG)
        self._anonymiser = AnonymiserBackend(CONFIG)
        self._file_io = FileIO(CONFIG)

    def _on_reupload(self) -> None:
        """ Reupload Image event

        User has changed the initial image.
        Clears predictions and anonymised image from the cache.
        """

        clear_predictions()
        clear_anon_image()

    def _image_uploader(self) -> None:
        """ Image uploader in Sidebar

        Renders the image uploader component
        Converts the image from PIL into numpy array format.
        """

        st.sidebar.markdown("### 1. Upload an Image")
        img_file = st.sidebar.file_uploader(label='Image Upload', type=['png', 'jpg', 'jpeg'], on_change=partial(self._on_reupload))

        if img_file:
            image = PIL.Image.open(img_file)
            st.session_state["image"] = np.array(image)

    def run(self) -> None:
        """ Main Run method of the class

        Renders the full application and its sub-components.

        1. If we don't have an image, just render side uploader.
        2. Once we have an image, render the Detector component.
        3. Once we have predictions, render the Blur component.

        """

        # Image Uploader
        st.markdown(" ## Image Anonymiser 👻 ")
        self._image_uploader()

        k = st.session_state.keys()
        cols = st.columns(2)

        # Detector Component on the LEFT
        if "image" in k:
            with cols[0]:
                Detection(self._detector, self._file_io).run()

        # Blur Component on the RIGHT
        if "predictions" in k:
            with cols[1]:
                Blurring(self._detector, self._anonymiser).run()


try:
    App().run()
except Exception as e:
    st.error("Something went wrong. Please refresh and try again.")
    FileIO(CONFIG).store_exception(e)
