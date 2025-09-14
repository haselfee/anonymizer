#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-vmgitlab}
PORT=${PORT:-5050}
REG="$HOST:$PORT"
REG_NS="$REG/workaholics/anonymizer"   # anpassen, falls nötig
REG_USER=${REG_USER:-}
REG_PASS=${REG_PASS:-}

echo "== DNS =="
getent hosts "$HOST" || { echo "Host $HOST nicht auflösbar"; exit 1; }

echo "== Port =="
nc -vz "$HOST" "$PORT" || { echo "Port $PORT nicht erreichbar"; exit 1; }

echo "== TLS HEAD =="
curl -skI "https://$REG/v2/" || { echo "Registry-Endpoint /v2/ nicht erreichbar"; exit 1; }

if [[ -n "${REG_USER}" && -n "${REG_PASS}" ]]; then
  echo "== Docker Login =="
  echo "$REG_PASS" | docker login "$REG" -u "$REG_USER" --password-stdin

  echo "== Optional: Probe-Tag & -Push (nur falls lokales Image existiert) =="
  if docker image inspect anonymizer-backend:1.0.0 >/dev/null 2>&1; then
    docker tag anonymizer-backend:1.0.0  "$REG_NS/anonymizer-backend:1.0.0"
    docker push "$REG_NS/anonymizer-backend:1.0.0"
  else
    echo "(lokales Image anonymizer-backend:1.0.0 nicht gefunden – Push übersprungen)"
  fi
else
  echo "(REG_USER/REG_PASS nicht gesetzt – Login übersprungen)"
fi

echo "== OK =="

