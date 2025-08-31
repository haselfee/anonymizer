# Development Guide

This document is for contributors/maintainers. End users should start with the top-level README.

## Project layout
```
backend/      # FastAPI app (uvicorn)
frontend/     # Angular app (built to dist/.../browser)
compose.dev.yml   # Dev setup (hot reload)
compose.prod.yml  # Prod setup (Nginx + FastAPI)
Makefile
```
## Prerequisites
- Docker Engine + Compose v2
- (Optional) Python 3.11+ and Node 20+ if you want to run without Docker

## Local development

### Dev mode (hot reload)
```bash
make dev
# Frontend: http://localhost:4200
# Backend:  http://localhost:8000
```

### Unit tests
```bash
pytest -q -rxXs
```

### Lint/format
```bash
ruff check .
black .
```

## Docker (manual)

```bash
make build-backend
make build-frontend
make redeploy-backend
make redeploy-frontend
```

## Docker Compose (prod-like)

```bash
make prod         # up -d --build
make logs         # logs -f
make down         # stop & remove
```

## Configuration & persistence
- Backend persists `mapping.txt`. In containers we recommend a volume or bind-mount.
- You can override the path with `MAP_PATH` env var; default is `mapping.txt` in CWD.

## Release workflow (GHCR)
- Push to `main` → images tagged `:latest`
- Tag `vX.Y.Z` → images tagged `:X.Y.Z`
- See `.github/workflows/docker.yml`

## Kubernetes (heads-up)
- Same images (OCI). Use the Helm chart under `charts/anonymizer/`.
- Frontend service routes `/api` to `backend:8000` via Nginx inside the pod.
