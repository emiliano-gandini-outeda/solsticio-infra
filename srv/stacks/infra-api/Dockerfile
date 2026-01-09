FROM python:3.12-alpine

# Instalar uv
RUN pip install uv

WORKDIR /app

# Copiar archivos de dependencias
COPY pyproject.toml uv.lock ./

# Instalar dependencias usando uv (esto creará un .venv)
RUN uv sync --frozen --no-dev

# Copiar la aplicación
COPY app ./app

EXPOSE 8000

# Activar el entorno virtual y ejecutar con uv
CMD ["/bin/sh", "-c", "source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"]