<p align="center">
  <img src="./title.svg" alt="Edge Watchdog" />
</p>

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![YOLOv5](https://img.shields.io/badge/YOLOv5-Detection-red?style=flat-square)
![MQTT](https://img.shields.io/badge/MQTT-WebSockets-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

## 📖 Overview

Edge Watchdog provides a distributed architecture consisting of a security system that provides the detection of humans on Edge devices in real-time. Each of the edge devices executes a detection pipeline consisting of YOLOv5 on an edge device, and communicate with a central server via MQTT. Upon detection of a person, the server autonomously activates alarms on all connected devices. Applications for the system include home security, property surveillance, and perimeter monitoring.

---

## 🏗️ Architecture

### 🖥️ Edge Device
Each edge device continuously captures frames from the video input stream and runs a YOLOv5 human detection tuned model on the frames. When a person is detected, the edge device immediately transmits the relevant frame to the server. The edge device will also freeze frame capture and activate a local alarm until it receives a command to reset from the server.

### ☁️ Server
The server has one responsibility: alarm control. When the server receives an image, it will store the image locally with a timestamp and send a broadcast to all connected edge devices that an alarm has been triggered. The alarm must be reset manually by pressing the `Enter` key; there is no automated path to dismiss an alarm.

---

## ⚙️ Setup

The same scripts work on Windows, Linux, and macOS with Paho MQTT 2.x.
Run these commands from the repository root, using your activated virtual environment.

### Install and run

**Windows (PowerShell):**
```powershell
python -m pip install -r server/requirements.txt
python server/mqtt-broker.py
# On the camera machine:
python -m pip install -r edge/requirements.txt
python edge/mqtt-client.py
```

**Linux / macOS:**
```sh
python3 -m pip install -r server/requirements.txt
python3 server/mqtt-broker.py
# On the camera machine:
python3 -m pip install -r edge/requirements.txt
python3 edge/mqtt-client.py
```

The edge script selects DirectShow on Windows and OpenCV's default backend on
Linux/macOS. Camera index defaults to **0** on all systems; set `CAMERA_INDEX=1`
if your camera is device 1. Grant camera access to your terminal when prompted.

### Optional settings

| Variable | Default | Meaning |
|----------|---------|---------|
| `CAMERA_INDEX` | `0` | Camera device index; depends on your hardware |
| `AUDIO_ENABLED` | `0` | Set to `1` to enable the local alarm speaker |
| `HEADLESS` | `0` | Set to `1` to disable the preview window |
| `MQTT_CLIENT_ID` | Generated per run | Optional explicit ID; must be unique per running process |

Example for a second camera with audio:

**Windows (PowerShell):**
```powershell
python -m pip install sounddevice numpy
$env:CAMERA_INDEX = "1"
$env:AUDIO_ENABLED = "1"
python edge/mqtt-client.py
```

**Linux / macOS:**
```sh
python3 -m pip install sounddevice numpy
CAMERA_INDEX=1 AUDIO_ENABLED=1 python3 edge/mqtt-client.py
```

Audio is optional on every platform. Linux may additionally need its distribution's
PortAudio runtime package. If audio initialization or playback fails, the client
reports the problem and continues without sound. A Linux machine without a display
should use `HEADLESS=1`. Press Ctrl+C to stop; `q` also exits the active preview
when the client is not paused by an alarm.

Run one alarm server and any number of edge clients. Photos are stored in
`captured_photos` relative to the directory you run the command from.
The server uses a plain-text reset prompt compatible with Windows terminals.

---

## 🌐 Network Setup

Communication is handled via **MQTT over WebSockets** using the HiveMQ public broker.  
For private deployments across different networks, use **[Hamachi VPN](https://vpn.net/)** to create a shared virtual LAN between all devices.

| Protocol | Port | Encryption |
|----------|------|------------|
| MQTT TCP | 1883 | None |
| MQTT TLS | 8883 | TLS/SSL |
| WebSockets | 8000 | None |
| WebSockets (WSS) | 8884 | TLS/SSL |

---

## Docker

Install and start Docker before running these commands. Docker downloads
the images automatically if they are not already available locally.
Python and application dependencies are included.

### Server

```sh
docker run -it --init --name edge-watchdog-server -v watchdog-photos:/data dmygzh/edge-watchdog-server:v1
```

Press **Enter** in the server terminal when prompted to reset an alarm.
Detach without stopping the server using **Ctrl+P, then Ctrl+Q**.

Photos persist in the `watchdog-photos` Docker volume.

### Camera client — native Linux host

Requires a camera available at `/dev/video0` and a compatible image
architecture. Windows/macOS Docker Desktop webcam access requires
additional configuration.

```sh
docker run -d --init --name edge-watchdog-edge --device=/dev/video0:/dev/video0 -v watchdog-edge-data:/data dmygzh/edge-watchdog-edge:v1
```

The client runs without a preview window or sound. Model weights download
on first use, requiring internet access, and persist in `watchdog-edge-data`.

View client output:

```sh
docker logs -f edge-watchdog-edge
```

### Stop and restart

Stop the containers:

```sh
docker stop edge-watchdog-server
docker stop edge-watchdog-edge
```

Restart existing containers instead of repeating `docker run`:

```sh
docker start -ai edge-watchdog-server
docker start edge-watchdog-edge
```

### Current limitations

Both applications use a public MQTT broker and shared alarm topics.
Separate deployments are not isolated from each other.

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
