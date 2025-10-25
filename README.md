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
  User[(Browser)] --> FE[Frontend (Container)]
  FE --> BE[Backend (Container)]
  subgraph Kubernetes (k3d)
    FE --- BE
    class FE,BE internal;
  end
```

- Frontend: serves UI (static assets or SPA).
- Backend: simple HTTP API / sockets; internal service in the cluster.
- Helm chart: charts/anonymizer (deployments, services, optional ingress).

## Repo Layout

``` pgsql

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

## Local Development
### Prerequisites

- Docker or compatible runtime
- k3d + kubectl + Helm
- Make (optional but convenient)

## Build & Load (no registry)

We default to a registry-free developer flow to avoid CI breakage:

``` bash

# Tag with :local and skip registry pushes
make build           # produces anonymizer-frontend:local, anonymizer-backend:local
k3d image import anonymizer-frontend:local anonymizer-backend:local -c anonymizer
```

Install via Helm
``` bash 

helm upgrade --install anonymizer charts/anonymizer \
  --namespace anonymizer --create-namespace \
  -f charts/anonymizer/values.dev.yaml
```
To uninstall:
``` bash 

helm uninstall anonymizer -n anonymizer
```

## Images & Registries

This project supports three modes:

1. Registry-free (default for learning):

  - Build with local tags (:local), import into k3d.

2. Local k3d registry (optional):

- If you create k3d-registry:5000, set:
``` bash 
  REGISTRY_HOST=k3d-registry
  REGISTRY_PORT=5000
  make build push

```

3. Remote registries (GitHub/GitLab):

- Provide REGISTRY_HOST, optional REGISTRY_PORT, and credentials (via docker login or CI secrets).

- Example tags: ghcr.io/<org>/<repo>/<name>:<tag> or gitlab.local:5050/<group>/<project>/<name>:<tag>.

The Makefile is designed to not fail if no registry is configured; it will still produce :local images.

---

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
``` bash 

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

Anonymizer is licensed under MIT 

## Acknowledgements

k3d, Helm, Kubernetes communities

Everyone exploring clean DevOps with small, understandable projects



