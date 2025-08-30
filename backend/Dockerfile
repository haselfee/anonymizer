# Multi-stage not necessary here; keep it slim & reproducible
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (curl only for healthchecks/logs; remove if not needed)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt ./requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source
# COPY backend/ /app/
COPY backend/ /app/backend/

# Security: drop root
RUN useradd -r -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

# App port
EXPOSE 8000

# Healthcheck (FastAPI /health)
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" >/dev/null 2>&1 || exit 1

CMD ["python", "-m", "uvicorn", "backend.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
