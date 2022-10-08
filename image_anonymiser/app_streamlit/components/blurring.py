from functools import partial

import streamlit as st

from image_anonymiser.backend.anonymiser import AnonymiserBackend
from image_anonymiser.backend.detector import DetectorBackend


class Blurring():
    """
    Component responsible for blurring of the image.
    Handles generating Step 3. in the sidebar and right part of the main screen.
    """


    def __init__(self, detector: DetectorBackend, anonymiser: AnonymiserBackend) -> None:
        self._predictions = st.session_state["predictions"]

        self._detector = detector
        self._anonymiser = anonymiser

    def _blur_type(self) -> None:
        """ User Choice of the blur and its paramaters

        Creates a 3-column wide selection with
        - Target type (boxes/segmentation)
        - Anonymisation type (blur/color)
        - Blur strength / Color Picker
        """

        c = st.sidebar.columns(3)
        self.target_type = c[0].selectbox(label="Target Type", options=self._detector.get_pred_types(self._predictions))
        self.anonymisation = c[1].selectbox(label="Anonymisation", options=["blur", "color"])

        if self.anonymisation == "color":
            self.color = c[2].color_picker(label="Pick Color")

        if self.anonymisation == "blur":
            self.blur_strength = c[2].slider(label="Blur Strength", min_value=0.0, max_value=1.0, step=0.05, value=0.2)

    def _checkboxes(self) -> None:
        """
        Generates checkboxes in the blur settings. Possible to add more switches.
        """

        self.compound = st.sidebar.checkbox(label="Compound Anonymisation")

    def _blur_targets(self) -> None:
        """ User Choice of the blur targets

        Creates a 2-column wide selection with

        - Which class to blur
        - Which instances within that class to blur
        """

        c = st.sidebar.columns(2)
        self.anonym_class = c[0].selectbox("Choose the Class", options=self._detector.get_pred_classes(self._predictions))
        box_options = self._detector.get_instance_ids(self.anonym_class, self._predictions, True)
        self.anonym_instance = c[1].selectbox("Chose the Instance", options=box_options)

    def _on_blur_button(self) -> None:
        """ Blur on Button Press event

        When called,  gather the settings of the blur and run anonymizer.
        Store the anonymised image in the session state for visualisation.
        If compound anonymisation is enabled, we operate with "image_keep",
         where we store the results of the anonymisation.

        """

        if self.compound:
            image = st.session_state.get("image_keep", st.session_state["image"])
        else:
            image = st.session_state["image"]

        predictions = st.session_state["predictions"]
        target_regions = self._detector.get_target_regions(
            class_name=self.anonym_class,
            instance_id=self.anonym_instance,
            target_type=self.target_type,
            predictions=predictions,
            incl_user_boxes=True
        )

        if self.anonymisation == "blur":
            intensity = self._anonymiser.convert_intensity(self.blur_strength)
            st.session_state["image_anon"] = self._anonymiser.anonymise(
                image=image,
                targets=target_regions,
                anonym_type="blur",
                blur_kernel=(intensity, intensity)
            )

        if self.anonymisation == "color":
            color = self._anonymiser.convert_color_hex_to_rgb(self.color)
            st.session_state["image_anon"] = self._anonymiser.anonymise(
                image=image,
                targets=target_regions,
                anonym_type="color",
                color=color
            )


        # Handling of the compound image - we store it in the "image_keep"
        if self.compound:
            st.session_state["image_keep"] = st.session_state["image_anon"]
        else:
            st.session_state.pop("image_keep", None)

    def _get_blur(self) -> None:
        """ Main Blur Settings in Sidebar

        Method to render all blur settings in the sidebar.
        """

        if "predictions" not in st.session_state.keys(): return

        st.sidebar.markdown("### 3. Anonymise")

        self._blur_type()
        self._checkboxes()
        self._blur_targets()

        st.sidebar.button(label="Anonymise", on_click=partial(self._on_blur_button))

    def run(self) -> None:
        """ Main Run method.

        Renders the sidebar options.

        Once anonymisation is done, renders the image.
        """

        self._get_blur()

        if "image_anon" in st.session_state.keys():
            st.markdown("### Anonymised Image:")
            st.image(st.session_state["image_anon"])
