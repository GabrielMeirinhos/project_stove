"""
Módulo de inferência standalone — sem dependências de treinamento.
Usa o mesmo pré-processamento do pipeline de treino para garantir consistência.
"""
import json
import time
from pathlib import Path

import cv2
import numpy as np

IMG_SIZE = (128, 128)


class Preprocessor:
    def __init__(self, img_size: tuple[int, int] = IMG_SIZE):
        self.img_size = img_size
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def process_bytes(self, image_bytes: bytes) -> np.ndarray | None:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.bilateralFilter(img, d=5, sigmaColor=75, sigmaSpace=75)
        img = self._apply_clahe(img)
        img = self._resize_with_padding(img)
        return img.astype(np.float32) / 255.0

    def _apply_clahe(self, img: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        l = self.clahe.apply(l)
        return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2RGB)

    def _resize_with_padding(self, img: np.ndarray) -> np.ndarray:
        th, tw = self.img_size
        h, w = img.shape[:2]
        scale = min(tw / w, th / h)
        nw, nh = int(w * scale), int(h * scale)
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((th, tw, 3), dtype=np.uint8)
        y0, x0 = (th - nh) // 2, (tw - nw) // 2
        canvas[y0:y0 + nh, x0:x0 + nw] = resized
        return canvas


def _load_interpreter(model_path: str):
    """Carrega o intérprete TFLite — suporta ai-edge-litert e tensorflow."""
    try:
        from ai_edge_litert.interpreter import Interpreter
        interp = Interpreter(model_path=model_path)
    except ImportError:
        import tensorflow as tf
        interp = tf.lite.Interpreter(model_path=model_path)
    interp.allocate_tensors()
    return interp


class PlantClassifier:
    """Inferência TFLite. Requer modelo treinado em models/model_int8.tflite."""

    def __init__(self, model_path: str, labels_path: str):
        self.preprocessor = Preprocessor()

        with open(labels_path) as f:
            self.labels = {int(k): v for k, v in json.load(f).items()}

        self.interpreter = _load_interpreter(model_path)
        self.interpreter.allocate_tensors()

        inp = self.interpreter.get_input_details()[0]
        self.in_idx = inp["index"]
        self.in_dtype = inp["dtype"]
        self.out_idx = self.interpreter.get_output_details()[0]["index"]

    def predict_bytes(self, image_bytes: bytes, top_k: int = 3) -> dict:
        img = self.preprocessor.process_bytes(image_bytes)
        if img is None:
            raise ValueError("Imagem inválida ou corrompida")

        t0 = time.perf_counter()

        inp = np.expand_dims(img, axis=0)
        if self.in_dtype == np.uint8:
            inp = (inp * 255).astype(np.uint8)

        self.interpreter.set_tensor(self.in_idx, inp)
        self.interpreter.invoke()

        probs = self.interpreter.get_tensor(self.out_idx)[0].astype(np.float32)
        if self.in_dtype == np.uint8:
            probs /= 255.0

        elapsed_ms = (time.perf_counter() - t0) * 1000
        top_indices = np.argsort(probs)[::-1][:top_k]

        return {
            "top_prediction": {
                "class": self.labels[int(top_indices[0])],
                "confidence": float(probs[top_indices[0]]),
            },
            "top_k": [
                {"class": self.labels[int(i)], "confidence": float(probs[i])}
                for i in top_indices
            ],
            "inference_ms": round(elapsed_ms, 2),
        }
