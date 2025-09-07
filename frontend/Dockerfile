# 1) Build stage
FROM node:20-alpine AS build
WORKDIR /app

# Install deps
COPY frontend/package*.json ./
RUN npm ci

# Copy sources & build
COPY frontend/ .
# Build and normalize Angular output to /app/www
# (Angular >=17: dist/<project>/browser/, ältere: dist/<project>/)
RUN npm run build && \
    PROJECT_NAME="$(node -e "const j=require('./angular.json');process.stdout.write(j.defaultProject || Object.keys(j.projects||{})[0] || '');")" && \
    OUTDIR="$(node -e "const j=require('./angular.json');const p=j.projects?.[process.argv[1]];process.stdout.write(p?.architect?.build?.options?.outputPath || 'dist');" "$PROJECT_NAME")" && \
    mkdir -p /app/www && \
    if [ -d "$OUTDIR/browser" ]; then cp -r "$OUTDIR/browser/"* /app/www/; \
    elif [ -d "$OUTDIR/$PROJECT_NAME/browser" ]; then cp -r "$OUTDIR/$PROJECT_NAME/browser/"* /app/www/; \
    elif [ -d "$OUTDIR/$PROJECT_NAME" ]; then cp -r "$OUTDIR/$PROJECT_NAME/"* /app/www/; \
    else cp -r "$OUTDIR/"* /app/www/; fi

# 2) Run stage
FROM nginx:alpine
# Optional: SPA-Routing + /api-Proxy (falls gewünscht):
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/www/ /usr/share/nginx/html/
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
