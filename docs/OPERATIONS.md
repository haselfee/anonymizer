# Operations Guide (Runbook)

This document is for operators/SREs who deploy and run the app.

## Quick start (Docker Compose)
```bash
docker compose -f compose.prod.yml up -d --build
# Frontend: http://localhost:8080
# API via proxy: GET /api/health
```

## Hot deploy a single component
```bash
docker compose -f compose.prod.yml up -d --build frontend
docker compose -f compose.prod.yml up -d --build backend
```

## Reset including volumes
```bash
docker compose -f compose.prod.yml down -v
```

## Health endpoints
- Backend: `GET /health` → 200
- Frontend: serve `/` → 200

## Environment variables
- `MAP_PATH` (backend): path to mapping file inside container. Default: `mapping.txt`.

## Ports
- Backend container port: 8000
- Frontend (Nginx) container port: 80
- Published (compose.prod.yml): 8080→frontend:80

## Logs
- Both services log to STDOUT/STDERR. Use:
```bash
docker compose -f compose.prod.yml logs -f
```

## Security notes
- Backend runs non-root (uid 10001).
- Consider read-only FS for frontend (Nginx) in hardened environments.
- Keep images up-to-date; rebuild regularly.
