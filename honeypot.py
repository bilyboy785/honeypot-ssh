"""Fake SSH server that logs every authentication attempt for fail2ban."""

import logging
import socket
import threading
import time
from pathlib import Path

import paramiko

HOST_KEY_PATH = Path("/data/hostkey/ssh_host_rsa_key")
LOG_PATH = Path("/data/log/honeypot.log")
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 22
BANNER = "SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13.5"


def get_or_create_host_key() -> paramiko.RSAKey:
    HOST_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if HOST_KEY_PATH.exists():
        return paramiko.RSAKey(filename=str(HOST_KEY_PATH))
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(str(HOST_KEY_PATH))
    return key


def log_attempt(client_ip: str, client_port: int, username: str, auth_method: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = (
        f"{timestamp} sshd-honeypot: Failed password for "
        f"{username or 'unknown'} from {client_ip} port {client_port} ssh2 ({auth_method})"
    )
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")
    logging.info(line)


class HoneypotServer(paramiko.ServerInterface):
    def __init__(self, client_ip: str, client_port: int):
        self.client_ip = client_ip
        self.client_port = client_port

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auths(self, username):
        return "password,publickey"

    def check_auth_password(self, username, password):
        log_attempt(self.client_ip, self.client_port, username, "password")
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        log_attempt(self.client_ip, self.client_port, username, "publickey")
        return paramiko.AUTH_FAILED

    def check_auth_none(self, username):
        return paramiko.AUTH_FAILED


def handle_connection(client_sock: socket.socket, addr, host_key: paramiko.RSAKey) -> None:
    client_ip, client_port = addr
    transport = None
    try:
        transport = paramiko.Transport(client_sock)
        transport.local_version = BANNER
        transport.add_server_key(host_key)
        server = HoneypotServer(client_ip, client_port)
        transport.start_server(server=server)
        transport.accept(20)
    except (paramiko.SSHException, EOFError, ConnectionResetError, OSError) as exc:
        logging.debug("connection error from %s: %s", client_ip, exc)
    finally:
        if transport is not None:
            transport.close()
        client_sock.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    host_key = get_or_create_host_key()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((LISTEN_HOST, LISTEN_PORT))
    sock.listen(100)
    logging.info("SSH honeypot listening on %s:%s", LISTEN_HOST, LISTEN_PORT)

    while True:
        client_sock, addr = sock.accept()
        thread = threading.Thread(
            target=handle_connection, args=(client_sock, addr, host_key), daemon=True
        )
        thread.start()


if __name__ == "__main__":
    main()
