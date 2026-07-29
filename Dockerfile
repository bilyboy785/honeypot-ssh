FROM python:3.13-alpine3.24

RUN pip install --no-cache-dir paramiko==5.0.0

WORKDIR /app
COPY honeypot.py /app/honeypot.py

VOLUME ["/data/log", "/data/hostkey"]

EXPOSE 22

# Runs as root: binding to port 22 requires CAP_NET_BIND_SERVICE.
CMD ["python", "/app/honeypot.py"]
