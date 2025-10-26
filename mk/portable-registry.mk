# mk/portable-registry.mk
# Portable registry & image tagging helpers for Anonymizer.
# Keeps legacy targets intact; just use provided vars & macros.

# ----- Project image names (override in outer Makefile if needed)
FE_NAME ?= anonymizer-frontend
BE_NAME ?= anonymizer-backend

# ----- Tagging
IMAGE_TAG ?= local

# ---- Neue Defaults: Dockerfile-Pfade & Kontexte ----
FE_DOCKERFILE ?= frontend/Dockerfile
BE_DOCKERFILE ?= backend/Dockerfile

FE_CONTEXT    ?= .
BE_CONTEXT    ?= .

# ----- Optional registry config
# Examples:
#   REGISTRY_HOST=k3d-registry REGISTRY_PORT=5000
#   REGISTRY_HOST=ghcr.io
#   REGISTRY_HOST=gitlab.local REGISTRY_PORT=5050
REGISTRY_HOST ?=
REGISTRY_PORT ?=

# Build an optional "<host>[:port]" prefix (empty if no host given)
REGISTRY_PREFIX := $(if $(REGISTRY_HOST),$(REGISTRY_HOST)$(if $(REGISTRY_PORT),:$(REGISTRY_PORT),),)

# Compose full image refs (with or without registry prefix)
FE_IMAGE := $(if $(REGISTRY_PREFIX),$(REGISTRY_PREFIX)/$(FE_NAME):$(IMAGE_TAG),$(FE_NAME):$(IMAGE_TAG))
BE_IMAGE := $(if $(REGISTRY_PREFIX),$(REGISTRY_PREFIX)/$(BE_NAME):$(IMAGE_TAG),$(BE_NAME):$(IMAGE_TAG))

# k3d cluster name (for imports)
K3D_CLUSTER ?= anonymizer

# Docker build contexts (override if your layout differs)
FE_DIR ?= ./frontend
BE_DIR ?= ./backend

# Dry-run: 1 = print commands only
DRY_RUN ?= 0
shx = if [ "$(DRY_RUN)" = "1" ]; then echo "+ $1"; else eval "$1"; fi

# Macro: Skip recipe if no registry configured (keeps builds green in CI)
define SKIP_IF_NO_REGISTRY
	@if [ -z "$(REGISTRY_PREFIX)" ]; then \
	  echo "⟳ No REGISTRY_HOST set → $(1) skipped (no-op)"; \
	  exit 0; \
	fi
endef

# Helpers for help target (optional)
HELP_PAD ?= 26
define __PRINT_HELP
	@awk 'BEGIN {FS=":.*?## "}; /^[a-zA-Z0-9_.-]+:.*?## / {printf "  %-$(HELP_PAD)s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
endef

# Convenience recipes you can call from legacy targets
.PHONY: __portable-build-fe __portable-build-be __portable-push-fe __portable-push-be __portable-import-k3d __portable-print

__portable-build-fe:
	@$(call shx, "docker build -t $(FE_IMAGE) -f $(FE_DOCKERFILE) $(FE_CONTEXT)")

__portable-build-be:
	@$(call shx, "docker build -t $(BE_IMAGE) -f $(BE_DOCKERFILE) $(BE_CONTEXT)")

__portable-push-fe:
	$(SKIP_IF_NO_REGISTRY,Push FE)
	@$(call shx, "docker push $(FE_IMAGE)")

__portable-push-be:
	$(SKIP_IF_NO_REGISTRY,Push BE)
	@$(call shx, "docker push $(BE_IMAGE)")

__portable-import-k3d:
	@$(call shx, "k3d image import $(FE_IMAGE) $(BE_IMAGE) -c $(K3D_CLUSTER)")

__portable-print:
	@echo "Frontend image: $(FE_IMAGE)"
	@echo "Backend  image: $(BE_IMAGE)"
	@if [ -z "$(REGISTRY_PREFIX)" ]; then \
	  echo "(local mode: no registry)"; \
	else \
	  echo "(registry: $(REGISTRY_PREFIX))"; \
	fi
