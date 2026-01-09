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
│  │     ├─config.js
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
├─ README.md
└─ setup.sh                     # Setup automation script
```

---

## Quick Setup

### Option A: Automated Setup (Recommended)

Run the automated setup script from `/srv`:

```bash
cd /srv
chmod +x setup.sh
./setup.sh your_username
```

Or if you want to use the current user:
```bash
./setup.sh
```

The script will create all required directories, set proper ownership and verify the structure.

### Option B: Manual Setup

Follow the traditional steps:

---

## Setup Instructions

### 1. Clone the repository

```bash
cd /srv
git clone https://github.com/emiliano-gandini-outeda/solsticio-infra .
# or, if already cloned
git pull origin main
```

---

### 2. Create required directories

**Option A: Using setup script**
```bash
cd /srv
chmod +x setup.sh
./setup.sh your_username
```

**Option B: Manually**
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

### 3. Configure environment variables

Before proceeding, complete the configuration by setting up the required environment variables:

1. **Update `config.js`** - Open `/srv/stacks/infra-ui/src/config.js` and complete the following variable:
   ```javascript
   INFRA_API_TOKEN: "your_secret_token"
   ```

2. **Setup environment file** - Copy the example environment file and adjust it with your specific values:
   ```bash
   cp /srv/.env.example /srv/.env
   nvim /srv/.env  # or use your preferred text editor
   ```

   The `.env` file should contain all necessary variables as shown in `.env.example`:
   ```bash
   # ---- GLOBAL ----
   TZ=America/Montevideo
   ENV=production
   
   # ---- SECURITY ----
   INFRA_API_TOKEN=your_secret_token
   JWT_SECRET=your_secret
   
   # ---- NETWORK ----
   DOMAIN=solsticio.local
   PUBLIC_IP=192.168.31.XXX
   
   # ---- CONTAINERS ----
   TEST_CONTAINER_TTL=3600
   ```

   **Important**: Replace all placeholder values (like `your_secret_token`, `your_secret`, `192.168.31.XXX`) with your actual configuration values.

---

### 4. Set proper ownership

All directories must be writable by the user that runs the stack (assumed `your_user`):

```bash
sudo chown -R your_user:your_user /srv/stacks
sudo chown -R your_user:your_user /srv/data
sudo chown -R your_user:your_user /srv/backups
```

> This ensures `uv` can create virtual environments and that Docker can write logs and persistent data.

---

### 5. Install Python dependencies with `uv`

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

### 6. Build and deploy the stack

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

---

### 7. Verify services

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

---

### 8. Test OCR functionality (via UI)

The example OCR system is designed to be used **from the web UI**, not manually via `curl`.

#### Access the UI

Open in your browser:

```
http://ui.solsticio.local
```

#### OCR workflow

1. Go to the **OCR** section in the dashboard.
2. Click **Select file** and choose a PDF from your local machine.
3. Click **Procesar OCR** to enqueue the job.
4. The job will appear under **Trabajos en curso**.
5. Once processing finishes, the result will appear under **Resultados**.
6. Click **📥 Descargar** to download the generated `.txt` file directly to your default downloads folder.

The UI automatically refreshes OCR jobs and results.

#### Storage paths (server-side)

* Uploaded files:

  ```
  /srv/data/ocr/uploads
  ```
* OCR results:

  ```
  /srv/data/ocr/results
  ```

These paths are shared between the OCR API and worker via Docker volumes.

---

Perfecto. Acá tenés la **sección adicional**, con el **mismo estilo claro y orientado a UI** que el OCR workflow:

---

### 9. Docker workflow (via UI)

Container management is handled **entirely from the web UI**, acting as a control panel over Docker.

#### Access

Open in your browser:

```
http://ui.solsticio.local
```

#### Docker workflow

1. The **Contenedores** table lists all managed Docker containers in the stack.
2. Each container shows:

   * **Name**
   * **Current status** (`running`, `exited`, etc.)
3. Available actions per container:

   * **▶ Start** starts the container
   * **■ Stop** stops the container
   * **🧪 Test 1h** runs a health/test action for the container
   * **🗑 Remove** stops and removes the container
4. Click **↻ Refresh** to reload container status at any time.

All actions are executed immediately through the backend API and reflected in real time in the UI.

#### What happens behind the scenes

* The UI sends authenticated requests to the **infra API**.
* The infra API:

  * Executes Docker commands (`start`, `stop`, `rm`, etc.)
  * Collects container state and metadata
  * Returns normalized status data to the UI
* No direct Docker access is required from the browser.

---

## Troubleshooting

### Permission Issues
```bash
# If you encounter permission errors:
sudo chmod +x /srv/setup.sh
./setup.sh $(whoami)
```

### Missing Directories
```bash
# Run the setup script again:
cd /srv
./setup.sh your_username
```

### Docker Issues
```bash
# Check Docker service
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Check logs
cd /srv/stacks/infra
docker compose logs
```

---

## License
AGPL-3.0 License - See [LICENSE](LICENSE) file for details.

---

**Maintained by Emiliano Gandini** | [GitHub](https://github.com/emiliano-gandini-outeda)

