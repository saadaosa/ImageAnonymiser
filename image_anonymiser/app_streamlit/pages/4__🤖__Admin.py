import argparse
import os
import sys
from functools import partial

import streamlit as st

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
    return DetectorBackend(config_name), FileIO(config_name)


# Initialise Backend
detector, file_io = init_backend(sys.argv[1:])
# Read password from env variable
PASSWORD = os.environ.get("STPASS")


def check_password():
    """ Password Checking: Render the password input page, check user password and provide feedback.
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
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True


def checkbox_img_flagged(dir_name, column):
    """ Load the image and the corresponding predictions that were saved
        Display the image
        ##todo enhance the visualisation to highlight which boxes were provided by the user
    """
    image, predictions, additional_info = file_io.load_image_with_predictions(dir_name)
    with column:
        st.markdown(f"**Detected by** {additional_info['used_model']} **on** {additional_info['detect_date']}")
        image_vis = detector.visualise_boxes(image, predictions, True)
        st.image(image_vis)


# Create the components of the app
try:
    st.set_page_config(layout="wide", page_title="Image Anonymiser - Admin", page_icon="🤖")
    st.markdown("## 🤖 Image Anonymiser - Admin")
    if not check_password():
        pass
    else:
        tab_flagged, tab_feedback = st.tabs(["Flagged Images", "User Feedback"])
        # tab to display images flagged by the users
        with tab_flagged:
            flagged_images = file_io.list_flagged_directory()
            c1, c2 = st.columns([3, 5])
            for fi in flagged_images:
                checkbox_checked = c1.checkbox(label=fi.name, value=False)
                if checkbox_checked: checkbox_img_flagged(fi, c2)

        # tab to display user feedbacks
        with tab_feedback:
            st.dataframe(file_io.get_feedback().iloc[:100])

except Exception as e:
    st.error(f"Something went wrong. Please refresh and try again.")
    file_io.store_exception(e)
