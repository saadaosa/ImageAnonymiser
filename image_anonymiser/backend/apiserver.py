import base64
import io
import os

import numpy as np
from fastapi import FastAPI
from PIL import Image
from pydantic import BaseModel

from image_anonymiser.backend.detector import DetectorBackend

app = FastAPI()
detector = None

class DetectionData(BaseModel):
    image_str: str
    model_index: int

@app.on_event("startup")
def load_model():
    global detector
    config = os.environ.get("FASTAPICONFIG", "config.yml")
    detector = DetectorBackend(config=config, force_inapp=True)

@app.get("/info")
def get_api_info():
    return {"choices": detector.choices,
            "descriptions": detector.descriptions,
            "classes": detector.classes
            }

@app.post("/detect")
def get_predictions(payload: DetectionData):
    payload = payload.dict()
    image_str = payload["image_str"]
    model_index = payload["model_index"]
    image_decoded = base64.b64decode(image_str)
    image = np.array(Image.open(io.BytesIO(image_decoded)))
    predictions = detector.detect(image, model_index)
    return {"predictions": predictions}