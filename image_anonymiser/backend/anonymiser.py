from pathlib import Path

import cv2
import numpy as np
import yaml

PAR_DIR = Path(__file__).resolve().parent 
CONFIG_DIR = PAR_DIR / "configs"

class AnonymiserBackend():
    """ Interface to a backend that returns an anonymised image
    """

    def __init__(self, config):
        config_file = CONFIG_DIR / config
        with open(config_file, 'r') as file:
            self.config = yaml.safe_load(file)
        anonymiser = Anonymiser()
        self.anonymise = anonymiser.anonymise
        self.max_blur_intensity = self.config["anonymiser"]["max_blur_intensity"]
        self.min_blur_intensity = self.config["anonymiser"]["min_blur_intensity"]

    def convert_intensity(self, intensity):
        """ Converts a blur intensity from percentage to a kernel value used by the anonymise function
        """
        result = int(intensity * (self.max_blur_intensity - self.min_blur_intensity + 1))
        if result % 2 == 0: result+=1 
        return result

    def convert_color_hex_to_rgb(self, color_hex):
        """ Converts a color code in hex to rgb format
        """
        code = color_hex.lstrip("#")
        result = list(int(code[i:i+2], 16) for i in [0, 2, 4])
        return result 

class Anonymiser():
    """ Perform anonymisation locally
    """
    def __init__(self):
        pass

    def anonymise(self, image, targets, anonym_type="blur", blur_kernel=(7,7), color=[0,255,255]):
        """ Method used to perform anonymisation

        Params:
            image: numpy array, input image
            targets: tuple(list[int], list[int]), coordinates of the pixels to anonymise
            anonym_type: str, can be "blur" or "color"
            blur_kernel: int, kernel size to be used by cv2.GaussianBlur
            color: list[int], color in [R,G,B] format
        
        Returns:
            output: numpy array, image anonymised
        """
        output = np.copy(image)
        if anonym_type =="blur":
            blur = cv2.GaussianBlur(output, blur_kernel, 0)
            output[targets] = blur[targets]
        elif anonym_type =="color":
            output[targets] = color 
        else:
            raise ValueError(f"anonymisation type: {anonym_type} not supported; use `blur` or `color`")
        return output

