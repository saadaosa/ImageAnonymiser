import base64
import io
import os

import numpy as np
from fastapi import FastAPI, HTTPException
from PIL import Image
from pydantic import BaseModel

from image_anonymiser.backend.fastapi.apidetector import DetectorBackend

app = FastAPI()
detector = None

class DetectionData(BaseModel):
    image_str: str
    model_index: int

@app.on_event("startup")
def load_model():
    global detector
    config = os.environ.get("FASTAPICONFIG")
    detector = DetectorBackend(config=config)

@app.get("/")
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
