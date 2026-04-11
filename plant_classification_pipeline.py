"""
╔══════════════════════════════════════════════════════════════════════╗
║       PIPELINE DE CLASSIFICAÇÃO DE ESPÉCIES DE PLANTAS               ║
║       Dataset: PlantVillage | Autor: Pipeline Profissional           ║
║       Stack: Python · OpenCV · TensorFlow · Transfer Learning        ║
╚══════════════════════════════════════════════════════════════════════╝

ESTRUTURA DO PIPELINE:
  Etapa 1 → Carregamento e Exploração dos Dados
  Etapa 2 → Pré-processamento com OpenCV
  Etapa 3 → Separação Treino / Validação / Teste
  Etapa 4 → Criação do Modelo (CNN + Transfer Learning)
  Etapa 5 → Treinamento com Callbacks e Visualização
  Etapa 6 → Avaliação (Matriz de Confusão + Métricas)
  Etapa 7 → Exportação do Modelo (SavedModel + TFLite)
  Etapa 8 → Inferência em Produção
"""

# ─────────────────────────────────────────────────────────────────────
# DEPENDÊNCIAS
# ─────────────────────────────────────────────────────────────────────
import os
import sys
import json
import time
import warnings
import numpy as np
import cv2
import matplotlib
matplotlib.use("Agg")          # backend sem janela para ambientes headless
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path
from datetime import datetime
from collections import Counter

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model, mixed_precision
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau,
    ModelCheckpoint, TensorBoard, CSVLogger
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix,
    top_k_accuracy_score
)
from sklearn.utils.class_weight import compute_class_weight

warnings.filterwarnings("ignore")
print(f"TensorFlow versão : {tf.__version__}")
print(f"OpenCV versão     : {cv2.__version__}")
print(f"GPUs disponíveis  : {tf.config.list_physical_devices('GPU')}")


# ─────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO GLOBAL — altere aqui para adaptar ao seu ambiente
# ─────────────────────────────────────────────────────────────────────
class Config:
    # Caminhos
    DATASET_ROOT   = Path("~/.cache/kagglehub/datasets/mohitsingh1804/plantvillage").expanduser()
    OUTPUT_DIR     = Path("./outputs")
    MODELS_DIR     = OUTPUT_DIR / "models"
    LOGS_DIR       = OUTPUT_DIR / "logs"
    PLOTS_DIR      = OUTPUT_DIR / "plots"

    # Imagem
    IMG_SIZE       = (128, 128)      # reduzido para melhor performance em embarcado
    IMG_CHANNELS   = 3

    # Treinamento
    BATCH_SIZE     = 32
    EPOCHS         = 50
    LEARNING_RATE  = 1e-3
    FINE_TUNE_LR   = 1e-5
    FINE_TUNE_AT   = 100             # camada a partir da qual descongelar no fine-tune

    # Divisão dos dados
    VAL_SPLIT      = 0.15
    TEST_SPLIT     = 0.15
    RANDOM_STATE   = 42

    # Modelo
    DROPOUT_RATE   = 0.4
    L2_REG         = 1e-4

    # Embarcado
    TFLITE_QUANTIZE = True           # quantização int8 para Raspberry Pi

    # Reprodutibilidade
    SEED           = 42

    @classmethod
    def setup_dirs(cls):
        """Cria estrutura de diretórios de saída."""
        for d in [cls.OUTPUT_DIR, cls.MODELS_DIR, cls.LOGS_DIR, cls.PLOTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)
        print(f"[✓] Diretórios criados em: {cls.OUTPUT_DIR.resolve()}")

    @classmethod
    def save(cls):
        """Persiste config em JSON para rastreabilidade."""
        cfg = {k: str(v) for k, v in vars(cls).items()
               if not k.startswith("_") and not callable(v)}
        with open(cls.OUTPUT_DIR / "config.json", "w") as f:
            json.dump(cfg, f, indent=2)


np.random.seed(Config.SEED)
tf.random.set_seed(Config.SEED)
Config.setup_dirs()
Config.save()


# ═══════════════════════════════════════════════════════════════════════
# ETAPA 1 — CARREGAMENTO E EXPLORAÇÃO DOS DADOS
# ═══════════════════════════════════════════════════════════════════════
class DataExplorer:
    """Varre o dataset e expõe metadados + visualizações."""

    SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp"}

    def __init__(self, root: Path):
        self.root = root
        self.image_paths: list[Path] = []
        self.labels:      list[str]  = []
        self.class_names: list[str]  = []
        self.class_to_idx: dict[str, int] = {}

    # ------------------------------------------------------------------
    def scan(self) -> "DataExplorer":
        """
        Percorre a árvore de diretórios esperando a estrutura:
            root/
              NomeClasse/
                imagem1.jpg
                imagem2.jpg
        """
        print("\n" + "═"*60)
        print("  ETAPA 1 — CARREGAMENTO E EXPLORAÇÃO DOS DADOS")
        print("═"*60)

        # Encontra o subdiretório que contém as pastas de classe
        dataset_dir = self._locate_dataset_dir()
        print(f"[→] Diretório do dataset: {dataset_dir}")

        classes = sorted([
            d.name for d in dataset_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ])

        if not classes:
            raise FileNotFoundError(
                f"Nenhuma subpasta encontrada em {dataset_dir}. "
                "Verifique se o dataset foi baixado corretamente."
            )

        self.class_names  = classes
        self.class_to_idx = {c: i for i, c in enumerate(classes)}

        for cls_name in classes:
            cls_dir = dataset_dir / cls_name
            for ext in self.SUPPORTED_EXT:
                for img_path in cls_dir.glob(f"*{ext}"):
                    self.image_paths.append(img_path)
                    self.labels.append(cls_name)

        print(f"[✓] Total de imagens  : {len(self.image_paths):,}")
        print(f"[✓] Total de classes  : {len(self.class_names)}")
        print(f"[✓] Classes           : {', '.join(self.class_names[:5])} …")
        return self

    def _locate_dataset_dir(self) -> Path:
        """Localiza o diretório raiz com as pastas de classe."""
        if not self.root.exists():
            raise FileNotFoundError(f"Dataset não encontrado em: {self.root}")
        # Busca recursiva pelo primeiro nível que contenha subpastas
        for candidate in [self.root, *self.root.rglob("*")]:
            if candidate.is_dir():
                subdirs = [d for d in candidate.iterdir() if d.is_dir()]
                if len(subdirs) > 2:   # heurística: pelo menos 3 classes
                    return candidate
        return self.root

    # ------------------------------------------------------------------
    def statistics(self) -> dict:
        """Imprime e retorna estatísticas do dataset."""
        counts = Counter(self.labels)
        stats = {
            "total_images" : len(self.image_paths),
            "num_classes"  : len(self.class_names),
            "min_per_class": min(counts.values()),
            "max_per_class": max(counts.values()),
            "avg_per_class": int(np.mean(list(counts.values()))),
        }
        print("\n[ESTATÍSTICAS DO DATASET]")
        for k, v in stats.items():
            print(f"  {k:<20}: {v}")
        return stats

    # ------------------------------------------------------------------
    def plot_samples(self, n_per_class: int = 3):
        """Salva grade de amostras (n_per_class × num_classes)."""
        n_classes = min(len(self.class_names), 10)  # máx 10 classes no plot
        fig, axes = plt.subplots(
            n_classes, n_per_class,
            figsize=(n_per_class * 3, n_classes * 3)
        )
        fig.suptitle("Amostras do Dataset PlantVillage", fontsize=14, y=1.01)

        for row, cls_name in enumerate(self.class_names[:n_classes]):
            cls_paths = [p for p, l in zip(self.image_paths, self.labels)
                         if l == cls_name]
            samples = np.random.choice(
                len(cls_paths),
                size=min(n_per_class, len(cls_paths)),
                replace=False
            )
            for col, idx in enumerate(samples):
                img = cv2.imread(str(cls_paths[idx]))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                ax = axes[row][col] if n_classes > 1 else axes[col]
                ax.imshow(img)
                ax.set_title(cls_name[:20], fontsize=7)
                ax.axis("off")

        plt.tight_layout()
        out = Config.PLOTS_DIR / "01_amostras.png"
        plt.savefig(out, dpi=120, bbox_inches="tight")
        plt.close()
        print(f"[✓] Amostras salvas em: {out}")

    # ------------------------------------------------------------------
    def plot_distribution(self):
        """Salva gráfico de distribuição de classes."""
        counts = Counter(self.labels)
        classes = list(counts.keys())
        values  = list(counts.values())

        plt.figure(figsize=(max(12, len(classes) * 0.4), 6))
        sns.barplot(x=classes, y=values, palette="viridis")
        plt.xticks(rotation=90, fontsize=7)
        plt.title("Distribuição de Imagens por Classe")
        plt.ylabel("Quantidade")
        plt.tight_layout()
        out = Config.PLOTS_DIR / "02_distribuicao.png"
        plt.savefig(out, dpi=120)
        plt.close()
        print(f"[✓] Distribuição salva em: {out}")


# ═══════════════════════════════════════════════════════════════════════
# ETAPA 2 — PRÉ-PROCESSAMENTO COM OPENCV
# ═══════════════════════════════════════════════════════════════════════
class Preprocessor:
    """
    Aplica pipeline de pré-processamento a cada imagem:
      1. Leitura com OpenCV
      2. Remoção de ruído (filtro bilateral)
      3. Melhoria de contraste via CLAHE
      4. Redimensionamento
      5. Normalização [0, 1]
    """

    def __init__(self, img_size: tuple[int, int] = Config.IMG_SIZE):
        self.img_size = img_size
        # CLAHE: melhora contraste localmente → preserva detalhes de nervuras
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    # ------------------------------------------------------------------
    def process(self, img_path: str | Path) -> np.ndarray | None:
        """
        Processa uma única imagem e retorna array float32 normalizado.
        Retorna None se a imagem for inválida.
        """
        img = cv2.imread(str(img_path))
        if img is None:
            return None

        # 1. Converte BGR → RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # 2. Remoção de ruído (preserva bordas — bom para folhas)
        img = cv2.bilateralFilter(img, d=5, sigmaColor=75, sigmaSpace=75)

        # 3. Melhoria de contraste canal por canal via CLAHE
        img = self._apply_clahe(img)

        # 4. Redimensiona mantendo proporção + padding
        img = self._resize_with_padding(img, self.img_size)

        # 5. Normalização para [0, 1]
        img = img.astype(np.float32) / 255.0

        return img

    # ------------------------------------------------------------------
    def _apply_clahe(self, img: np.ndarray) -> np.ndarray:
        """Aplica CLAHE em espaço LAB para evitar saturação de cores."""
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        l = self.clahe.apply(l)
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    # ------------------------------------------------------------------
    def _resize_with_padding(
        self, img: np.ndarray, target: tuple[int, int]
    ) -> np.ndarray:
        """
        Redimensiona preservando proporção e adiciona padding preto.
        Evita distorção de folhas que são verticalmente mais longas.
        """
        h, w = img.shape[:2]
        th, tw = target
        scale = min(tw / w, th / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Centraliza na imagem de destino
        canvas = np.zeros((th, tw, 3), dtype=np.uint8)
        y_off = (th - new_h) // 2
        x_off = (tw - new_w) // 2
        canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
        return canvas

    # ------------------------------------------------------------------
    def demo_comparison(self, img_path: Path):
        """Salva comparativo antes/depois do pré-processamento."""
        original = cv2.imread(str(img_path))
        original = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        processed = self.process(img_path)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        ax1.imshow(original)
        ax1.set_title("Original")
        ax1.axis("off")

        ax2.imshow(processed)
        ax2.set_title(f"Pré-processado {Config.IMG_SIZE}")
        ax2.axis("off")

        plt.suptitle("Comparativo de Pré-processamento (OpenCV)")
        plt.tight_layout()
        out = Config.PLOTS_DIR / "03_preprocessamento.png"
        plt.savefig(out, dpi=120)
        plt.close()
        print(f"[✓] Comparativo salvo em: {out}")


# ═══════════════════════════════════════════════════════════════════════
# ETAPA 3 — SEPARAÇÃO DOS DADOS
# ═══════════════════════════════════════════════════════════════════════
class DatasetBuilder:
    """
    Constrói tf.data.Dataset com:
      - Carregamento lazy (evita OOM em datasets grandes)
      - Data augmentation no treino
      - Prefetch e cache para performance
    """

    def __init__(
        self,
        explorer: DataExplorer,
        preprocessor: Preprocessor,
    ):
        self.explorer     = explorer
        self.preprocessor = preprocessor
        self.num_classes  = len(explorer.class_names)

    # ------------------------------------------------------------------
    def split(self) -> tuple[list, list, list, list, list, list]:
        """Divide paths e labels em treino / validação / teste."""
        print("\n" + "═"*60)
        print("  ETAPA 3 — SEPARAÇÃO DOS DADOS")
        print("═"*60)

        paths  = np.array([str(p) for p in self.explorer.image_paths])
        labels = np.array([
            self.explorer.class_to_idx[l] for l in self.explorer.labels
        ])

        # Primeiro split: separa teste
        X_temp, X_test, y_temp, y_test = train_test_split(
            paths, labels,
            test_size=Config.TEST_SPLIT,
            stratify=labels,
            random_state=Config.RANDOM_STATE,
        )

        # Segundo split: treino / validação do restante
        val_ratio = Config.VAL_SPLIT / (1 - Config.TEST_SPLIT)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_ratio,
            stratify=y_temp,
            random_state=Config.RANDOM_STATE,
        )

        print(f"  Treino     : {len(X_train):>6,} imagens")
        print(f"  Validação  : {len(X_val):>6,} imagens")
        print(f"  Teste      : {len(X_test):>6,} imagens")

        return X_train, X_val, X_test, y_train, y_val, y_test

    # ------------------------------------------------------------------
    def _load_and_preprocess(self, path: tf.Tensor, label: tf.Tensor):
        """
        Função de carregamento usada pelo tf.data pipeline.
        Executa o pré-processamento OpenCV via tf.py_function.
        """
        def _py_load(p):
            img = self.preprocessor.process(p.numpy().decode())
            if img is None:
                img = np.zeros((*Config.IMG_SIZE, 3), dtype=np.float32)
            return img.astype(np.float32)

        img = tf.py_function(_py_load, [path], tf.float32)
        img.set_shape([*Config.IMG_SIZE, Config.IMG_CHANNELS])
        label_oh = tf.one_hot(label, self.num_classes)
        return img, label_oh

    # ------------------------------------------------------------------
    def _augment(self, img: tf.Tensor, label: tf.Tensor):
        """
        Data augmentation apenas no conjunto de treino.
        Transformações inspecionadas para não distorcer folhas.
        """
        img = tf.image.random_flip_left_right(img)
        img = tf.image.random_flip_up_down(img)
        img = tf.image.random_brightness(img, max_delta=0.2)
        img = tf.image.random_contrast(img, lower=0.8, upper=1.2)
        img = tf.image.random_saturation(img, lower=0.8, upper=1.2)
        img = tf.clip_by_value(img, 0.0, 1.0)

        # Rotação aleatória ±30°
        img = self._random_rotate(img)
        return img, label

    @staticmethod
    def _random_rotate(img: tf.Tensor) -> tf.Tensor:
        """Rotação aleatória com tf.raw_ops para compatibilidade."""
        try:
            import tensorflow_addons as tfa
            angle = tf.random.uniform([], -0.52, 0.52)  # ±30 graus
            return tfa.image.rotate(img, angle)
        except ImportError:
            # Fallback: sem rotação se tfa não disponível
            return img

    # ------------------------------------------------------------------
    def build(
        self,
        X_train, X_val, X_test,
        y_train, y_val, y_test,
    ) -> tuple[tf.data.Dataset, tf.data.Dataset, tf.data.Dataset]:
        """Constrói e retorna os três tf.data.Dataset."""
        AUTOTUNE = tf.data.AUTOTUNE

        def make_ds(paths, labels, augment=False, shuffle=False):
            ds = tf.data.Dataset.from_tensor_slices((paths, labels))
            if shuffle:
                ds = ds.shuffle(len(paths), seed=Config.SEED)
            ds = ds.map(self._load_and_preprocess, num_parallel_calls=AUTOTUNE)
            if augment:
                ds = ds.map(self._augment, num_parallel_calls=AUTOTUNE)
            ds = ds.batch(Config.BATCH_SIZE).prefetch(AUTOTUNE)
            return ds

        train_ds = make_ds(X_train, y_train, augment=True, shuffle=True)
        val_ds   = make_ds(X_val,   y_val)
        test_ds  = make_ds(X_test,  y_test)

        print(f"\n[✓] Datasets tf.data construídos com batch_size={Config.BATCH_SIZE}")
        return train_ds, val_ds, test_ds

    # ------------------------------------------------------------------
    def compute_class_weights(self, y_train: np.ndarray) -> dict:
        """Calcula pesos para lidar com desequilíbrio de classes."""
        weights = compute_class_weight(
            "balanced",
            classes=np.unique(y_train),
            y=y_train,
        )
        return {i: w for i, w in enumerate(weights)}


# ═══════════════════════════════════════════════════════════════════════
# ETAPA 4 — CRIAÇÃO DO MODELO
# ═══════════════════════════════════════════════════════════════════════
class ModelFactory:
    """
    Fábrica de modelos com duas estratégias:
      A) CNN customizada (referência + interpretabilidade)
      B) MobileNetV2 com Transfer Learning (recomendado para produção)
    """

    @staticmethod
    def build_custom_cnn(num_classes: int) -> Model:
        """
        CNN do zero com blocos conv + BN + pooling.
        Boa para entender o comportamento do modelo.
        """
        inputs = keras.Input(shape=(*Config.IMG_SIZE, Config.IMG_CHANNELS))

        # Bloco 1
        x = layers.Conv2D(32, 3, padding="same", activation="relu")(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Conv2D(32, 3, padding="same", activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D()(x)
        x = layers.Dropout(0.25)(x)

        # Bloco 2
        x = layers.Conv2D(64, 3, padding="same", activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Conv2D(64, 3, padding="same", activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D()(x)
        x = layers.Dropout(0.25)(x)

        # Bloco 3
        x = layers.Conv2D(128, 3, padding="same", activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Conv2D(128, 3, padding="same", activation="relu")(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D()(x)
        x = layers.Dropout(0.3)(x)

        # Classificador
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dense(256, activation="relu",
                         kernel_regularizer=keras.regularizers.l2(Config.L2_REG))(x)
        x = layers.Dropout(Config.DROPOUT_RATE)(x)
        outputs = layers.Dense(num_classes, activation="softmax")(x)

        model = Model(inputs, outputs, name="custom_cnn")
        return model

    # ------------------------------------------------------------------
    @staticmethod
    def build_mobilenetv2(num_classes: int) -> Model:
        """
        MobileNetV2 com Transfer Learning.
        ✔ Leve (~14MB), projetado para embarcados
        ✔ Treinado no ImageNet → boas features visuais
        Estratégia: congelar backbone → treinar head → fine-tune parcial
        """
        base = MobileNetV2(
            input_shape=(*Config.IMG_SIZE, Config.IMG_CHANNELS),
            include_top=False,
            weights="imagenet",
        )
        base.trainable = False   # fase 1: apenas o classificador

        inputs = keras.Input(shape=(*Config.IMG_SIZE, Config.IMG_CHANNELS))

        # Pré-processamento específico do MobileNetV2 ([-1, 1])
        x = layers.Rescaling(scale=2.0, offset=-1.0)(inputs)

        x = base(x, training=False)
        x = layers.GlobalAveragePooling2D()(x)
        x = layers.Dense(256, activation="relu",
                         kernel_regularizer=keras.regularizers.l2(Config.L2_REG))(x)
        x = layers.Dropout(Config.DROPOUT_RATE)(x)
        outputs = layers.Dense(num_classes, activation="softmax")(x)

        model = Model(inputs, outputs, name="mobilenetv2_transfer")
        return model, base   # retorna base separadamente para fine-tune

    # ------------------------------------------------------------------
    @staticmethod
    def enable_fine_tuning(base_model: Model) -> None:
        """
        Descongela as últimas camadas do backbone para fine-tuning.
        Mantém BatchNorm congelado para estabilidade.
        """
        base_model.trainable = True
        for layer in base_model.layers[:Config.FINE_TUNE_AT]:
            layer.trainable = False
        # BatchNorm sempre congelado durante fine-tune
        for layer in base_model.layers:
            if isinstance(layer, layers.BatchNormalization):
                layer.trainable = False
        print(f"[✓] Fine-tuning: {sum(1 for l in base_model.layers if l.trainable)} "
              f"camadas treináveis desbloqueadas")


# ═══════════════════════════════════════════════════════════════════════
# ETAPA 5 — TREINAMENTO
# ═══════════════════════════════════════════════════════════════════════
class Trainer:
    """Encapsula o ciclo completo de treinamento."""

    def __init__(self, model: Model, num_classes: int):
        self.model       = model
        self.num_classes = num_classes
        self.history_p1  = None
        self.history_p2  = None

    # ------------------------------------------------------------------
    def compile(self, lr: float = Config.LEARNING_RATE):
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=lr),
            loss="categorical_crossentropy",
            metrics=[
                "accuracy",
                keras.metrics.TopKCategoricalAccuracy(k=3, name="top3_acc"),
            ],
        )
        self.model.summary(print_fn=lambda x: print(" " + x))

    # ------------------------------------------------------------------
    def _get_callbacks(self, phase: str) -> list:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return [
            EarlyStopping(
                monitor="val_accuracy", patience=8,
                restore_best_weights=True, verbose=1,
            ),
            ReduceLROnPlateau(
                monitor="val_loss", factor=0.5,
                patience=4, min_lr=1e-7, verbose=1,
            ),
            ModelCheckpoint(
                str(Config.MODELS_DIR / f"best_{phase}.keras"),
                monitor="val_accuracy",
                save_best_only=True, verbose=0,
            ),
            TensorBoard(
                log_dir=str(Config.LOGS_DIR / f"{phase}_{ts}"),
                histogram_freq=0,
            ),
            CSVLogger(str(Config.LOGS_DIR / f"history_{phase}.csv")),
        ]

    # ------------------------------------------------------------------
    def train_phase1(
        self,
        train_ds, val_ds,
        class_weights: dict | None = None,
    ):
        """Fase 1: treina apenas o classificador (backbone congelado)."""
        print("\n" + "═"*60)
        print("  ETAPA 5 — TREINAMENTO  |  Fase 1: Transfer Learning")
        print("═"*60)

        self.compile(Config.LEARNING_RATE)
        self.history_p1 = self.model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=Config.EPOCHS,
            callbacks=self._get_callbacks("fase1"),
            class_weight=class_weights,
            verbose=1,
        )
        print("[✓] Fase 1 concluída")
        return self.history_p1

    # ------------------------------------------------------------------
    def train_phase2(
        self,
        train_ds, val_ds,
        base_model: Model,
        class_weights: dict | None = None,
    ):
        """Fase 2: fine-tuning — desbloqueia parte do backbone."""
        print("\n" + "═"*60)
        print("  ETAPA 5 — TREINAMENTO  |  Fase 2: Fine-Tuning")
        print("═"*60)

        ModelFactory.enable_fine_tuning(base_model)
        self.compile(Config.FINE_TUNE_LR)   # LR menor para não destruir features

        self.history_p2 = self.model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=Config.EPOCHS // 2,
            callbacks=self._get_callbacks("fase2"),
            class_weight=class_weights,
            verbose=1,
        )
        print("[✓] Fase 2 concluída")
        return self.history_p2

    # ------------------------------------------------------------------
    def plot_history(self):
        """Plota curvas de loss e accuracy das duas fases."""
        histories = []
        labels = []
        if self.history_p1:
            histories.append(self.history_p1)
            labels.append("Fase 1")
        if self.history_p2:
            histories.append(self.history_p2)
            labels.append("Fase 2")

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        for hist, label in zip(histories, labels):
            epochs = range(1, len(hist.history["loss"]) + 1)
            axes[0].plot(epochs, hist.history["loss"],     label=f"{label} - Treino")
            axes[0].plot(epochs, hist.history["val_loss"], label=f"{label} - Val", ls="--")
            axes[1].plot(epochs, hist.history["accuracy"],     label=f"{label} - Treino")
            axes[1].plot(epochs, hist.history["val_accuracy"], label=f"{label} - Val", ls="--")

        axes[0].set_title("Loss")
        axes[0].set_xlabel("Épocas")
        axes[0].legend()
        axes[0].grid(alpha=0.3)

        axes[1].set_title("Acurácia")
        axes[1].set_xlabel("Épocas")
        axes[1].legend()
        axes[1].grid(alpha=0.3)

        plt.suptitle("Curvas de Treinamento", fontsize=13)
        plt.tight_layout()
        out = Config.PLOTS_DIR / "04_training_curves.png"
        plt.savefig(out, dpi=120)
        plt.close()
        print(f"[✓] Curvas salvas em: {out}")


# ═══════════════════════════════════════════════════════════════════════
# ETAPA 6 — AVALIAÇÃO
# ═══════════════════════════════════════════════════════════════════════
class Evaluator:
    """Avalia o modelo no conjunto de teste e gera relatórios."""

    def __init__(self, model: Model, class_names: list[str]):
        self.model       = model
        self.class_names = class_names

    # ------------------------------------------------------------------
    def evaluate(self, test_ds: tf.data.Dataset) -> dict:
        """Avalia métricas gerais no conjunto de teste."""
        print("\n" + "═"*60)
        print("  ETAPA 6 — AVALIAÇÃO")
        print("═"*60)

        results = self.model.evaluate(test_ds, verbose=1)
        metric_names = self.model.metrics_names
        metrics = dict(zip(metric_names, results))

        print("\n[MÉTRICAS NO CONJUNTO DE TESTE]")
        for k, v in metrics.items():
            print(f"  {k:<20}: {v:.4f}")

        # Salva métricas
        with open(Config.OUTPUT_DIR / "test_metrics.json", "w") as f:
            json.dump({k: float(v) for k, v in metrics.items()}, f, indent=2)

        return metrics

    # ------------------------------------------------------------------
    def full_report(self, test_ds: tf.data.Dataset):
        """Gera previsões, classification report e matriz de confusão."""
        y_true, y_pred = [], []

        for batch_imgs, batch_labels in test_ds:
            preds = self.model.predict(batch_imgs, verbose=0)
            y_pred.extend(np.argmax(preds, axis=1))
            y_true.extend(np.argmax(batch_labels.numpy(), axis=1))

        y_true = np.array(y_true)
        y_pred = np.array(y_pred)

        # Classification report
        report = classification_report(
            y_true, y_pred,
            target_names=self.class_names,
            digits=4,
        )
        print("\n[CLASSIFICATION REPORT]")
        print(report)
        with open(Config.OUTPUT_DIR / "classification_report.txt", "w") as f:
            f.write(report)

        # Matriz de confusão
        self._plot_confusion_matrix(y_true, y_pred)

    # ------------------------------------------------------------------
    def _plot_confusion_matrix(self, y_true, y_pred):
        cm = confusion_matrix(y_true, y_pred)
        n = len(self.class_names)
        figsize = max(12, n * 0.6)

        plt.figure(figsize=(figsize, figsize * 0.85))
        sns.heatmap(
            cm, annot=(n <= 30),   # anotações apenas se houver poucas classes
            fmt="d",
            cmap="Blues",
            xticklabels=self.class_names,
            yticklabels=self.class_names,
        )
        plt.title("Matriz de Confusão", fontsize=13)
        plt.ylabel("Real")
        plt.xlabel("Predito")
        plt.xticks(rotation=90, fontsize=7)
        plt.yticks(rotation=0, fontsize=7)
        plt.tight_layout()
        out = Config.PLOTS_DIR / "05_confusion_matrix.png"
        plt.savefig(out, dpi=150)
        plt.close()
        print(f"[✓] Matriz de confusão salva em: {out}")


# ═══════════════════════════════════════════════════════════════════════
# ETAPA 7 — EXPORTAÇÃO DO MODELO
# ═══════════════════════════════════════════════════════════════════════
class ModelExporter:
    """
    Exporta o modelo em múltiplos formatos:
      • SavedModel  → deploy genérico (TF Serving, etc.)
      • .keras      → checkpoint padrão Keras
      • TFLite FP32 → baseline embarcado
      • TFLite INT8 → quantizado para Raspberry Pi (recomendado)
    """

    def __init__(self, model: Model, class_names: list[str]):
        self.model       = model
        self.class_names = class_names

    # ------------------------------------------------------------------
    def export_savedmodel(self):
        path = str(Config.MODELS_DIR / "saved_model")
        self.model.export(path)
        print(f"[✓] SavedModel salvo em: {path}")

    # ------------------------------------------------------------------
    def export_keras(self):
        path = str(Config.MODELS_DIR / "model_final.keras")
        self.model.save(path)
        print(f"[✓] Keras model salvo em: {path}")

    # ------------------------------------------------------------------
    def export_tflite(
        self,
        representative_dataset=None,
        quantize: bool = Config.TFLITE_QUANTIZE,
    ):
        """
        Converte para TFLite.
        Com quantize=True aplica quantização INT8 completa:
          ✔ Reduz tamanho em ~4x
          ✔ Acelera inferência em ARM via operações inteiras nativas
          ✔ Ideal para Raspberry Pi 4 / Zero 2W
        """
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)

        if quantize and representative_dataset is not None:
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.representative_dataset = representative_dataset
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
            converter.inference_input_type  = tf.uint8
            converter.inference_output_type = tf.uint8
            suffix = "int8"
        elif quantize:
            # Quantização dinâmica (sem dataset de calibração)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            suffix = "dynamic"
        else:
            suffix = "fp32"

        tflite_model = converter.convert()
        path = Config.MODELS_DIR / f"model_{suffix}.tflite"
        path.write_bytes(tflite_model)

        size_mb = path.stat().st_size / 1e6
        print(f"[✓] TFLite {suffix.upper()} salvo em: {path} ({size_mb:.2f} MB)")
        return str(path)

    # ------------------------------------------------------------------
    def save_labels(self):
        """Salva mapeamento de índice → classe para uso na inferência."""
        labels_path = Config.MODELS_DIR / "labels.json"
        with open(labels_path, "w") as f:
            json.dump({i: name for i, name in enumerate(self.class_names)}, f,
                      indent=2, ensure_ascii=False)
        print(f"[✓] Labels salvas em: {labels_path}")

    # ------------------------------------------------------------------
    def benchmark_tflite(self, tflite_path: str, n_runs: int = 50):
        """Benchmarks latência de inferência do modelo TFLite."""
        interpreter = tf.lite.Interpreter(model_path=tflite_path)
        interpreter.allocate_tensors()
        in_details  = interpreter.get_input_details()
        out_details = interpreter.get_output_details()

        dummy = np.random.randint(0, 255, in_details[0]["shape"]).astype(
            in_details[0]["dtype"]
        )

        latencies = []
        for _ in range(n_runs):
            t0 = time.perf_counter()
            interpreter.set_tensor(in_details[0]["index"], dummy)
            interpreter.invoke()
            latencies.append((time.perf_counter() - t0) * 1000)

        latencies = latencies[5:]  # descarta warm-up
        print(f"\n[BENCHMARK TFLITE — {n_runs} runs]")
        print(f"  Média    : {np.mean(latencies):.1f} ms")
        print(f"  P95      : {np.percentile(latencies, 95):.1f} ms")
        print(f"  Min/Max  : {np.min(latencies):.1f} / {np.max(latencies):.1f} ms")


# ═══════════════════════════════════════════════════════════════════════
# ETAPA 8 — INFERÊNCIA EM PRODUÇÃO
# ═══════════════════════════════════════════════════════════════════════
class PlantClassifier:
    """
    Classe pronta para produção — suporta modelo Keras ou TFLite.
    Integre com câmera USB/Pi Camera assim:

        cap = cv2.VideoCapture(0)
        _, frame = cap.read()
        result = classifier.predict_from_array(frame)
    """

    def __init__(
        self,
        model_path: str,
        labels_path: str,
        use_tflite: bool = False,
    ):
        self.use_tflite   = use_tflite
        self.preprocessor = Preprocessor()

        # Carrega labels
        with open(labels_path) as f:
            self.labels = {int(k): v for k, v in json.load(f).items()}

        if use_tflite:
            self.interpreter = tf.lite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            self.in_idx  = self.interpreter.get_input_details()[0]["index"]
            self.out_idx = self.interpreter.get_output_details()[0]["index"]
            self.in_dtype = self.interpreter.get_input_details()[0]["dtype"]
        else:
            self.model = keras.models.load_model(model_path)

    # ------------------------------------------------------------------
    def predict(self, image_path: str, top_k: int = 3) -> dict:
        """
        Classifica uma imagem a partir do caminho.

        Retorna:
            {
              "top_prediction": {"class": "Tomato___Healthy", "confidence": 0.97},
              "top_k": [{"class": ..., "confidence": ...}, ...],
              "inference_ms": 12.4
            }
        """
        img = self.preprocessor.process(image_path)
        if img is None:
            raise ValueError(f"Não foi possível carregar a imagem: {image_path}")
        return self._run_inference(img, top_k)

    # ------------------------------------------------------------------
    def predict_from_array(self, bgr_array: np.ndarray, top_k: int = 3) -> dict:
        """
        Classifica diretamente de um array BGR (ex: captura de câmera).
        """
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            cv2.imwrite(tmp.name, bgr_array)
            result = self.predict(tmp.name, top_k)
        os.unlink(tmp.name)
        return result

    # ------------------------------------------------------------------
    def _run_inference(self, img: np.ndarray, top_k: int) -> dict:
        t0 = time.perf_counter()

        if self.use_tflite:
            inp = np.expand_dims(img, axis=0)
            if self.in_dtype == np.uint8:
                inp = (inp * 255).astype(np.uint8)
            self.interpreter.set_tensor(self.in_idx, inp)
            self.interpreter.invoke()
            probs = self.interpreter.get_tensor(self.out_idx)[0].astype(np.float32)
            if self.in_dtype == np.uint8:
                probs /= 255.0
        else:
            inp   = np.expand_dims(img, axis=0)
            probs = self.model.predict(inp, verbose=0)[0]

        elapsed_ms = (time.perf_counter() - t0) * 1000
        top_indices = np.argsort(probs)[::-1][:top_k]

        return {
            "top_prediction": {
                "class"     : self.labels[top_indices[0]],
                "confidence": float(probs[top_indices[0]]),
            },
            "top_k": [
                {"class": self.labels[i], "confidence": float(probs[i])}
                for i in top_indices
            ],
            "inference_ms": round(elapsed_ms, 2),
        }

    # ------------------------------------------------------------------
    def predict_and_visualize(self, image_path: str, save_path: str | None = None):
        """Exibe imagem com a predição sobreposta."""
        result = self.predict(image_path)
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        ax1.imshow(img)
        ax1.set_title(
            f"{result['top_prediction']['class']}\n"
            f"Confiança: {result['top_prediction']['confidence']:.1%}",
            fontsize=10
        )
        ax1.axis("off")

        classes = [r["class"][:25] for r in result["top_k"]]
        confs   = [r["confidence"] for r in result["top_k"]]
        colors  = ["#2ecc71" if i == 0 else "#95a5a6" for i in range(len(classes))]
        ax2.barh(classes[::-1], confs[::-1], color=colors[::-1])
        ax2.set_xlim(0, 1)
        ax2.set_xlabel("Confiança")
        ax2.set_title(f"Top-{len(classes)} Predições ({result['inference_ms']} ms)")
        ax2.grid(axis="x", alpha=0.3)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=120, bbox_inches="tight")
        else:
            plt.show()
        plt.close()
        return result


# ═══════════════════════════════════════════════════════════════════════
# MAIN — EXECUÇÃO DO PIPELINE COMPLETO
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "█"*60)
    print("  PIPELINE DE CLASSIFICAÇÃO DE PLANTAS — PlantVillage")
    print("█"*60 + "\n")

    # ── Etapa 1: Exploração ──────────────────────────────────────────
    explorer = DataExplorer(Config.DATASET_ROOT)
    explorer.scan()
    explorer.statistics()
    explorer.plot_samples(n_per_class=3)
    explorer.plot_distribution()

    # ── Etapa 2: Pré-processamento (demo) ───────────────────────────
    preprocessor = Preprocessor()
    sample_path  = explorer.image_paths[0]
    preprocessor.demo_comparison(sample_path)

    # ── Etapa 3: Divisão dos dados ──────────────────────────────────
    builder = DatasetBuilder(explorer, preprocessor)
    X_train, X_val, X_test, y_train, y_val, y_test = builder.split()
    class_weights = builder.compute_class_weights(y_train)
    train_ds, val_ds, test_ds = builder.build(
        X_train, X_val, X_test,
        y_train, y_val, y_test,
    )

    # ── Etapa 4: Modelo (MobileNetV2 — recomendado) ─────────────────
    print("\n" + "═"*60)
    print("  ETAPA 4 — CRIAÇÃO DO MODELO (MobileNetV2 + Transfer Learning)")
    print("═"*60)
    num_classes = len(explorer.class_names)
    model, base_model = ModelFactory.build_mobilenetv2(num_classes)

    # ── Etapa 5: Treinamento ─────────────────────────────────────────
    trainer = Trainer(model, num_classes)
    trainer.train_phase1(train_ds, val_ds, class_weights)
    trainer.train_phase2(train_ds, val_ds, base_model, class_weights)
    trainer.plot_history()

    # ── Etapa 6: Avaliação ───────────────────────────────────────────
    evaluator = Evaluator(model, explorer.class_names)
    evaluator.evaluate(test_ds)
    evaluator.full_report(test_ds)

    # ── Etapa 7: Exportação ──────────────────────────────────────────
    print("\n" + "═"*60)
    print("  ETAPA 7 — EXPORTAÇÃO DO MODELO")
    print("═"*60)
    exporter = ModelExporter(model, explorer.class_names)
    exporter.export_keras()
    exporter.export_savedmodel()
    exporter.save_labels()

    # Dataset de calibração para quantização INT8
    def representative_dataset_gen():
        for imgs, _ in train_ds.unbatch().batch(1).take(200):
            yield [imgs.numpy()]

    tflite_path = exporter.export_tflite(
        representative_dataset=representative_dataset_gen,
        quantize=True,
    )
    exporter.benchmark_tflite(tflite_path)

    # ── Etapa 8: Inferência de exemplo ──────────────────────────────
    print("\n" + "═"*60)
    print("  ETAPA 8 — INFERÊNCIA")
    print("═"*60)
    labels_path = str(Config.MODELS_DIR / "labels.json")

    # Usando Keras
    classifier_keras = PlantClassifier(
        model_path=str(Config.MODELS_DIR / "model_final.keras"),
        labels_path=labels_path,
        use_tflite=False,
    )
    result = classifier_keras.predict_and_visualize(
        image_path=str(sample_path),
        save_path=str(Config.PLOTS_DIR / "06_inferencia_exemplo.png"),
    )
    print("\n[RESULTADO DA INFERÊNCIA]")
    print(f"  Espécie detectada : {result['top_prediction']['class']}")
    print(f"  Confiança         : {result['top_prediction']['confidence']:.1%}")
    print(f"  Tempo de inferência: {result['inference_ms']} ms")

    # Usando TFLite (simulando Raspberry Pi)
    classifier_tflite = PlantClassifier(
        model_path=tflite_path,
        labels_path=labels_path,
        use_tflite=True,
    )
    result_lite = classifier_tflite.predict(str(sample_path))
    print(f"\n[TFLITE] {result_lite['top_prediction']['class']} "
          f"({result_lite['inference_ms']} ms)")

    print("\n" + "█"*60)
    print("  PIPELINE CONCLUÍDO COM SUCESSO!")
    print(f"  Outputs em: {Config.OUTPUT_DIR.resolve()}")
    print("█"*60 + "\n")


if __name__ == "__main__":
    main()


# ═══════════════════════════════════════════════════════════════════════
# SCRIPT BÔNUS — INFERÊNCIA EM TEMPO REAL COM CÂMERA (Raspberry Pi)
# Execute separadamente: python plant_classification_pipeline.py --camera
# ═══════════════════════════════════════════════════════════════════════
def run_camera_inference():
    """
    Loop de inferência em tempo real com câmera.
    Pressione 'q' para sair, 's' para salvar o frame atual.
    """
    labels_path = str(Config.MODELS_DIR / "labels.json")
    tflite_path = str(Config.MODELS_DIR / "model_dynamic.tflite")

    classifier = PlantClassifier(
        model_path=tflite_path,
        labels_path=labels_path,
        use_tflite=True,
    )

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("[CÂMERA] Iniciando... Pressione 'q' para sair, 's' para salvar.")
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Inferência a cada 10 frames (reduz CPU)
        if frame_count % 10 == 0:
            try:
                result = classifier.predict_from_array(frame)
                label  = result["top_prediction"]["class"]
                conf   = result["top_prediction"]["confidence"]
                ms     = result["inference_ms"]

                # Overlay na imagem
                text = f"{label} ({conf:.0%}) | {ms:.0f}ms"
                color = (0, 200, 0) if conf > 0.7 else (0, 165, 255)
                cv2.putText(frame, text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            except Exception as e:
                cv2.putText(frame, f"Erro: {e}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("PlantVillage Classifier", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            cv2.imwrite(f"capture_{frame_count}.jpg", frame)
            print(f"[✓] Frame salvo: capture_{frame_count}.jpg")

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()


if "--camera" in sys.argv:
    run_camera_inference()
