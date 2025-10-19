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
BACKEND_IMG_C  := $(CLUSTER_REG)/anonymizer-backend:$(TAG)
FRONTEND_IMG_C := $(CLUSTER_REG)/anonymizer-frontend:$(TAG)

# -------- Targets --------
.PHONY: all build push deploy restart logs pf clean print-vars 

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

deploy:
	helm upgrade --install $(RELEASE) $(CHART) -n $(NS) \
	  --reset-values \
	  -f $(CHART)/values.dev.yaml \
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
