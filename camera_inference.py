#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inferência em tempo real de doencas de plantas via webcam.

Uso basico:
    python camera_inference.py

Opcoes:
    python camera_inference.py --camera 1
    python camera_inference.py --model outputs/models/model_final.keras
    python camera_inference.py --threshold 0.6 --top-k 5 --no-roi
    python camera_inference.py --record sessao.avi

Controles durante a sessao:
    Q / ESC  -> Encerrar
    S        -> Salvar frame atual como JPEG
    ESPACO   -> Pausar/Retomar inferencia
    R        -> Ativar/Desativar ROI central

IMPORTANTE: rode com o Python que tem TensorFlow instalado.
    Verifique com: python -c "import tensorflow; print('OK')"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

# Força UTF-8 no stdout/stderr para evitar UnicodeEncodeError no Windows (CP1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ──────────────────────────────────────────────────────────────────────────────
# Caminhos padrão (relativos ao diretório do script, independente do CWD)
# ──────────────────────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent
_MODELS_DIR = _SCRIPT_DIR / "outputs" / "models"
_DEFAULT_TFLITE = _MODELS_DIR / "model_int8.tflite"
_DEFAULT_KERAS  = _MODELS_DIR / "model_final.keras"
_DEFAULT_LABELS = _MODELS_DIR / "labels.json"

# ──────────────────────────────────────────────────────────────────────────────
# Parâmetros de pré-processamento — devem espelhar o pipeline de treino
# ──────────────────────────────────────────────────────────────────────────────
_IMG_SIZE        = (128, 128)
_CLAHE_CLIP      = 2.0
_CLAHE_TILE      = (8, 8)
_BILATERAL_D     = 5
_BILATERAL_SIGMA = 75

# ──────────────────────────────────────────────────────────────────────────────
# Parâmetros de UI
# ──────────────────────────────────────────────────────────────────────────────
_DEFAULT_INFER_EVERY = 3       # inferência a cada N frames
_ROI_RATIO           = 0.65    # fração de min(w, h) para o ROI central
_FPS_WINDOW          = 30      # janela de frames para média do FPS

# Cores em BGR
_C_GREEN   = (0, 210, 0)
_C_YELLOW  = (0, 200, 200)
_C_RED     = (0, 60, 220)
_C_WHITE   = (255, 255, 255)
_C_GRAY    = (150, 150, 150)
_C_CYAN    = (220, 220, 0)
_C_DARK    = (25, 25, 25)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
_log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Estrutura de resultado de inferência
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Prediction:
    class_name:   str
    confidence:   float
    inference_ms: float
    top_k:        list[dict] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        """'Tomato___Early_blight' → 'Tomato: Early Blight'."""
        if "___" in self.class_name:
            plant, condition = self.class_name.split("___", 1)
            return f"{plant}: {condition.replace('_', ' ').title()}"
        return self.class_name.replace("_", " ")

    @property
    def color(self) -> tuple[int, int, int]:
        if self.confidence >= 0.80:
            return _C_GREEN
        if self.confidence >= 0.55:
            return _C_YELLOW
        return _C_RED


# ──────────────────────────────────────────────────────────────────────────────
# Pré-processamento em memória (sem escrita em disco)
# ──────────────────────────────────────────────────────────────────────────────
class Preprocessor:
    """
    Replica o pipeline de treino diretamente sobre arrays BGR,
    eliminando a latência de I/O por arquivo temporário.
    """

    def __init__(self, img_size: tuple[int, int] = _IMG_SIZE) -> None:
        self.img_size = img_size
        self._clahe = cv2.createCLAHE(clipLimit=_CLAHE_CLIP, tileGridSize=_CLAHE_TILE)

    def process(self, bgr: np.ndarray) -> np.ndarray:
        """BGR uint8 → float32 [0, 1] shape (H, W, 3)."""
        img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        img = cv2.bilateralFilter(
            img, d=_BILATERAL_D,
            sigmaColor=_BILATERAL_SIGMA,
            sigmaSpace=_BILATERAL_SIGMA,
        )
        img = self._clahe_rgb(img)
        img = self._resize_pad(img)
        return img.astype(np.float32) / 255.0

    def _clahe_rgb(self, rgb: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        l = self._clahe.apply(l)
        return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2RGB)

    def _resize_pad(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        th, tw = self.img_size
        scale = min(tw / w, th / h)
        nw, nh = int(w * scale), int(h * scale)
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((th, tw, 3), dtype=np.uint8)
        yo, xo = (th - nh) // 2, (tw - nw) // 2
        canvas[yo:yo + nh, xo:xo + nw] = resized
        return canvas


# ──────────────────────────────────────────────────────────────────────────────
# Motor de inferência — suporta Keras e TFLite INT8
# ──────────────────────────────────────────────────────────────────────────────
class InferenceEngine:
    """
    Carrega modelo Keras ou TFLite e executa inferência sobre frames BGR.

    Para modelos TFLite INT8, a dequantização usa os parâmetros reais
    do tensor de saída (scale / zero_point) em vez de uma divisão fixa,
    o que preserva a precisão do softmax mesmo com quantização agressiva.
    """

    def __init__(
        self,
        model_path: Path,
        labels_path: Path,
        use_tflite: bool,
    ) -> None:
        self.use_tflite   = use_tflite
        self.preprocessor = Preprocessor()

        if not labels_path.exists():
            raise FileNotFoundError(f"Labels não encontradas: {labels_path}")

        with labels_path.open() as f:
            self.labels: dict[int, str] = {int(k): v for k, v in json.load(f).items()}

        if use_tflite:
            self._load_tflite(model_path)
        else:
            self._load_keras(model_path)

        self._warmup()

    # ── Carregamento ────────────────────────────────────────────────────────

    def _load_tflite(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Modelo TFLite nao encontrado: {path}")

        interpreter_cls = self._resolve_tflite_interpreter()
        self._interp = interpreter_cls(model_path=str(path))
        self._interp.allocate_tensors()

        in_det  = self._interp.get_input_details()[0]
        out_det = self._interp.get_output_details()[0]

        self._in_idx   = in_det["index"]
        self._out_idx  = out_det["index"]
        self._in_dtype = in_det["dtype"]

        self._in_scale,  self._in_zp  = self._quant_params(in_det)
        self._out_scale, self._out_zp = self._quant_params(out_det)

        _log.info(
            "TFLite carregado | dtype entrada=%s | saída scale=%.6f zp=%d",
            in_det["dtype"].__name__, self._out_scale, self._out_zp,
        )

    @staticmethod
    def _resolve_tflite_interpreter():
        """
        Retorna a classe Interpreter disponivel no ambiente.
        Tenta na ordem: tensorflow.lite -> ai_edge_litert -> erro claro.
        """
        try:
            import tensorflow as tf  # noqa: PLC0415
            return tf.lite.Interpreter
        except ImportError:
            pass

        try:
            from ai_edge_litert.interpreter import Interpreter  # noqa: PLC0415
            return Interpreter
        except ImportError:
            pass

        raise ImportError(
            "Nenhum runtime TFLite encontrado.\n"
            "Instale um dos pacotes abaixo e tente novamente:\n"
            "  pip install tensorflow          (recomendado)\n"
            "  pip install ai-edge-litert      (alternativa leve)\n\n"
            "Se o TF ja esta instalado, verifique se voce esta rodando\n"
            "com o Python correto (fora do venv ou com o venv que tem TF):\n"
            "  python -c \"import tensorflow; print('OK')\""
        )

    def _load_keras(self, path: Path) -> None:
        try:
            from tensorflow import keras  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "TensorFlow/Keras necessário. "
                "Instale com: pip install tensorflow"
            ) from exc

        if not path.exists():
            raise FileNotFoundError(f"Modelo Keras não encontrado: {path}")

        _log.info("Carregando Keras: %s …", path)
        self._model = keras.models.load_model(str(path))
        _log.info("Keras carregado.")

    @staticmethod
    def _quant_params(details: dict) -> tuple[float, int]:
        """Extrai (scale, zero_point) dos detalhes do tensor TFLite."""
        qp = details.get("quantization_parameters", {})
        scales = qp.get("scales", [])
        zps    = qp.get("zero_points", [])
        if len(scales) > 0 and len(zps) > 0:
            return float(scales[0]), int(zps[0])
        # API legada: 'quantization' é uma tupla (scale, zero_point)
        legacy = details.get("quantization", (1.0 / 255.0, 0))
        return float(legacy[0]), int(legacy[1])

    # ── Inferência ──────────────────────────────────────────────────────────

    def predict(self, bgr: np.ndarray, top_k: int = 3) -> Prediction:
        """Recebe um frame BGR uint8 e retorna a predição."""
        img = self.preprocessor.process(bgr)
        return self._run(img, top_k)

    def _run(self, img: np.ndarray, top_k: int = 3) -> Prediction:
        t0 = time.perf_counter()
        probs = self._infer_tflite(img) if self.use_tflite else self._infer_keras(img)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        top_idx = np.argsort(probs)[::-1][:top_k]
        return Prediction(
            class_name   = self.labels[int(top_idx[0])],
            confidence   = float(probs[top_idx[0]]),
            inference_ms = round(elapsed_ms, 1),
            top_k        = [
                {"class": self.labels[int(i)], "confidence": float(probs[i])}
                for i in top_idx
            ],
        )

    def _infer_tflite(self, img: np.ndarray) -> np.ndarray:
        inp = np.expand_dims(img, axis=0)

        if self._in_dtype == np.uint8:
            inp = np.clip(
                inp / self._in_scale + self._in_zp, 0, 255
            ).astype(np.uint8)

        self._interp.set_tensor(self._in_idx, inp)
        self._interp.invoke()
        raw = self._interp.get_tensor(self._out_idx)[0]

        if raw.dtype == np.uint8:
            probs = (raw.astype(np.float32) - self._out_zp) * self._out_scale
        else:
            probs = raw.astype(np.float32)

        probs = np.clip(probs, 0.0, 1.0)
        total = probs.sum()
        return probs / total if total > 0 else probs

    def _infer_keras(self, img: np.ndarray) -> np.ndarray:
        return self._model.predict(np.expand_dims(img, 0), verbose=0)[0]

    def _warmup(self, n: int = 3) -> None:
        dummy = np.zeros((128, 128, 3), dtype=np.uint8)
        for _ in range(n):
            self._run(self.preprocessor.process(dummy))
        _log.info("Warm-up concluído (%d execuções).", n)


# ──────────────────────────────────────────────────────────────────────────────
# Renderização do overlay de UI
# ──────────────────────────────────────────────────────────────────────────────
class OverlayRenderer:
    """Desenha todos os elementos visuais sobre o frame da câmera."""

    _FONT = cv2.FONT_HERSHEY_SIMPLEX

    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    def render(
        self,
        frame:      np.ndarray,
        prediction: Optional[Prediction],
        fps:        float,
        roi:        Optional[tuple[int, int, int, int]],
        paused:     bool,
    ) -> np.ndarray:
        out = frame.copy()
        h, w = out.shape[:2]

        if roi is not None:
            self._draw_roi(out, roi)

        if prediction is not None:
            self._draw_top_bar(out, prediction, w)
            self._draw_topk_panel(out, prediction, h)

        self._draw_fps(out, fps, w)
        self._draw_hint_bar(out, h, w)

        if paused:
            self._draw_paused(out, h, w)

        return out

    def _draw_roi(self, frame: np.ndarray, roi: tuple[int, int, int, int]) -> None:
        x1, y1, x2, y2 = roi
        cv2.rectangle(frame, (x1, y1), (x2, y2), _C_CYAN, 2)
        tick = 14
        for px, py in ((x1, y1), (x2, y1), (x1, y2), (x2, y2)):
            dx = tick if px == x1 else -tick
            dy = tick if py == y1 else -tick
            cv2.line(frame, (px, py), (px + dx, py), _C_CYAN, 3)
            cv2.line(frame, (px, py), (px, py + dy), _C_CYAN, 3)

    def _draw_top_bar(
        self, frame: np.ndarray, pred: Prediction, w: int
    ) -> None:
        bar_h = 56
        self._blend_rect(frame, (0, 0, w, bar_h), alpha=0.70)
        color = pred.color if pred.confidence >= self.threshold else _C_GRAY

        cv2.putText(
            frame, pred.display_name,
            (12, 36), self._FONT, 0.90, color, 2, cv2.LINE_AA,
        )
        info = f"{pred.confidence:.1%}   {pred.inference_ms:.0f} ms"
        cv2.putText(
            frame, info,
            (w - 210, 36), self._FONT, 0.62, color, 1, cv2.LINE_AA,
        )

    def _draw_topk_panel(
        self, frame: np.ndarray, pred: Prediction, h: int
    ) -> None:
        n        = len(pred.top_k)
        panel_w  = 310
        panel_h  = 18 + n * 30
        x0, y0   = 10, h - panel_h - 36
        x1, y1   = x0 + panel_w, y0 + panel_h

        # guardar limites para evitar saída do frame
        y0 = max(0, y0)
        y1 = min(h, y1)
        x1 = min(frame.shape[1], x1)

        self._blend_rect(frame, (x0, y0, x1, y1), alpha=0.65)

        for i, item in enumerate(pred.top_k):
            bar_y   = y0 + 12 + i * 30
            bar_len = int(item["confidence"] * (panel_w - 16))
            bar_clr = _C_GREEN if i == 0 else _C_GRAY

            cv2.rectangle(frame, (x0 + 4, bar_y), (x0 + 4 + bar_len, bar_y + 16), bar_clr, -1)
            label = self._short_label(item["class"])
            cv2.putText(
                frame,
                f"{label}  {item['confidence']:.0%}",
                (x0 + 8, bar_y + 12),
                self._FONT, 0.42, _C_WHITE, 1, cv2.LINE_AA,
            )

    def _draw_fps(self, frame: np.ndarray, fps: float, w: int) -> None:
        cv2.putText(
            frame, f"FPS {fps:.1f}",
            (w - 100, 74), self._FONT, 0.58, _C_WHITE, 1, cv2.LINE_AA,
        )

    def _draw_hint_bar(self, frame: np.ndarray, h: int, w: int) -> None:
        bar_h = 26
        self._blend_rect(frame, (0, h - bar_h, w, h), alpha=0.70)
        hint = "[Q] Sair   [S] Salvar   [ESPAÇO] Pausar   [R] ROI"
        cv2.putText(
            frame, hint,
            (10, h - 8), self._FONT, 0.42, _C_GRAY, 1, cv2.LINE_AA,
        )

    def _draw_paused(self, frame: np.ndarray, h: int, w: int) -> None:
        cv2.putText(
            frame, "PAUSADO",
            (w // 2 - 68, h // 2),
            self._FONT, 1.4, _C_YELLOW, 3, cv2.LINE_AA,
        )

    @staticmethod
    def _blend_rect(
        frame: np.ndarray,
        rect: tuple[int, int, int, int],
        alpha: float,
    ) -> None:
        """Semi-transparente: darkens the region without full opacity."""
        x0, y0, x1, y1 = rect
        h, w = frame.shape[:2]
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w, x1), min(h, y1)
        if x1 <= x0 or y1 <= y0:
            return
        region = frame[y0:y1, x0:x1]
        dark   = np.full_like(region, 20)
        frame[y0:y1, x0:x1] = cv2.addWeighted(dark, alpha, region, 1.0 - alpha, 0)

    @staticmethod
    def _short_label(class_name: str, max_len: int = 30) -> str:
        if "___" in class_name:
            _, cond = class_name.split("___", 1)
            return cond.replace("_", " ").title()[:max_len]
        return class_name.replace("_", " ")[:max_len]


# ──────────────────────────────────────────────────────────────────────────────
# Sessão de câmera — loop de captura, inferência e controle
# ──────────────────────────────────────────────────────────────────────────────
class CameraSession:
    """Gerencia câmera, agenda inferências e processa teclas."""

    def __init__(
        self,
        engine:   InferenceEngine,
        renderer: OverlayRenderer,
        args:     argparse.Namespace,
    ) -> None:
        self._engine   = engine
        self._renderer = renderer
        self._args     = args

        self._cap:             Optional[cv2.VideoCapture] = None
        self._writer:          Optional[cv2.VideoWriter]  = None
        self._fps_buf:         deque[float] = deque(maxlen=_FPS_WINDOW)
        self._last_pred:       Optional[Prediction] = None
        self._frame_count      = 0
        self._saved_count      = 0
        self._paused           = False
        self._use_roi: bool    = not args.no_roi

    def run(self) -> None:
        self._open_camera()
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if self._args.record:
            self._open_writer(Path(self._args.record), w, h)

        roi = self._roi(w, h)
        _log.info("Câmera %d aberta (%dx%d). Pressione Q para encerrar.", self._args.camera, w, h)
        _log.info("Modelo: %s | Limiar: %.0f%%", "TFLite" if self._engine.use_tflite else "Keras", self._args.threshold * 100)

        t_prev = time.perf_counter()
        try:
            while True:
                ok, frame = self._cap.read()
                if not ok:
                    _log.error("Falha ao capturar frame. Verifique a câmera.")
                    break

                now = time.perf_counter()
                dt  = now - t_prev
                t_prev = now
                self._fps_buf.append(1.0 / max(dt, 1e-6))
                fps = float(np.mean(self._fps_buf))

                if not self._paused:
                    self._schedule_infer(frame, roi)

                out = self._renderer.render(
                    frame,
                    self._last_pred,
                    fps,
                    roi if self._use_roi else None,
                    self._paused,
                )

                cv2.imshow("PlantVillage — Diagnóstico em Tempo Real", out)

                if self._writer is not None:
                    self._writer.write(out)

                if not self._handle_key(cv2.waitKey(1) & 0xFF, frame):
                    break

                self._frame_count += 1
        finally:
            self._cleanup()

    # ── Inicialização de recursos ────────────────────────────────────────────

    def _open_camera(self) -> None:
        idx = self._args.camera
        self._cap = cv2.VideoCapture(idx)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Não foi possível abrir a câmera índice {idx}. "
                "Verifique se a webcam está conectada e tente --camera 0 ou --camera 1."
            )
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT,  720)
        self._cap.set(cv2.CAP_PROP_FPS,            30)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE,      1)  # minimiza latência

    def _open_writer(self, path: Path, w: int, h: int) -> None:
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self._writer = cv2.VideoWriter(str(path), fourcc, 25.0, (w, h))
        if not self._writer.isOpened():
            _log.warning("Não foi possível abrir o gravador de vídeo: %s", path)
            self._writer = None
        else:
            _log.info("Gravando em: %s", path)

    # ── Inferência ──────────────────────────────────────────────────────────

    def _schedule_infer(
        self,
        frame: np.ndarray,
        roi: tuple[int, int, int, int],
    ) -> None:
        if self._frame_count % self._args.infer_every != 0:
            return
        try:
            region = self._crop_roi(frame, roi) if self._use_roi else frame
            if region is not None:
                self._last_pred = self._engine.predict(region, top_k=self._args.top_k)
        except Exception as exc:  # noqa: BLE001
            _log.warning("Erro na inferência: %s", exc)

    def _crop_roi(
        self,
        frame: np.ndarray,
        roi: tuple[int, int, int, int],
    ) -> Optional[np.ndarray]:
        x1, y1, x2, y2 = roi
        crop = frame[y1:y2, x1:x2]
        return crop if crop.size > 0 else None

    # ── Teclado ─────────────────────────────────────────────────────────────

    def _handle_key(self, key: int, frame: np.ndarray) -> bool:
        """Retorna False quando a sessão deve encerrar."""
        if key in (ord("q"), 27):          # Q ou ESC
            return False
        if key == ord("s"):
            self._save_frame(frame)
        elif key == ord(" "):
            self._paused = not self._paused
            _log.info("Pausado: %s", self._paused)
        elif key == ord("r"):
            self._use_roi = not self._use_roi
            _log.info("ROI: %s", "ativado" if self._use_roi else "desativado")
        return True

    def _save_frame(self, frame: np.ndarray) -> None:
        self._saved_count += 1
        path = _SCRIPT_DIR / f"capture_{self._saved_count:03d}.jpg"
        cv2.imwrite(str(path), frame)
        print(f"  [✓] Frame salvo: {path.name}")

    # ── Geometria ───────────────────────────────────────────────────────────

    @staticmethod
    def _roi(w: int, h: int) -> tuple[int, int, int, int]:
        side = int(min(w, h) * _ROI_RATIO)
        cx, cy = w // 2, h // 2
        return cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2

    def _cleanup(self) -> None:
        if self._cap:
            self._cap.release()
        if self._writer:
            self._writer.release()
        cv2.destroyAllWindows()
        _log.info("Câmera liberada. Sessão encerrada.")


# ──────────────────────────────────────────────────────────────────────────────
# Resolução automática do modelo
# ──────────────────────────────────────────────────────────────────────────────
def _resolve_model(args: argparse.Namespace) -> tuple[Path, bool]:
    """
    Determina o caminho e tipo do modelo.
    Prioridade: argumento --model > TFLite INT8 > Keras.
    """
    if args.model:
        p = Path(args.model)
        return p, p.suffix.lower() == ".tflite"

    if _DEFAULT_TFLITE.exists():
        _log.info("Modelo selecionado automaticamente: %s", _DEFAULT_TFLITE)
        return _DEFAULT_TFLITE, True

    if _DEFAULT_KERAS.exists():
        _log.warning(
            "TFLite não encontrado. Usando Keras: %s", _DEFAULT_KERAS
        )
        return _DEFAULT_KERAS, False

    raise FileNotFoundError(
        "Nenhum modelo encontrado. Esperado em:\n"
        f"  {_DEFAULT_TFLITE}\n  {_DEFAULT_KERAS}\n"
        "Use --model <caminho> para especificar o modelo."
    )


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Diagnóstico de doenças em plantas via webcam (PlantVillage).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="Exemplo: python camera_inference.py --camera 0 --threshold 0.65",
    )
    p.add_argument(
        "--model", default=None, metavar="CAMINHO",
        help="Caminho para modelo .tflite ou .keras. Detectado automaticamente se omitido.",
    )
    p.add_argument(
        "--labels", default=str(_DEFAULT_LABELS), metavar="CAMINHO",
        help="Caminho para o arquivo labels.json.",
    )
    p.add_argument(
        "--camera", type=int, default=0, metavar="N",
        help="Índice do dispositivo de câmera.",
    )
    p.add_argument(
        "--threshold", type=float, default=0.50, metavar="0-1",
        help="Confiança mínima para exibir predição com cor de destaque.",
    )
    p.add_argument(
        "--top-k", type=int, default=3, dest="top_k", metavar="N",
        help="Número de predições a exibir no painel lateral.",
    )
    p.add_argument(
        "--infer-every", type=int, default=_DEFAULT_INFER_EVERY,
        dest="infer_every", metavar="N",
        help="Executa inferência a cada N frames (menor = mais frequente, mais CPU).",
    )
    p.add_argument(
        "--no-roi", action="store_true",
        help="Classifica o frame completo em vez do ROI central.",
    )
    p.add_argument(
        "--record", default=None, metavar="ARQUIVO.avi",
        help="Grava a sessão em arquivo de vídeo.",
    )
    return p


# ──────────────────────────────────────────────────────────────────────────────
# Ponto de entrada
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    print(
        "\n"
        "================================================\n"
        "  PlantVillage - Diagnostico em Tempo Real\n"
        "  MobileNetV2 | 38 classes | 97.3% acc\n"
        "================================================\n"
    )

    args = _build_parser().parse_args()

    try:
        model_path, use_tflite = _resolve_model(args)
    except FileNotFoundError as exc:
        _log.error("%s", exc)
        sys.exit(1)

    _log.info(
        "Carregando modelo %s: %s",
        "TFLite" if use_tflite else "Keras",
        model_path,
    )

    try:
        engine = InferenceEngine(
            model_path   = model_path,
            labels_path  = Path(args.labels),
            use_tflite   = use_tflite,
        )
    except (FileNotFoundError, ImportError, RuntimeError) as exc:
        _log.error("Falha ao carregar modelo: %s", exc)
        sys.exit(1)

    renderer = OverlayRenderer(threshold=args.threshold)
    session  = CameraSession(engine=engine, renderer=renderer, args=args)

    try:
        session.run()
    except RuntimeError as exc:
        _log.error("%s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        _log.info("Interrompido pelo usuário.")


if __name__ == "__main__":
    main()
