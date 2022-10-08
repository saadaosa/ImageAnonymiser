import streamlit as st


def clear_predictions():
    """
    Clear Model Predictions from the cache

    :return: None
    """

    st.session_state.pop("predictions", None)
    st.session_state.pop("image_boxes", None)


def clear_anon_image():
    """
    Clear anonymized image from the cache

    :return:
    """

    st.session_state.pop("blur_settings", None)
    st.session_state.pop("image_keep", None)
    st.session_state.pop("image_anon", None)
