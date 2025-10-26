# Anonymizer

A small, containerized demo project with frontend + backend and a Helm chart for local development with k3d.
The goal is to learn modern DevOps practices (containers, registries, Kubernetes, Helm) with a compact, reproducible setup.

Status: Learning project (no deadlines, no product owner). We optimize for clarity, reproducibility, and clean code.

TL;DR

``` bash

# 1) Create a local k3d cluster (+ optional local registry)
k3d cluster create anonymizer --agents 1 --servers 1

# 2) Build images locally (no registry required)
make build   # builds anonymizer-frontend and anonymizer-backend

# 3) Load images into the k3d cluster
k3d image import anonymizer-frontend:local anonymizer-backend:local -c anonymizer

# 4) Install/upgrade the Helm chart
helm upgrade --install anonymizer charts/anonymizer \
  --namespace anonymizer --create-namespace \
  -f charts/anonymizer/values.dev.yaml

# 5) Get the service endpoint(s)
kubectl get svc -n anonymizer
```

## Architecture

``` mermaid

flowchart LR
  User["Browser"] --> FE["Frontend Container"]
  FE --> BE["Backend Container"]
  subgraph "Kubernetes (k3d)"
    FE --- BE
    class FE,BE internal
  end

```

- Frontend: serves UI (static assets or SPA).
- Backend: simple HTTP API / sockets; internal service in the cluster.
- Helm chart: charts/anonymizer (deployments, services, optional ingress).

## Repo Layout

``` text

├─ backend/
├─ frontend/
├─ charts/
│  └─ anonymizer/
│     ├─ templates/
│     ├─ values.yaml
│     ├─ values.dev.yaml
│     └─ _helpers.tpl
├─ Makefile
└─ README.md
```

### Image Workflow and Portability

This project supports exactly two registry modes:

| Mode                                 | Description                                                                                        | Typical Use                           |
| ------------------------------------ | -------------------------------------------------------------------------------------------------- | ------------------------------------- |
| **Local (k3d)**                      | Build and import images directly into your local k3d cluster. No registry or credentials required. | Fast development, debugging, learning |
| **GitHub Container Registry (GHCR)** | Push and pull images from `ghcr.io/<owner>/<repo>/<image>:<tag>`.                                  | Public or team-wide sharing           |

All other registries (Docker Hub, GitLab Registry, etc.) are intentionally unsupported to keep the setup simple and portable.

## Local Development (k3d)

### Prerequisites

- Docker or compatible runtime
- k3d + kubectl + Helm
- Make (optional but convenient)

``` bash 
make doctor
make build
make import-k3d
helm upgrade --install anonymizer charts/anonymizer \
  --namespace anonymizer --create-namespace \
  -f charts/anonymizer/values.dev.yaml
```

  This builds local images (:local or :dev) and imports them into the running k3d cluster.
Helm then deploys those images without pulling from any external registry (pullPolicy: Never).

### Push to k3d (optional)

``` bash 

export REGISTRY_HOST=localhost
export REGISTRY_PORT=5000
export IMAGE_TAG=dev1
make k3d-registry-create
make build push

```

### Push to GHCR (optional)

``` bash 
export REGISTRY_HOST=ghcr.io
export REGISTRY_PATH=<owner>/<repo>
export IMAGE_TAG=v0.1.0
export GH_USER=<user>
export GHCR_TOKEN=<token with package:write>
make ghcr-login
make build push

```

Images are tagged as
ghcr.io/<owner>/<repo>/anonymizer-frontend:v0.1.0
and
ghcr.io/<owner>/<repo>/anonymizer-backend:v0.1.0.

GitLab CI and Other CIs

GitLab pipelines build and test without any registry dependency.
The variable REGISTRY_HOST is left empty, so builds use local tags (:local) and skip push steps automatically.
This keeps CI fast and independent of external services.


To uninstall:

``` bash 

helm uninstall anonymizer -n anonymizer
```

## Configuration

Key knobs live in the Helm values:

- charts/anonymizer/values.yaml — generic defaults
- charts/anonymizer/values.dev.yaml — local dev overrides (e.g., image.pullPolicy: Never, ports)

Recommended pattern:

``` yaml

# values.dev.yaml (example)
image:
  repositoryFrontend: anonymizer-frontend
  tagFrontend: local
  repositoryBackend: anonymizer-backend
  tagBackend: local
  pullPolicy: Never

service:
  frontendPort: 80
  backendPort: 8000

ingress:
  enabled: false
```

Make Targets (typical)

``` bash 

make build         # Build both images (tags default to :local)
make build-fe      # Build frontend only
make build-be      # Build backend only
make push          # Push if REGISTRY_HOST set; otherwise no-op
make clean         # Remove local images/tarballs (safe clean)
```

Environment variables (optional):

``` bash 

REGISTRY_HOST=localhost
REGISTRY_PORT=5000
IMAGE_TAG=mytag
```

Defaults are chosen so that no vars are required for local learning.

``` yaml

name: build
on: [push, pull_request]
jobs:
  docker-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - name: Build (no push)
        run: |
          make build

```

GitLab CI (minimal)

``` yaml

stages: [build]
build:
  stage: build
  image: docker:27.0
  services: ["docker:27.0-dind"]
  script:
    - make build

```

For pushing to registries in CI, add login steps and set REGISTRY_HOST (and REGISTRY_PORT if needed).
If no registry credentials are present, the build still succeeds locally (no push).

### Security & Privacy (baseline)

- No secrets in Git: keep credentials out of repo; prefer CI secrets or local env vars.

- Helm values: keep sensitive overrides out of values*.yaml committed to Git.

- Container hardening:

  - Non-root user, minimal base images, Trivy scans (planned).
  - We will introduce these changes later to avoid blocking learning flow.


Troubleshooting

- Images not found in cluster
  - Ensure you ran k3d image import ... -c anonymizer.
  - If using a registry, check imagePullPolicy and that the cluster can reach it.

- Helm install fails on first run
  - Add --create-namespace and verify values.dev.yaml paths.

- Push errors in CI
  - Remove/pause push steps, or ensure REGISTRY_HOST + login are set.
  - The build should not fail just because no registry exists.

## Contributing

Learning-first: prefer clear commits and small diffs.
All code and comments should use English variable names and English comments.
Commit messages: imperative style (e.g., “Add Helm values for local dev”).


## License

Licensed under the MIT License

## Acknowledgements

Acknowledgements to the k3d, Helm, and Kubernetes communities,
and to everyone exploring clean DevOps with small, understandable projects.



