# frontend/Dockerfile
# --- Stage 1: build -----------------------------------------------------------
FROM node:22-slim AS build
WORKDIR /app
ENV CI=1
COPY frontend/package*.json /app/
RUN npm ci
COPY frontend/ /app/
# Falls Angular CLI lokal: npx verwenden
RUN npx ng build --configuration=production

# --- Stage 2: runtime (non-root nginx) ---------------------------------------
FROM nginxinc/nginx-unprivileged:stable
# Default listen: 8080 (non-root)
COPY --from=build /app/dist/ /usr/share/nginx/html/
# Optional: eigene nginx.conf mit security headers
# COPY ops/nginx/nginx.conf /etc/nginx/nginx.conf
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
