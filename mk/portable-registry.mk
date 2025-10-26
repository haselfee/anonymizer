# mk/portable-registry.mk
# Portable registry & image tagging helpers for Anonymizer.
# Keeps legacy targets intact; just use provided vars & macros.

# --- allow-list ---
ALLOWED_REGISTRY_HOSTS := ghcr.io k3d-registry localhost

# Optional path for ghcr: <owner>/<repo>
REGISTRY_PATH ?=

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

# Build prefix: <host>[:port][/path]
# ghcr: no port; k3d: with port; local: empty
define __mk_prefix
$(if $(REGISTRY_HOST),\
  $(REGISTRY_HOST)$(if $(REGISTRY_PORT),:$(REGISTRY_PORT),)$(if $(REGISTRY_PATH),/$(REGISTRY_PATH),),)
endef
REGISTRY_PREFIX := $(call __mk_prefix)

# Gate: enforce allowed registries (or empty = local)
ifneq ($(strip $(REGISTRY_HOST)),)
  ifeq (,$(filter $(REGISTRY_HOST),$(ALLOWED_REGISTRY_HOSTS)))
    $(error Registry host '$(REGISTRY_HOST)' is not allowed. Use one of: $(ALLOWED_REGISTRY_HOSTS))
  endif
endif

# Images
FE_IMAGE := $(if $(REGISTRY_PREFIX),$(REGISTRY_PREFIX)/$(FE_NAME):$(IMAGE_TAG),$(FE_NAME):$(IMAGE_TAG))
BE_IMAGE := $(if $(REGISTRY_PREFIX),$(REGISTRY_PREFIX)/$(BE_NAME):$(IMAGE_TAG),$(BE_NAME):$(IMAGE_TAG))


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

# Convenience logins
.PHONY: ghcr-login k3d-registry-create
ghcr-login: ## docker login ghcr.io with GHCR_TOKEN (classic token or PAT with package:write)
	@test -n "$$GHCR_TOKEN" || { echo "Set GHCR_TOKEN first"; exit 1; }
	echo "$$GHCR_TOKEN" | docker login ghcr.io -u $$GH_USER --password-stdin

k3d-registry-create: ## create local k3d registry if missing
	-k3d registry create k3d-registry --port 5000 || true

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
