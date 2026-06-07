"""
╔══════════════════════════════════════════════════════════════════════╗
║       DOWNLOAD DE DATASETS — PROJECT STOVE                          ║
║       Coleta multi-fonte para balancear o modelo                    ║
║                                                                      ║
║  Datasets baixados (todos com licença de uso para pesquisa):        ║
║    1. PlantVillage          — base original (Kaggle)                ║
║    2. Strawberry Disease    — 2.500 imgs, estufa real (Kaggle)      ║
║    3. Chili Plant Disease   — 5 classes, malagueta (Kaggle)         ║
║    4. PlantDoc              — imagens de CAMPO real (GitHub)         ║
║                                                                      ║
║  O PlantDoc é o mais importante para ROBUSTEZ: o PlantVillage tem   ║
║  só imagens de laboratório (fundo limpo), o que faz o modelo        ║
║  falhar em fotos reais. PlantDoc traz fundos complexos de campo.    ║
╚══════════════════════════════════════════════════════════════════════╝

PRÉ-REQUISITOS:
    pip install kagglehub

    Para o Kaggle, configure suas credenciais uma vez:
      1. Acesse https://www.kaggle.com/settings/account
      2. Em "API", clique em "Create New Token" → baixa kaggle.json
      3. Coloque em:
           Windows: C:\\Users\\<seu_usuario>\\.kaggle\\kaggle.json
           Linux/Mac: ~/.kaggle/kaggle.json

    Para o PlantDoc é necessário ter o `git` instalado.

USO:
    python download_dataset.py              # baixa tudo
    python download_dataset.py --skip-plantdoc   # pula o PlantDoc
"""

import os
import sys
import shutil
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("download")


# ─────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────────────────────────────
class Config:
    # Pasta onde os datasets brutos ficarão organizados
    DOWNLOAD_DIR = Path("./datasets_raw")

    # Datasets do Kaggle: (slug, nome_amigavel)
    KAGGLE_DATASETS = [
        ("mohitsingh1804/plantvillage",                      "plantvillage"),
        ("usmanafzaal/strawberry-disease-detection-dataset", "strawberry_disease"),
        ("dhenyd/chili-plant-disease",                       "chili_disease"),
    ]

    # PlantDoc — repositório GitHub (imagens de campo real)
    PLANTDOC_REPO = "https://github.com/pratikkayal/PlantDoc-Dataset.git"
    PLANTDOC_DIR_NAME = "plantdoc"


# ═══════════════════════════════════════════════════════════════════════
# DOWNLOAD VIA KAGGLE
# ═══════════════════════════════════════════════════════════════════════
def download_kaggle_datasets() -> dict:
    """
    Baixa cada dataset do Kaggle via kagglehub e copia para DOWNLOAD_DIR.
    Retorna um dicionário {nome_amigavel: caminho_local}.
    """
    log.info("=" * 64)
    log.info("  KAGGLE — baixando %d datasets", len(Config.KAGGLE_DATASETS))
    log.info("=" * 64)

    try:
        import kagglehub
    except ImportError:
        log.error("kagglehub não instalado. Rode:  pip install kagglehub")
        sys.exit(1)

    results: dict = {}

    for slug, friendly_name in Config.KAGGLE_DATASETS:
        log.info("\n[->] Baixando: %s", slug)
        try:
            cache_path = Path(kagglehub.dataset_download(slug))
            log.info("    Baixado no cache: %s", cache_path)

            # Copia do cache para a nossa pasta organizada
            dest = Config.DOWNLOAD_DIR / friendly_name
            if dest.exists():
                log.info("    [SKIP] Já existe em %s", dest)
            else:
                shutil.copytree(cache_path, dest)
                log.info("    [OK] Copiado para: %s", dest)

            results[friendly_name] = dest

        except Exception as e:
            log.error("    [ERRO] Falha ao baixar %s: %s", slug, e)
            log.error("    Verifique suas credenciais do Kaggle (kaggle.json).")

    return results


# ═══════════════════════════════════════════════════════════════════════
# DOWNLOAD DO PLANTDOC (GitHub)
# ═══════════════════════════════════════════════════════════════════════
def download_plantdoc():
    """
    Clona o repositório PlantDoc do GitHub.
    Contém imagens de campo real — essencial para robustez do modelo.
    """
    log.info("\n" + "=" * 64)
    log.info("  PLANTDOC — clonando repositório (imagens de campo)")
    log.info("=" * 64)

    dest = Config.DOWNLOAD_DIR / Config.PLANTDOC_DIR_NAME

    if dest.exists():
        log.info("[SKIP] PlantDoc já existe em %s", dest)
        return dest

    # Verifica se o git está disponível
    if shutil.which("git") is None:
        log.error("[ERRO] git não encontrado no sistema.")
        log.error("       Instale o git ou baixe manualmente o ZIP em:")
        log.error("       https://github.com/pratikkayal/PlantDoc-Dataset")
        return None

    try:
        log.info("[->] git clone %s", Config.PLANTDOC_REPO)
        subprocess.run(
            ["git", "clone", "--depth", "1",
             Config.PLANTDOC_REPO, str(dest)],
            check=True,
        )
        log.info("[OK] PlantDoc clonado em: %s", dest)
        return dest

    except subprocess.CalledProcessError as e:
        log.error("[ERRO] git clone falhou: %s", e)
        return None


# ═══════════════════════════════════════════════════════════════════════
# RELATÓRIO DE CONTAGEM
# ═══════════════════════════════════════════════════════════════════════
def count_images(directory: Path) -> int:
    """Conta imagens recursivamente em um diretório."""
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    return sum(
        1 for p in directory.rglob("*")
        if p.suffix.lower() in exts
    )


def print_summary(kaggle_results: dict, plantdoc_path):
    """Imprime um resumo do que foi baixado."""
    log.info("\n" + "#" * 64)
    log.info("  RESUMO DO DOWNLOAD")
    log.info("#" * 64)

    total = 0

    for name, path in kaggle_results.items():
        if path and path.exists():
            n = count_images(path)
            total += n
            log.info("  %-28s %7d imagens   %s", name, n, path)

    if plantdoc_path and plantdoc_path.exists():
        n = count_images(plantdoc_path)
        total += n
        log.info("  %-28s %7d imagens   %s", "plantdoc", n, plantdoc_path)

    log.info("-" * 64)
    log.info("  TOTAL DE IMAGENS BAIXADAS: %d", total)
    log.info("=" * 64)

    log.info(
        "\n[PRÓXIMOS PASSOS]\n"
        "  Os datasets foram baixados em estruturas DIFERENTES:\n"
        "    - plantvillage / chili     -> pastas por classe (classificação)\n"
        "    - strawberry / plantdoc    -> imagens + anotações (detecção)\n\n"
        "  Para unificá-los em uma única árvore de classes pronta para o\n"
        "  seu pipeline.py, rode o próximo script de organização\n"
        "  (merge_datasets.py) — posso gerá-lo se quiser.\n"
    )


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════
def main():
    log.info("#" * 64)
    log.info("  DOWNLOAD DE DATASETS — PROJECT STOVE")
    log.info("#" * 64)

    Config.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Pasta de destino: %s\n", Config.DOWNLOAD_DIR.resolve())

    # 1. Datasets do Kaggle
    kaggle_results = download_kaggle_datasets()

    # 2. PlantDoc (a menos que --skip-plantdoc)
    plantdoc_path = None
    if "--skip-plantdoc" not in sys.argv:
        plantdoc_path = download_plantdoc()
    else:
        log.info("\n[SKIP] PlantDoc pulado (--skip-plantdoc)")

    # 3. Resumo
    print_summary(kaggle_results, plantdoc_path)


if __name__ == "__main__":
    main()