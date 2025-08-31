# anonymizer (Helm Chart)

Minimal chart to deploy the anonymizer frontend + backend to Kubernetes.

## Install
```bash
helm repo add anonymizer https://<your-gh-username>.github.io/anonymizer-helm
helm install anonymizer anonymizer/anonymizer --version 1.0.0
```

## Values (excerpt)
```yaml
image:
  registry: ghcr.io/<user>
  backend:
    repository: anonymizer-backend
    tag: "1.0.0"
  frontend:
    repository: anonymizer-frontend
    tag: "1.0.0"

ingress:
  enabled: true
  className: nginx
  host: anonymizer.local
```

## Notes
- Frontend proxies `/api` to the backend Service `backend:8000` inside the cluster.
- Backend PVC stores the mapping file (or configure `MAP_PATH`).
