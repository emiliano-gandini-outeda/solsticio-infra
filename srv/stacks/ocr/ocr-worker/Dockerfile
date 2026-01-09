FROM python:3.12-alpine

WORKDIR /app

# 1. Instalar dependencias del sistema
RUN apk add --no-cache \
    tesseract-ocr \
    tesseract-ocr-data-spa \
    tesseract-ocr-data-eng \
    poppler-utils

# 2. Copiar UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 3. Copiar pyproject.toml y uv.lock
COPY pyproject.toml uv.lock ./

# 4. Crear virtual environment con UV e instalar dependencias
RUN uv sync --frozen --no-dev

# 5. Copiar worker
COPY worker.py ./

# 6. Crear directorios
RUN mkdir -p uploads results

# 7. Ejecutar con UV run
CMD ["uv", "run", "python", "worker.py"]