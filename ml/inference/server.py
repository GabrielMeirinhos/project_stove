"""
Microserviço de inferência ML — FastAPI na porta 8001.

Se o modelo não estiver treinado ainda, retorna uma resposta mock
para que o frontend funcione sem travar.
"""
import base64
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

MODEL_PATH = Path(os.getenv("MODEL_PATH", "models/model_int8.tflite"))
LABELS_PATH = Path(os.getenv("LABELS_PATH", "models/labels.json"))

classifier = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global classifier
    if MODEL_PATH.exists() and LABELS_PATH.exists():
        from inference.classifier import PlantClassifier
        classifier = PlantClassifier(str(MODEL_PATH), str(LABELS_PATH))
        print(f"Modelo carregado: {MODEL_PATH}")
    else:
        print(
            f"Modelo nao encontrado em {MODEL_PATH} — rodando em modo simulado.\n"
            f"Treine o modelo com: python training/pipeline.py"
        )
    yield


app = FastAPI(title="Plant ML Inference", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    image_b64: str  # data URL (data:image/jpeg;base64,...) ou base64 puro


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": classifier is not None}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    b64 = req.image_b64
    if "," in b64:
        b64 = b64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=422, detail="Base64 invalido")

    if classifier is None:
        return {
            "top_prediction": {"class": "Modelo_nao_treinado", "confidence": 0.0},
            "top_k": [{"class": "Modelo_nao_treinado", "confidence": 0.0}],
            "inference_ms": 0.0,
            "mock": True,
        }

    try:
        result = classifier.predict_bytes(image_bytes)
        result["mock"] = False
        return result
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


if __name__ == "__main__":
    uvicorn.run("inference.server:app", host="0.0.0.0", port=8001, reload=False)
