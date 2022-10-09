from functools import partial

import streamlit as st

from image_anonymiser.app_streamlit.components.constants import CONFIG
from image_anonymiser.backend.detector import DetectorBackend
from image_anonymiser.backend.file_io import FileIO

st.set_page_config(
    layout="wide",
    page_title="Image Anonymiser - Admin",
    page_icon="🤖"
)

st.markdown("## 🤖 Image Anonymiser - Admin")

PASSWORD = "password"  # TODO: Figure out streamlit secrets


class Admin():
    """ Admin application Component

    Creates a page which enables developers to track user feedback.
    """

    def __init__(self):
        self._detector = self._get_detector()
        self._file_io = self._get_file_io()

    @st.cache
    def _get_detector(self) -> DetectorBackend:
        return DetectorBackend(CONFIG)

    @st.cache
    def _get_file_io(self) -> FileIO:
        return FileIO(CONFIG)

    def _check_password(self):
        """ Password Checking

        Render the password input page, check user password and provide feedback.

        Returns: True once a correct password has been supplied.

        """

        def password_entered():
            """Checks whether a password entered by the user is correct."""
            if st.session_state["password"] == PASSWORD:
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # don't store password
            else:
                st.session_state["password_correct"] = False

        if "password_correct" not in st.session_state:
            # First run, show input for password.
            st.text_input(
                "Password", type="password", on_change=password_entered, key="password"
            )
            return False
        elif not st.session_state["password_correct"]:
            # Password not correct, show input + error.
            st.text_input(
                "Password", type="password", on_change=password_entered, key="password"
            )
            st.error("😕 Password incorrect")
            return False
        else:
            # Password correct.
            return True

    def _on_user_feedback_button(self, file_name: str, column) -> None:
        """
        Render User Feedback

        Args:
            file_name: File with stored feedback
            column: Column where the feedback will be rendered
        """

        feedback = self._file_io.get_feedback(file_name)
        with column:
            st.text(feedback)

    def _user_feedback_tab(self) -> None:
        """
        Renders user Feedback Tab
        Creates 3 columns, one with file names, one with "show" buttons
        Third is empty (and wider) for the feedback showing.
        """

        user_feedbacks = self._file_io.list_feedback_directory()

        c = st.columns([2, 1, 5])

        for ufb in user_feedbacks:
            c[0].text(ufb.name)
            c[1].button(key=ufb, label="Show", on_click=partial(self._on_user_feedback_button, file_name=ufb, column=c[2]))

    def _on_flagged_button(self, dir_name: str, column) -> None:
        """
        Render Flagged Image

        Args:
            dir_name: Folder with stored flagged image and predictions
            column: Column where the feedback will be rendered
        """

        image, predictions = self._file_io.load_image_with_predictions(dir_name)
        with column:
            image_vis = self._detector.visualise_boxes(image, predictions, True)
            st.image(image_vis)

    def _flagged_images_tab(self) -> None:
        """
        Renders Flagged Images tab
        Creates 3 columns, one with file names, one with "show" buttons
        Third is empty (and wider) for the flagged images showing.
        """

        flagged_images = self._file_io.list_flagged_directory()

        c = st.columns([2, 1, 5])

        for fi in flagged_images:
            c[0].text(body=fi.name)
            c[1].button(key=fi, label="Show", on_click=partial(self._on_flagged_button, dir_name=fi, column=c[2]))

    def run(self):
        """ Main Run method of the Class

            Check the admin password
            Then render 2 tabs, one user feedback, one flagged images.

        """
        if not self._check_password(): return

        tab_flagged, tab_feedback = st.tabs(["Flagged Images", "User Feedback"])
        with tab_flagged:
            self._flagged_images_tab()

        with tab_feedback:
            self._user_feedback_tab()


try:
    Admin().run()
except Exception as e:
    st.error("Something went wrong. Please refresh and try again.")
    FileIO(CONFIG).store_exception(e)
