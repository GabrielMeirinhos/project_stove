FROM python:3.12-slim AS base
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY training/ ./training/
COPY inference/ ./inference/
COPY __init__.py ./

VOLUME ["/app/datasets", "/app/models", "/app/checkpoints", "/app/outputs"]

CMD ["python", "training/pipeline.py"]
