#!/usr/bin/env bash
# Build amd64 et push vers le registry privé : :latest + tag de version si HEAD est taggé (vX.Y.Z).
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE="registry.bldwebagency.fr/docker-honeypot-ssh"

TAGS=(-t "${IMAGE}:latest")
if VERSION=$(git describe --tags --exact-match HEAD 2>/dev/null); then
  TAGS+=(-t "${IMAGE}:${VERSION#v}")
  echo "==> Tag de version : ${VERSION#v}"
else
  echo "==> HEAD non taggé : push de :latest uniquement"
fi

docker buildx build --platform linux/amd64 "${TAGS[@]}" --push .
