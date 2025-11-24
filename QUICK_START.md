# Quick Start Guide

## Start Backend (with hot reload)

```bash
cd src/cad_coder_backend
sudo docker compose up -d
```

Backend runs at: http://localhost:8000
- Code changes auto-reload (--reload flag enabled)

## Start Frontend

### Option 1: Dev Mode (Recommended - Hot Reload)

```bash
cd src/ui
sudo docker compose -f docker-compose.dev.yml up
```

Frontend runs at: http://localhost:3000
- Code changes auto-reload

### Option 2: Production Mode

```bash
cd src/ui
sudo docker build -t cad-coder-ui .
sudo docker run -d -p 8080:80 --name cad-coder-ui-container cad-coder-ui
```

Frontend runs at: http://localhost:8080

## Stop Services

```bash
# Backend
cd src/cad_coder_backend
sudo docker compose down

# Frontend Dev
cd src/ui
sudo docker compose -f docker-compose.dev.yml down

# Frontend Production
sudo docker stop cad-coder-ui-container
sudo docker rm cad-coder-ui-container
```

