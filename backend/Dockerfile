# backend/Dockerfile
FROM python:3.12-slim

# Prevent .pyc & enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# (optional) system deps for building wheels
RUN apt-get update -y && apt-get install -y --no-install-recommends \
      build-essential \
    && rm -rf /var/lib/apt/lists/*

# 1) install deps (best layer caching)
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# 2) copy source
COPY backend/ /app/

# 3) Optional non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
# adapt module if needed (api_server:app from your repo)
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
