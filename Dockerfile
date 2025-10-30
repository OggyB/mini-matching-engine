# ========= Base image =========
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
 && rm -rf /var/lib/apt/lists/*

# Poetry kur
RUN pip install --no-cache-dir "poetry==1.8.3"

WORKDIR /app

# ========= Install dependencies =========
COPY pyproject.toml poetry.lock ./

# Sanal env devre dışı bırak (global install)
RUN poetry config virtualenvs.create false

# Derlenmiş wheel sorunu çözmek için native build
RUN poetry install --no-root --no-interaction --no-ansi --compile

# ========= Copy source =========
COPY . .

# src dizinini Python path’e ekle
ENV PYTHONPATH=/app/src

CMD ["python", "-m", "src.engine.main"]
