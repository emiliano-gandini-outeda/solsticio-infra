FROM python:3.12-slim

WORKDIR /app

# Copiamos uv desde la imagen oficial para lockfile reproducible
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiamos pyproject.toml + lock
COPY pyproject.toml uv.lock ./

# Instalamos dependencias con uv
RUN uv sync --frozen --no-dev

# Copiamos la app
COPY app ./app

# Logs persistentes opcionales
VOLUME ["/app/logs"]

# Comando de arranque
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
