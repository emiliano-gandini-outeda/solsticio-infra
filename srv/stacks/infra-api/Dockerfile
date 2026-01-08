FROM python:3.12-slim

WORKDIR /app

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# app
COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
