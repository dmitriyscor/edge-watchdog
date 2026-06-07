# Edge Watchdog

> Real-time human detection and alarm system for edge devices

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

### Edge Device

**Windows:**
```bash
python -m pip install paho-mqtt opencv-python sounddevice numpy ultralytics
```

**Linux (Jetson Nano / Ubuntu):**
```bash
pip3 install paho-mqtt opencv-python sounddevice numpy ultralytics
```

### Server

**Windows:**
```bash
python -m pip install paho-mqtt
```

**Linux:**
```bash
pip3 install paho-mqtt
```

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

## Roadmap

- [ ] Trigger video recording on all edge devices when alarm fires, to capture intruder footage
- [ ] Customizable and improved alarm sounds
- [ ] Server dashboard to monitor all connected edge devices on the network

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
