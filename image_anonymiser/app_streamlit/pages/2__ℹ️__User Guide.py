from pathlib import Path

import streamlit as st

PAR_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PAR_DIR / "assets"


# Create the components of the app
st.set_page_config(layout="wide", page_title="Image Anonymiser - Help", page_icon="ℹ️")
st.markdown("## ℹ️ Image Anonymiser - Help")

col = st.columns(2)
with col[0]:
    st.markdown(""" ### Step 1: Choose your input image""")
    st.markdown("""
    - Enter your image by clicking on the **Browse File** button. This will display your image
    - Note: By clearing the image or uploading a new one, your current work will be lost, so save your anonymised image first
    """)
    st.image(str(ASSETS_DIR /"image_upload.png"))

    st.markdown(""" ### Step 3: Add your own annotations""")
    st.markdown("""
    - If the model fails to detect an instance that should have been identified, you can decide to add your own annotations
    and use them to anonymise the image
    - This is accomplished by defining a box around the target and clicking on **Add box**
    - You can decide if you want to share those annotations with us or not. If you are ok, you can press **Send your annotations**
    """)
    st.image(str(ASSETS_DIR /"annotations.png"))

with col[1]:
    st.markdown(""" ### Step 2: Choose the detection model""")
    st.markdown("""
    Select the model from the dropdown menu and click on the **Detect** button. If the model detects relevant objects/classes
    in the image, it will display an output with the **bounding boxes** around these object, as well as the anonymisation parameters
    """)
    st.image(str(ASSETS_DIR /"detection.png"))

    st.markdown(""" ### Step 4: Choose the anonymisation params""")
    st.markdown("""
    * `Target Type`: Can be `box` (for bounding boxes), or `mask` (for segmentation masks). The choices are set automatically
    based on the model outputs. If for instance, there is only `box`, this means that the model doesn't support segmentation
    * `Anonymisation`: Can be `blur` or `color`
    * `Compound Anonymisation` flag: If selected, several anonymisations can be applied to the same image. e.g. using a face
    detector to blur faces and then using a text detector to color text
    * `Blur Strength`: Value from 0 to 100%, `0` meaning no blur and `1` meaning maximum blur. Used if the `Anonymisation`
    is `blur`
    * `Color`: Click to choose the color. Used if the `Anonymisation` is `color`
    * `Choose the class`: Object classes detected in the image. This is relevant for multi-class models. For models that detect
    only one class, the latter will be selected by default
    * `Choose the instance`: Can be `all` in which case all the class instances will be anonymised or a specific instance id
    within the class
    """)
    st.image(str(ASSETS_DIR /"anonymisation.png"))