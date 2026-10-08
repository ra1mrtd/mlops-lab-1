import os
from io import BytesIO

import mlflow
import mlflow.pyfunc
import torch
from fastapi import FastAPI, File, UploadFile
from PIL import Image
from torchvision import transforms

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MODEL_URI = "models:/food11@champion"

CLASS_NAMES = [
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
]


app = FastAPI(title="Food-11 API")

model = mlflow.pyfunc.load_model(MODEL_URI)


transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()

    image = Image.open(BytesIO(contents)).convert("RGB")
    tensor = transform(image).unsqueeze(0)
    input_array = tensor.numpy()
    outputs = model.predict(input_array)

    outputs = torch.tensor(outputs)

    probabilities = torch.softmax(outputs, dim=1)

    confidence, predicted = probabilities.max(dim=1)

    class_id = predicted.item()

    return {
        "category": CLASS_NAMES[class_id],
        "confidence": float(confidence.item()),
    }