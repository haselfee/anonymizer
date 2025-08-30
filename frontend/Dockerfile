# 1) Build Angular
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# ggf. Konfiguration-Name anpassen (production/prod)
RUN npm run build -- --configuration production

# 2) Serve with Nginx
FROM nginx:1.27-alpine AS runtime
# Static assets
COPY --from=build /app/dist/ /usr/share/nginx/html/
# Nginx reverse proxy to backend service name "backend" on port 8000 (Compose network)
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null 2>&1 || exit 1
