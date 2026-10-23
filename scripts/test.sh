#!/usr/bin/env bash
# Tests locaux via Docker : lint Dockerfile, syntaxe/import Python, build amd64.
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE="docker-honeypot-ssh:test"

echo "==> Lint Dockerfile (hadolint)"
docker run --rm -i hadolint/hadolint < Dockerfile

echo "==> Build ${IMAGE} (linux/amd64)"
docker build --platform linux/amd64 -t "$IMAGE" .

echo "==> Syntaxe Python"
docker run --rm --platform linux/amd64 "$IMAGE" python -m py_compile /app/honeypot.py

echo "==> Import Python"
docker run --rm --platform linux/amd64 -w /app "$IMAGE" python -c "import honeypot"

echo "==> Tests OK"
