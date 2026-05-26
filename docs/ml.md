# ML — Classificação de Doenças em Plantas

## Visão Geral

Pipeline de transfer learning para detectar doenças em plantas usando o dataset PlantVillage.
Modelo otimizado para Raspberry Pi via quantização INT8 TFLite.

## Estrutura

```
ml/
├── datasets/          # Dataset PlantVillage (gitignored, ~3GB)
├── models/            # Pesos finais .keras / .tflite (gitignored)
├── checkpoints/       # Checkpoints por época (gitignored)
├── notebooks/         # Exploração e análise
├── training/
│   ├── pipeline.py    # Pipeline completo (download → treino → export)
│   └── download_dataset.py  # Só download via kagglehub
├── inference/         # Código de inferência reutilizável
├── experiments/       # Experimentos isolados
└── outputs/
    ├── config.json            # Configuração do treino (tracked)
    ├── test_metrics.json      # Métricas do conjunto de teste (tracked)
    └── classification_report.txt  # Report por classe (tracked)
```

## Arquitetura do Modelo

- **Backbone**: MobileNetV2 (pré-treinado ImageNet, congelado na fase 1)
- **Head**: GlobalAveragePooling2D → Dense(256, relu) → Dropout(0.5) → Dense(N, softmax)
- **Fase 1**: Só o head, LR=1e-3, ~10 épocas
- **Fase 2**: Últimas camadas do backbone desbloqueadas, LR=1e-5, ~10 épocas

## Pré-processamento

Via OpenCV:
1. Redimensionamento para 224×224
2. Filtro bilateral (redução de ruído, preserva bordas)
3. CLAHE (melhora contraste adaptativo)
4. Normalização [0, 1]

## Dataset

**PlantVillage** (Kaggle: `emmarex/plantdisease`)
- ~54.000 imagens, 38 classes (planta + doença)
- Classes incluem: tomate, batata, uva, maçã, morango, etc.
- ⚠️ Morango sub-representado no dataset atual

```bash
# Download manual
python ml/training/download_dataset.py
```

Requer `KAGGLE_USERNAME` e `KAGGLE_KEY` no `.env`.

## Treinamento

```bash
cd ml
python training/pipeline.py
```

Flags disponíveis (ver código):
- `--camera`: modo inferência em tempo real via webcam

## Exportação para Raspberry Pi

O pipeline gera automaticamente:
1. `models/model.keras` — pesos completos
2. `models/model.tflite` — INT8 quantizado (~3.5MB, ~50ms/inferência no RPi 4)
3. `models/labels.json` — mapeamento índice → classe

## Métricas esperadas

| Métrica | Valor alvo |
|---------|-----------|
| Acurácia (test) | >90% |
| Latência RPi 4 | ~50ms |
| Tamanho TFLite | ~3.5MB |

## Pendências técnicas

- [ ] Fine-tuning com fotos tiradas de celular (domínio diferente do dataset)
- [ ] Aumentar representação de morango no dataset (coleta manual ou data augmentation agressivo)
- [ ] Módulo de inferência standalone em `ml/inference/` para integração com backend
- [ ] Endpoint `/api/v1/vision` no backend para receber imagem → retornar predição
