#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || realpath "$SCRIPT_DIR/../..")"
source "$REPO_ROOT/scripts/lib/common.sh"

NS=anonymizer
VALUES="$REPO_ROOT/charts/anonymizer/values.prod.yaml"

helm upgrade -i anonymizer "$REPO_ROOT/charts/anonymizer" \
  -n "$NS" -f "$VALUES" --atomic --wait --timeout 5m

