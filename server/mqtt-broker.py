import paho.mqtt.client as mqtt
import time
import base64
import os
import platform
import uuid

alarm_status = 0
os.makedirs("captured_photos", exist_ok=True)


def on_message(client, userdata, message):
    global alarm_status

    if message.topic == "ALARM/IMAGE":
        encoded = message.payload.decode("utf-8")
        img_bytes = base64.b64decode(encoded)

        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"captured_photos/{timestamp}.jpg"

        with open(filename, "wb") as f:
            f.write(img_bytes)

        print(f"Image saved: {filename}")

        alarm_status = 1
        Publish(client, 1)


def Publish(client, status):
    client.publish("ALARM/STATUS", status)
    print(f"Just published {status} to topic ALARM/STATUS")


# -----------------------------
# MQTT CONNECTION SETTINGS
# -----------------------------

mqttBroker = "broker.hivemq.com"
websocket_port = 8000
websocket_path = "/mqtt"

# This script uses MQTT over WebSockets.
# For TLS, additional TLS configuration is required.

# Paho 2.x uses the same API on Windows, Linux, and macOS.
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id=os.getenv("MQTT_CLIENT_ID") or f"ew-server-{uuid.uuid4().hex[:16]}",
    transport="websockets",
)

client.ws_set_options(path=websocket_path)
client.on_message = on_message

# Topics:
# ALARM/IMAGE  — incoming images
# ALARM/STATUS — turning the alarm on/off

print(f"Detected system: {platform.system()}")
print("Connecting to broker via WebSockets...")

try:
    client.connect(mqttBroker, port=websocket_port)
    client.loop_start()
    client.subscribe("ALARM/IMAGE")
    print("Successfully connected and loop started!")

except Exception as e:
    print(f"Connection failed: {e}")
    raise SystemExit(1)


# -----------------------------
# ALARM RESET LOOP
# -----------------------------

try:
    while True:
        if alarm_status == 1:
            print("Alarm is ON. Press Enter to acknowledge and reset.")

            input()
            alarm_status = 0
            Publish(client, 0)
            print("Alarm acknowledged and reset.")
        else:
            time.sleep(1)

except KeyboardInterrupt:
    print("\nDisconnecting...")
finally:
    client.loop_stop()
    client.disconnect()