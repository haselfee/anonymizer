# Aufruf z.B. make redeploy-frontend
.PHONY: dev prod up down logs test \
        build-backend build-frontend \
        redeploy-backend redeploy-frontend

# Development (Hot Reload via compose.dev.yml)
dev:
	docker compose -f compose.dev.yml up

# Production (Nginx + FastAPI via compose.prod.yml)
prod:
	docker compose -f compose.prod.yml up --build -d

down:
	docker compose -f compose.dev.yml down || true
	docker compose -f compose.prod.yml down || true

logs:
	docker compose -f compose.prod.yml logs -f

test:
	pytest -q -rxXs

# --- Build only ---
build-backend:
	docker build -t anonymizer-backend -f backend/Dockerfile .

build-frontend:
	docker build -t anonymizer-frontend -f frontend/Dockerfile .

# --- Redeploy container (manuell, außerhalb von Compose) ---
redeploy-backend: build-backend
	docker rm -f backend 2>/dev/null || true
	docker run -d --name backend --network anonymizer-net -p 8000:8000 anonymizer-backend

redeploy-frontend: build-frontend
	docker rm -f frontend 2>/dev/null || true
	docker run -d --name frontend --network anonymizer-net -p 8080:80 anonymizer-frontend
