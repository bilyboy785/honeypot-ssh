# docker-honeypot-ssh

## Workflow (pas de CI GitHub)

À chaque nouvelle feature :
1. `scripts/test.sh` (tests locaux via Docker).
2. Commit + push sur `origin/main`.
3. Release GitHub si nécessaire : tag `vX.Y.Z` + `gh release create`.
4. `scripts/release.sh` : build amd64+arm64 et push `registry.bldwebagency.fr/docker-honeypot-ssh:latest` (+ tag de version si HEAD taggé). Lancer après le tag pour pousser aussi la version.

Ne jamais recréer de workflow GitHub Actions.
