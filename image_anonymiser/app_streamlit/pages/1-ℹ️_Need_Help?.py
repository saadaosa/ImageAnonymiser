import streamlit as st

from image_anonymiser.app_streamlit.components.constants import USER_GUIDE

st.set_page_config(
    layout="wide",
    page_title="Image Anonymiser - Help",
    page_icon="ℹ️"
)

st.markdown(" ## ℹ️ Image Anonymiser - Help")
st.markdown(USER_GUIDE)
