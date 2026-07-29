# honey-pot-ssh

Honeypot SSH minimaliste. Le container ouvre un vrai handshake SSH (banner + échange de clés + négociation d'auth via [paramiko](https://www.paramiko.org/)), refuse systématiquement toute authentification, et logge chaque tentative (IP source, port, méthode d'auth) dans un fichier exploitable par fail2ban.

Aucune session shell n'est jamais ouverte : la connexion s'arrête à l'étape d'authentification.

## CI/CD

`.github/workflows/ci.yml` : sur chaque PR/push, lint Dockerfile (hadolint) + vérif syntaxe/import Python + build. Sur push vers `main` ou tag `v*`, build et push l'image vers Docker Hub (`bilyboy785/honeypot-ssh`).

Secrets requis dans le repo GitHub (Settings → Secrets and variables → Actions) :
- `DOCKER_HUB_USERNAME` — username Docker Hub
- `DOCKER_HUB_TOKEN` — access token Docker Hub (Account Settings → Security → New Access Token)

## Architecture

- `honeypot.py` — serveur SSH factice (thread par connexion, clé hôte RSA persistée)
- `Dockerfile` — image `python:3.12-alpine` + paramiko
- `docker-compose.yml` — expose le port 22, monte les volumes de logs et de clé hôte
- `examples/filter.d/sshd-honeypot.conf` — filtre fail2ban
- `examples/jail.d/sshd-honeypot.local` — jail fail2ban d'exemple
- `examples/sample.log` — extrait de log pour tester le filtre
- `examples/docker-compose.yml` — variante utilisant l'image publiée sur Docker Hub (pas de build local)

## Démarrage

Build local :

```bash
docker compose up -d --build
```

Ou via l'image publiée sur Docker Hub (voir `examples/docker-compose.yml`) :

```bash
docker compose -f examples/docker-compose.yml up -d
```

Le port 22 de l'hôte est redirigé vers le container. Si un vrai sshd tourne sur cette même machine, changez le port hôte dans `docker-compose.yml` (ex. `"2222:22"`) et redirigez le trafic voulu via iptables/nftables plutôt que d'exposer 22 en direct.

Logs et clé hôte persistent dans `./data/log/honeypot.log` et `./data/hostkey/`.

## Format de log

```
2026-07-28T21:14:02Z sshd-honeypot: Failed password for root from 203.0.113.42 port 51422 ssh2 (password)
```

Compatible avec le format `sshd` standard attendu par fail2ban (`Failed password for <user> from <HOST> port <port> ssh2`), avec suffixe `(password|publickey)` indiquant la méthode tentée.

## Installation fail2ban

1. Copier le filtre et la jail :

```bash
sudo cp examples/filter.d/sshd-honeypot.conf /etc/fail2ban/filter.d/
sudo cp examples/jail.d/sshd-honeypot.local /etc/fail2ban/jail.d/
```

2. Adapter `logpath` dans `sshd-honeypot.local` au chemin réel de `data/log/honeypot.log` sur l'hôte.

3. Redémarrer fail2ban :

```bash
sudo systemctl restart fail2ban
sudo fail2ban-client status sshd-honeypot
```

### Tester le filtre sans attendre une vraie attaque

```bash
sudo fail2ban-regex examples/sample.log examples/filter.d/sshd-honeypot.conf
```

## Tester le honeypot

```bash
ssh -p 22 root@<host-ip>
# n'importe quel mot de passe → toujours refusé, mais loggé
```

## Notes sécurité

- Le container tourne en root pour pouvoir bind le port 22 (`CAP_NET_BIND_SERVICE`). Isoler ce container (réseau dédié, pas d'autre service exposé dessus).
- Ne jamais faire tourner ce honeypot sur le même port que le vrai sshd de la machine.
- Rotation des logs : brancher `logrotate` sur `data/log/honeypot.log` si volume d'attaques élevé (le service Docker limite déjà les logs du daemon via `json-file` `max-size`/`max-file`, mais pas le fichier applicatif).
