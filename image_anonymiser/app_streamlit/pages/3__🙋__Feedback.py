import argparse
import sys

import streamlit as st

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
    return FileIO(config_name)

# Initialise Backend
file_io =  init_backend(sys.argv[1:])

def btn_feedback(name, feedback):
    """ Function called to store user feedback
    """
    if feedback is None: return
    file_io.store_feedback(name, feedback)
    st.success("**Thank you 🙏**")

# Create the components of the app
try:
    st.set_page_config(layout="wide", page_title="Image Anonymiser - Feedback", page_icon="🙋")
    st.markdown("## 🙋 Image Anonymiser - Feedback")
    # Feedback form
    with st.form(key="feedback_form", clear_on_submit=True):
        name = st.text_input(label="What should we call you? Feel free to leave blank...", max_chars=20)
        if not name:
            name = "Anonymous"
        feedback = st.text_area(label="Do you want something changed? Improved? Tell us here!", max_chars=500)
        submitted = st.form_submit_button(label="Send")
        if submitted:
            btn_feedback(name, feedback)

except Exception as e:
    st.error("Something went wrong. Please refresh and try again.")
    file_io.store_exception(e)