# honeypot-ssh

Minimal SSH honeypot: presents a real SSH handshake (banner + key exchange via paramiko), always rejects authentication, and logs every attempt (IP, port, method) — no shell session is ever opened.

Built to sit in front of port 22 and feed a **fail2ban** jail via a custom filter (included in the repo).

**Repo / full docs**: https://github.com/bilyboy785/honeypot-ssh

## Quick start

```bash
docker run -d \
  --name ssh-honeypot \
  -p 22:22 \
  -v ./data/log:/data/log \
  -v ./data/hostkey:/data/hostkey \
  --restart unless-stopped \
  martinbouillaud/honeypot-ssh:latest
```

Or with `docker-compose.yml`:

```yaml
services:
  ssh-honeypot:
    image: martinbouillaud/honeypot-ssh:latest
    container_name: ssh-honeypot
    restart: unless-stopped
    ports:
      - "22:22"
    volumes:
      - ./data/log:/data/log
      - ./data/hostkey:/data/hostkey
```

## Volumes

| Path | Content |
|---|---|
| `/data/log` | `honeypot.log` — one line per auth attempt |
| `/data/hostkey` | RSA host key, persisted across restarts |

## Log format

```
2026-07-28T21:14:02Z sshd-honeypot: Failed password for root from 203.0.113.42 port 51422 ssh2 (password)
```

Matches the standard `sshd` fail2ban log format (`Failed password for <user> from <HOST> port <port> ssh2`). Example filter + jail included in the GitHub repo.

## Security

- Container runs as root (required to bind port 22 / `CAP_NET_BIND_SERVICE`)
- Never run this on the same port as a real sshd
- Isolate this container (dedicated network, no other service exposed on it)

## Tags

- `latest` — last build from `main`
- `sha-xxxxxxx` — per-commit build
- `X.Y.Z` — tagged releases `vX.Y.Z`
