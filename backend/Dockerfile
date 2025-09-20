# backend/Dockerfile
# --- Stage 1: builder ---------------------------------------------------------
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps (build-only)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Lock your deps if available; fallback to requirements.txt
# Copy minimal context first for better layer cache
COPY backend/requirements*.txt /app/
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip wheel \
 && if [ -f requirements.lock.txt ]; then /opt/venv/bin/pip install -r requirements.lock.txt; \
    elif [ -f requirements.txt ]; then /opt/venv/bin/pip install -r requirements.txt; fi

# --- Stage 2: runtime (non-root) ---------------------------------------------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -r -u 10001 -m appuser
WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Only copy runtime code (avoid tests, docs, etc.)
COPY backend/ /app/

# Drop Linux capabilities & tighten perms
RUN chown -R appuser:appuser /app
USER appuser

# Expose unprivileged port (backend already on 8000 → OK)
EXPOSE 8000

# HEALTHCHECK probes uvicorn root path
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1

# Use uvicorn (no root, no reload in prod)
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
