#!/usr/bin/env bash

HOST=vmgitlab
PORT=5050
REG="$HOST:$PORT/workaholics/anonymizer"

# Login (Deploy-Token oder User+PAT)
docker login https://$HOST:$PORT

# Tag + Push
docker tag anonymizer-backend:1.0.0  $REG/anonymizer-backend:1.0.0
docker tag anonymizer-frontend:1.0.0 $REG/anonymizer-frontend:1.0.0
docker push $REG/anonymizer-backend:1.0.0
docker push $REG/anonymizer-frontend:1.0.0
