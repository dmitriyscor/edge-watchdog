# Shared Python runtime; application data is written relative to /data.
FROM python:3.11-slim-bookworm AS base
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /data

# Optional CPU-based camera client for a Linux host.
FROM base AS edge
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY edge/requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt
COPY edge/mqtt-client.py /app/mqtt-client.py
ENV HEADLESS=1 AUDIO_ENABLED=0 YOLO_CONFIG_DIR=/data/ultralytics
CMD ["python", "/app/mqtt-client.py"]

# Default target: alarm server, with no camera/ML dependencies.
FROM base AS server
COPY server/requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt
COPY server/mqtt-broker.py /app/mqtt-broker.py
CMD ["python", "/app/mqtt-broker.py"]
