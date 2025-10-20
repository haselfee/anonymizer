SHELL := /bin/bash
.ONESHELL:
.SILENT:

# Host-Perspektive (push)
REG_HOST := $(strip localhost:5000)
# Cluster-Perspektive (pull)
CLUSTER_REG := $(strip k3d-registry:5000)

NS       ?= anonymizer
CHART    ?= charts/anonymizer
RELEASE  ?= anonymizer
TAG      ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo dev)

BACKEND_IMG_H  := $(REG_HOST)/anonymizer-backend:$(TAG)
FRONTEND_IMG_H := $(REG_HOST)/anonymizer-frontend:$(TAG)


# -------- Targets --------
.PHONY: all build push deploy restart logs pf clean print-vars registry-config check-hosts clean-rollout

all: print-vars build push deploy

build: build_backend build_frontend
	@echo "Built images with tag $(TAG)"

build_backend:
	docker build -t $(BACKEND_IMG_H) -f backend/Dockerfile .

build_frontend:
	docker build -t $(FRONTEND_IMG_H) -f frontend/Dockerfile .

push: push_backend push_frontend
	@echo "Pushed to $(REG_HOST)"

push_backend:
	docker push $(BACKEND_IMG_H)

push_frontend:
	docker push $(FRONTEND_IMG_H)

deploy: | check-hosts
	@echo "Deploying TAG=$(TAG) to $(CLUSTER_REG)"
	helm upgrade --install $(RELEASE) $(CHART) -n $(NS) \
	  --reset-values -f $(CHART)/values.dev.yaml \
	  --set-string global.imageRegistry= \
	  --set backend.repository=$(CLUSTER_REG)/anonymizer-backend \
	  --set frontend.repository=$(CLUSTER_REG)/anonymizer-frontend \
	  --set backend.tag=$(TAG) --set frontend.tag=$(TAG) \
	  --set backend.pullPolicy=IfNotPresent --set frontend.pullPolicy=IfNotPresent

restart:
	kubectl rollout restart deploy/$(RELEASE)-backend -n $(NS) || true
	kubectl rollout restart deploy/$(RELEASE)-frontend -n $(NS) || true

logs:
	@echo "Backend logs:" && kubectl logs deploy/$(RELEASE)-backend -n $(NS) --tail=80 || true
	@echo "Frontend logs:" && kubectl logs deploy/$(RELEASE)-frontend -n $(NS) --tail=80 || true

pf:
	@echo "Forwarding: backend 8000->svc, frontend 8080->svc"
	kubectl port-forward svc/$(RELEASE)-backend 8000:80 -n $(NS) & \
	kubectl port-forward svc/$(RELEASE)-frontend 8080:80 -n $(NS)

clean:
	-kubectl delete ns $(NS)
	-helm uninstall $(RELEASE) -n $(NS)

print-vars:
	echo "REG_HOST=[$(REG_HOST)]"
	echo "BACKEND_IMG_H=[$(BACKEND_IMG_H)]"
# --- NEW: generate registries.yaml reliably (no heredoc pitfalls)
.PHONY: registry-config
registry-config:
	@REG_IP=$$(docker inspect k3d-k3d-registry --format '{{ (index .NetworkSettings.Networks "k3d-anonymizer").IPAddress }}' 2>/dev/null); \
	if [ -z "$$REG_IP" ]; then \
	  docker network connect k3d-anonymizer k3d-k3d-registry 2>/dev/null || true; \
	  docker restart k3d-k3d-registry >/dev/null; sleep 2; \
	  REG_IP=$$(docker inspect k3d-k3d-registry --format '{{ (index .NetworkSettings.Networks "k3d-anonymizer").IPAddress }}'); \
	fi; \
	if [ -z "$$REG_IP" ]; then echo "ERROR: Could not determine registry IP in network k3d-anonymizer"; exit 1; fi; \
	echo "Using registry IP: $$REG_IP"; \
	printf '%s\n' \
'mirrors:' \
'  "k3d-registry:5000":' \
'    endpoint:' \
'      - "http://'"$$REG_IP"':5000"' \
'  "k3d-k3d-registry:5000":' \
'    endpoint:' \
'      - "http://'"$$REG_IP"':5000"' \
'configs:' \
'  "k3d-registry:5000":' \
'    tls:' \
'      insecure_skip_verify: true' \
'  "k3d-k3d-registry:5000":' \
'    tls:' \
'      insecure_skip_verify: true' \
	> registries.yaml

# --- NEW: /etc/hosts recommendation (no auto-edit)
check-hosts:
	@missing=0; \
	for host in anonymizer.local api.anonymizer.local; do \
	  if ! getent hosts $$host >/dev/null; then missing=1; fi; \
	done; \
	if [ $$missing -eq 0 ]; then \
	  echo "OK: hosts resolve (anonymizer.local, api.anonymizer.local)"; \
	else \
	  echo "Add this line to /etc/hosts (manual):"; \
	  echo "127.0.0.1 anonymizer.local api.anonymizer.local"; \
	fi

clean-rollout:
	kubectl scale deploy anonymizer-{frontend,backend} -n anonymizer --replicas=0
	kubectl delete rs -n anonymizer -l app=anonymizer || true
	kubectl delete pod -n anonymizer -l app=anonymizer --force --grace-period=0 || true
	kubectl scale deploy anonymizer-{frontend,backend} -n anonymizer --replicas=1