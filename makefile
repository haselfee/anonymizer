# Makefile at repo root
REG?=localhost
IMAGE_B?=$(REG)/anonymizer-backend:dev
IMAGE_F?=$(REG)/anonymizer-frontend:dev

.PHONY: build-backend build-frontend run-backend run-frontend scan-backend scan-frontend k3d-import

build-backend:
	docker build -f backend/Dockerfile -t $(IMAGE_B) .

build-frontend:
	docker build -f frontend/Dockerfile -t $(IMAGE_F) .

run-backend:
	docker run --rm -p 8000:8000 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m \
		--security-opt no-new-privileges \
		--cap-drop ALL \
		$(IMAGE_B)

run-frontend:
	docker run --rm -p 8080:8080 --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m \
		--security-opt no-new-privileges \
		--cap-drop ALL \
		$(IMAGE_F)

scan-backend:
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $$HOME/.cache/trivy:/root/.cache/ aquasec/trivy:latest \
		image --severity CRITICAL,HIGH --ignore-unfixed --scanners vuln,secret,config --no-progress $(IMAGE_B)

scan-frontend:
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $$HOME/.cache/trivy:/root/.cache/ aquasec/trivy:latest \
		image --severity CRITICAL,HIGH --ignore-unfixed --scanners vuln,secret,config --no-progress $(IMAGE_F)

k3d-import:
	k3d image import $(IMAGE_B) $(IMAGE_F) -c anonymizer


# Optional: 
# .trivyignore anlegen (z. B. für false positives, 
# CVEs mit „won’t fix“ in Upstream).