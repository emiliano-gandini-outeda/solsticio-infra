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

---

## Development Workflow

1. Clone the repository on your local machine
2. Copy `.env.example` to `.env` and adjust values for local development
3. Develop and test services locally using Docker Compose
4. Push changes to the repository
5. Pull the repository on the server
6. Provide a production `.env` file on the server
7. Start the stack using Docker Compose

