import streamlit as st

from image_anonymiser.app_streamlit.components.constants import CONFIG
from image_anonymiser.backend.file_io import FileIO

st.set_page_config(
    page_title="Image Anonymiser - Feedback",
    page_icon="🙋"
)

st.markdown(" ## 🙋 Image Anonymiser - Send us Feedback!")


class Feedback():
    """ Feedback application Component

    Creates a page which enables users to input feedback.
    """

    def __init__(self):
        self._file_io = FileIO(CONFIG)

    def _on_feedback_button(self, name: str, feedback: str) -> None:
        """ Send us Feedback on Button Press event


        Args:
            name: Username of the user. Replaced by anonymous if empty.
            feedback: Feedback from the user. Won't save feedback if empty
        """

        if name is None: return
        if feedback is None: return

        self._file_io.store_feedback(name, feedback)
        st.success("**Thank you <3**")

    def run(self):
        """ Main Run method of the Class

        Renders a form with username text input, feedback, and a "send" button.
        """

        with st.form(key="feedback_form", clear_on_submit=True):
            name = st.text_input(label="What should we call you? Feel free to leave blank...", max_chars=20)
            if not name:
                name = "Anonymous"

            feedback = st.text_area(label="Do you want something changed? Improved? Tell us here!", max_chars=500)
            submitted = st.form_submit_button(label="Send")
            if submitted:
                self._on_feedback_button(name, feedback)


try:
    Feedback().run()
except Exception as e:
    st.error("Something went wrong. Please refresh and try again.")
    FileIO(CONFIG).store_exception(e)
