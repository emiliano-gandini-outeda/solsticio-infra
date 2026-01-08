FROM python:3.12-slim

WORKDIR /app

# Copiamos uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependencias
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Código del worker
COPY worker.py ./

# Logs persistentes opcionales
VOLUME ["/app/logs"]

# Comando de arranque
CMD ["python", "worker.py"]
