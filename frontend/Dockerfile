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

# Alles aus dem Angular-Build in ein temp-Verzeichnis legen
# COPY --from=build /app/dist/ /tmp/dist/

# Robust kopieren: Angular <17 (dist/<app>/) oder >=17 (dist/<app>/browser/)
# RUN set -eux; \
#    if ls -d /tmp/dist/*/browser >/dev/null 2>&1; then \
#        cp -R /tmp/dist/*/browser/* /usr/share/nginx/html/; \
#    elif ls -d /tmp/dist/* >/dev/null 2>&1; then \
#        cp -R /tmp/dist/*/* /usr/share/nginx/html/ 2>/dev/null || cp -R /tmp/dist/* /usr/share/nginx/html/; \
#    else \
#        echo "No Angular build artifacts found under /tmp/dist"; exit 1; \
#    fi; \
#    rm -rf /tmp/dist

# siehe angular.json  "outputPath": "dist", 
COPY --from=build /app/dist/browser/ /usr/share/nginx/html/

# Deine Nginx-Config zuletzt
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null 2>&1 || exit 1