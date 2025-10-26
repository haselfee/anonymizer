SHELL := /bin/bash
.ONESHELL:
.SILENT:

# Keep all your existing variables/targets.
# Add this include near the top:
include mk/portable-registry.mk

.PHONY: mirror-main
mirror-main:
	@echo "🔁 Mirroring 'main' to GitHub..."
	@git fetch github main >/dev/null 2>&1 || true
	@git push github main --force-with-lease
	@echo "✅ Mirror complete: GitHub(main) now matches local(main)"

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

# =============================================================================
#  K3D Cluster Recreate (Golden Path)
# =============================================================================
K3D_CLUSTER      ?= anonymizer
K3D_API_PORT     ?= 6445
K3D_REGISTRY     ?= k3d-registry:5000
K3D_NAMESPACE    ?= anonymizer
KUBECONFIG_FILE  ?= ~/.kube/config


# -------- Targets --------
.PHONY: all build push deploy restart logs pf clean print-vars registry-config check-hosts clean-rollout  k3d-recreate

all: print-vars build push deploy

#build: build_backend build_frontend
#	@echo "Built images with tag $(TAG)"

build: ## Build FE+BE images (portable)
	$(MAKE) __portable-build-fe
	$(MAKE) __portable-build-be

build_backend:
	docker build -t $(BACKEND_IMG_H) -f backend/Dockerfile .

build_frontend:
	docker build -t $(FRONTEND_IMG_H) -f frontend/Dockerfile .

#push: push_backend push_frontend
#	@echo "Pushed to $(REG_HOST)"

push: ## Push FE+BE if registry configured (no-op otherwise)
	$(MAKE) __portable-push-fe
	$(MAKE) __portable-push-be

push_backend:
	docker push $(BACKEND_IMG_H)

push_frontend:
	docker push $(FRONTEND_IMG_H)


import-k3d: ## Import images into k3d cluster
	$(MAKE) __portable-import-k3d

print-img: ## Show effective image references
	$(MAKE) __portable-print

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

registry-config: ## Configure local registry (no-op if none defined)
	@if [ -z "$(REGISTRY_PREFIX)" ]; then \
	  echo "⟳ No REGISTRY_HOST set → registry-config skipped (no-op)"; \
	else \
	  echo "Configuring registry at $(REGISTRY_PREFIX) ..."; \
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
	fi


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

k3d-recreate: registry-config
	@echo "🧹 Deleting old k3d cluster '$(K3D_CLUSTER)' (if exists)..."
	@k3d cluster delete $(K3D_CLUSTER) >/dev/null 2>&1 || true

	@echo "🚀 Creating new k3d cluster with registry mirror..."
	k3d cluster create $(K3D_CLUSTER) \
		--api-port $(K3D_API_PORT) \
		--registry-use $(K3D_REGISTRY) \
		--registry-config registries.yaml

	@echo "📁 Setting up kubeconfig for kubectl..."
	mkdir -p $(dir $(KUBECONFIG_FILE))
	k3d kubeconfig get $(K3D_CLUSTER) | sed 's/0\.0\.0\.0/127.0.0.1/g' > $(KUBECONFIG_FILE)
	kubectl config use-context k3d-$(K3D_CLUSTER)
	kubectl create ns $(K3D_NAMESPACE) 2>/dev/null || true
	kubectl config set-context --current --namespace=$(K3D_NAMESPACE)

	@echo "✅ Cluster recreated successfully!"
	@echo "Next steps:"
	@echo "  1. make deploy"
	@echo "  2. kubectl get pods -n $(K3D_NAMESPACE) -w"

.PHONY: doctor
doctor: ## Quick sanity checks (paths, tools, cluster, registry mode)
	@echo "== Doctor =="
	@test -f frontend/package.json || { echo "❌ Missing frontend/package.json"; exit 1; }
	@test -f backend/requirements.txt || { echo "❌ Missing backend/requirements.txt"; exit 1; }
	@command -v docker >/dev/null || { echo "❌ docker not found"; exit 1; }
	@command -v helm   >/dev/null || { echo "❌ helm not found"; exit 1; }
	@command -v kubectl>/dev/null || { echo "❌ kubectl not found"; exit 1; }
	@command -v k3d    >/dev/null || echo "ℹ︎ k3d not found (ok if only building)"
	@if [ -z "$(REGISTRY_PREFIX)" ]; then \
	  echo "Mode: local, registry-free (portable)"; \
	else \
	  echo "Mode: registry = $(REGISTRY_PREFIX)"; \
	fi
	@echo "FE_IMAGE=$(FE_IMAGE)"
	@echo "BE_IMAGE=$(BE_IMAGE)"
	@echo "✅ Doctor passed"

help: 
	## Show available targets
	@echo "Anonymizer Makefile — portable mode"
	$(__PRINT_HELP)



