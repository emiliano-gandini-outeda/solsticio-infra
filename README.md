# solsticio-infra
Infrastructure stack for my server (Solsticio): Docker-based services, internal API, and web UI for managing containers and system resources.

This repository is designed to be developed locally and deployed to a Linux server.

---

## Architecture Overview

The stack is composed of:

- **Infra API**  
  A FastAPI service that manages container lifecycle and exposes internal endpoints.

- **Web UI**  
  A lightweight Vue-based interface that communicates with the Infra API.

- **Docker Stack**  
  All services are orchestrated using Docker Compose.

---

## Repository Structure

```

/srv
├─ stacks/
│  ├─ infra/                     # Single entry point
│  │  ├─ docker-compose.yml      # Traefik
│  │
│  ├─ infra-api/                 # Server brain
│  │  ├─ docker-compose.yml
│  │  ├─ Dockerfile
│  │  └─ app/
│  │     └─ main.py
│  │
│  ├─ infra-ui/                  # Web dashboard
│  │  ├─ docker-compose.yml
│  │  ├─ Dockerfile
│  │  ├─ nginx.conf
│  │  ├─ index.html
│  │  ├─ package.json
│  │  ├─ vite.config.js
│  │  └─ src/
│  │     ├─ main.js
│  │     ├─ api.js
│  │     └─ App.vue
│  │
│  ├─ ocr/                       # Actual service (example)
│  │  ├─ docker-compose.yml
│  │  ├─ ocr-api/
│  │  │  ├─ Dockerfile
│  │  │  └─ app/
│  │  │     └─ main.py
│  │  ├─ ocr-worker/
│  │  │  ├─ Dockerfile
│  │  │  └─ worker.py
│  │  └─ tesseract/
│  │     └─ Dockerfile
│  │
│  └─ test/                      # Temporary stacks
│     └─ docker-compose.yml
│
├─ data/
│  ├─ ocr/                       # OCR inputs / outputs
│  │  ├─ uploads/
│  │  └─ results/
│  │
│  ├─ redis/                     # Job persistence
│  │
│  └─ logs/
│     ├─ infra-api/
│     ├─ infra-ui/
│     └─ ocr/
│
├─ backups/                      # Manual backups
│
└─ README.md                     # Internal documentation

```

## Setup Instructions

### 1. Clone the repository

```bash
cd /srv
git clone https://your-repo.git .
# or, if already cloned
git pull origin main
````

---

### 2. Create required directories

The stack requires persistent directories for data, logs, and backups.

```bash
sudo mkdir -p /srv/data/ocr/uploads
sudo mkdir -p /srv/data/ocr/results
sudo mkdir -p /srv/data/redis
sudo mkdir -p /srv/data/logs/infra-api
sudo mkdir -p /srv/data/logs/infra-ui
sudo mkdir -p /srv/data/logs/ocr
sudo mkdir -p /srv/backups
```

---

### 3. Set proper ownership

All directories must be writable by the user that runs the stack (assumed `your_user`):

```bash
sudo chown -R your_user:your_user /srv/stacks
sudo chown -R your_user:your_user /srv/data
sudo chown -R your_user:your_user /srv/backups
```

> This ensures `uv` can create virtual environments and that Docker can write logs and persistent data.

---

### 4. Install Python dependencies with `uv`

Run `uv` inside each Python stack:

```bash
# Infra API
cd /srv/stacks/infra-api
uv sync --frozen --no-dev

# OCR API
cd /srv/stacks/ocr/ocr-api
uv sync --frozen --no-dev

# OCR Worker
cd /srv/stacks/ocr/ocr-worker
uv sync --frozen --no-dev
```

> This will create virtual environments and install all dependencies according to the lock files.

---

### 5. Build and deploy the stack

Use the **infra** compose as the entry point for the whole system:

```bash
cd /srv/stacks/infra
docker compose build
docker compose up -d
```

This will start:

* Traefik (reverse proxy)
* Infra API
* Infra UI
* OCR API + OCR Worker
* Redis
* Tesseract container

---

### 6. Verify services

```bash
docker compose ps
```

All services should be `Up`:

* `traefik`
* `infra-api`
* `infra-ui`
* `ocr-api`
* `ocr-worker`
* `redis`
* `tesseract`

---

### 7. Test OCR functionality

From your PC:

```bash
# Upload file
curl -F "file=@/path/to/file.pdf" http://ocr.solsticio.local/upload

# Check result
curl http://ocr.solsticio.local/results/file.txt
```

All uploaded files are stored in `/srv/data/ocr/uploads` and results are stored in `/srv/data/ocr/results`.

---

### Notes

* All secrets, tokens, and configuration variables are managed via `/srv/.env`.
* The stack assumes the user `your_user` owns all relevant folders.
* Traefik routes the services via hostnames defined in `.env` (e.g., `ui.DOMAIN`, `ocr.DOMAIN`, etc.).
