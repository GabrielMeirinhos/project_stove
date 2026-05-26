FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dependências do OpenCV (headless — sem GUI)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-inference.txt ./
RUN pip install --no-cache-dir -r requirements-inference.txt

# Copia apenas os módulos necessários para inferência
COPY __init__.py ./
COPY inference/__init__.py ./inference/
COPY inference/classifier.py ./inference/
COPY inference/server.py ./inference/

EXPOSE 8001
CMD ["uvicorn", "inference.server:app", "--host", "0.0.0.0", "--port", "8001"]
