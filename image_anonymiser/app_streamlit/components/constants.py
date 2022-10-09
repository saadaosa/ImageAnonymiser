CONFIG = "config.yml"

USER_GUIDE = """
- **Input image**: Enter your image by clicking on the `Input Image` frame. To upload a new image, first clear the current
one (by clicking on `x` in the input frame). Note: By clearing the image, your current work will be lost, so save your 
anonymised image first.

- **Chosing the Detection Model**: By selecting the model, the app will automatically run the detection process and update
the `Detection Output` image with the objects identified in the input. The configuration parameters for the anonymisation
will also be updated based on the model output and classes/instances identified. If no object is detected, the 
anonymisation options will not be displayed.

- **Choosing the Anonymisation Parameters**:
    * `Anonymisation type`: Can be `blur` or `color`
    * `Compound Anonymisation` flag: If selected, several anonymisations can be applied to the same image. e.g. using a face
    detector to blur faces and then using a text detector to color text
    * `Target Type`: Can be `box` (for bounding boxes), or `mask` (for segmentation masks). The choices are set automatically
    based on the model outputs. If for instance, there is only `box`, this means that the model doesn't support segmentation
    * `Blur Intensity`: Value from 0 to 100%, `0` meaning no blur and `1` meaning maximum blur. Used if the `Anonymisation Type`
    is `blur`
    * `Color`: Click to choose the color. Used if the `Anonymisation Type` is `color`
    * `Choose the class`: Object classes detected in the image. This is relevant for multi-class models. For models that detect
    only one class, the latter will be selected by default
    * `Choose the instance`: Can be `all` in which case all the class instances will be anonymised or a specific instance id
    within the class (as displayed in the `Detection Output` frame)
"""
