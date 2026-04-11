# 🌿 Pipeline de Classificação de Espécies de Plantas
### Dataset PlantVillage · OpenCV · TensorFlow · TFLite · Raspberry Pi

---

## Estrutura do Projeto

```
outputs/
├── models/
│   ├── best_fase1.keras        # Melhor checkpoint da Fase 1
│   ├── best_fase2.keras        # Melhor checkpoint da Fase 2
│   ├── model_final.keras       # Modelo final Keras
│   ├── saved_model/            # TF SavedModel (deploy genérico)
│   ├── model_dynamic.tflite   # TFLite quantização dinâmica
│   ├── model_int8.tflite      # TFLite INT8 (Raspberry Pi) ✅ recomendado
│   └── labels.json             # Mapeamento índice → classe
├── plots/
│   ├── 01_amostras.png
│   ├── 02_distribuicao.png
│   ├── 03_preprocessamento.png
│   ├── 04_training_curves.png
│   ├── 05_confusion_matrix.png
│   └── 06_inferencia_exemplo.png
├── logs/
│   ├── history_fase1.csv
│   └── history_fase2.csv
├── config.json
├── test_metrics.json
└── classification_report.txt
```

---

## Instalação

```bash
pip install tensorflow opencv-python scikit-learn matplotlib seaborn kagglehub
# Opcional (rotação aleatória no augmentation)
pip install tensorflow-addons
```

---

## Execução

```bash
# Pipeline completo
python plant_classification_pipeline.py

# Inferência em tempo real com câmera
python plant_classification_pipeline.py --camera
```

---

## Arquitetura — MobileNetV2 + Transfer Learning

```
Input (128×128×3)
    │
    ▼
Rescaling [-1, 1]       ← normalização específica MobileNetV2
    │
    ▼
MobileNetV2 backbone    ← pesos ImageNet, ~154 camadas
  [Fase 1: CONGELADO]
  [Fase 2: camadas > 100 desbloqueadas]
    │
    ▼
GlobalAveragePooling2D
    │
    ▼
Dense(256, relu) + L2
    │
    ▼
Dropout(0.4)
    │
    ▼
Dense(N_classes, softmax)
```

**Por que MobileNetV2?**
- Projetado para embarcados (depthwise separable convolutions)
- ~14 MB — cabe facilmente em Raspberry Pi
- Treinado no ImageNet → excelentes features visuais de base
- Com quantização INT8: ~3.5 MB e 2–5× mais rápido

---

## Estratégia de Treinamento em 2 Fases

| Fase | Backbone | LR | Objetivo |
|------|----------|----|----------|
| 1 | Congelado | 1e-3 | Treinar apenas o classificador |
| 2 | Parcialmente desbloqueado (camadas > 100) | 1e-5 | Fine-tune para domínio de folhas |

---

## Pré-processamento OpenCV

1. **BGR → RGB** — converte canal de cor
2. **Filtro bilateral** — remove ruído preservando bordas das nervuras
3. **CLAHE (LAB)** — melhora contraste sem saturar cores
4. **Resize com padding** — preserva proporção da folha
5. **Normalização** → [0, 1]

---

## Otimização para Raspberry Pi

### Quantização INT8
```python
# Reduz ~4× o tamanho e ~2× a latência
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type  = tf.uint8
converter.inference_output_type = tf.uint8
```

### Comparativo de Tamanho
| Formato | Tamanho | Latência (RPi 4) |
|---------|---------|-----------------|
| Keras (.keras) | ~14 MB | ~200 ms |
| TFLite FP32 | ~14 MB | ~120 ms |
| TFLite Dynamic | ~4 MB | ~80 ms |
| **TFLite INT8** | **~3.5 MB** | **~50 ms** |

### Outras técnicas recomendadas
- Reduzir resolução: 128×128 → 96×96 (mais rápido, leve perda de acurácia)
- Usar `tflite_runtime` no Pi (mais leve que o TF completo)
- Inferência a cada N frames na câmera (não é necessário processar todo frame)

---

## Uso da Classe de Inferência

```python
from plant_classification_pipeline import PlantClassifier

# Com TFLite (produção / embarcado)
classifier = PlantClassifier(
    model_path="outputs/models/model_int8.tflite",
    labels_path="outputs/models/labels.json",
    use_tflite=True,
)

result = classifier.predict("minha_folha.jpg")
print(result)
# {
#   'top_prediction': {'class': 'Tomato___Healthy', 'confidence': 0.97},
#   'top_k': [...],
#   'inference_ms': 52.3
# }

# Integração com câmera (OpenCV)
import cv2
cap = cv2.VideoCapture(0)
_, frame = cap.read()
result = classifier.predict_from_array(frame)
```

---

## Monitoramento com TensorBoard

```bash
tensorboard --logdir outputs/logs
```
