import paho.mqtt.client as mqtt
import base64
import os
import platform
import uuid
import time
import cv2
from datetime import datetime
from ultralytics import YOLO


alarm_status = False

# -----------------------------
# CAMERA / YOLO SETTINGS
# -----------------------------

SYSTEM = platform.system()
# Camera numbering depends on your hardware, not your operating system.
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
AUDIO_ENABLED = os.getenv("AUDIO_ENABLED", "0") == "1"
HEADLESS = os.getenv("HEADLESS", "0") == "1"

if AUDIO_ENABLED:
    try:
        import sounddevice as sd
        import numpy as np
    except (ImportError, OSError) as error:
        print(f"Audio disabled: {error}")
        AUDIO_ENABLED = False

MODEL_NAME = "yolov5nu.pt"
CONFIDENCE_THRESHOLD = 0.80
YOLO_IMAGE_SIZE = 224
PROCESS_EVERY_N_FRAMES = 3

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

PHOTO_COOLDOWN_SECONDS = 5
PHOTO_FOLDER = "captured_photos"

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def beep(frequency=555, duration_ms=460):
    global AUDIO_ENABLED
    if not AUDIO_ENABLED:
        return
    try:
        sample_rate = 44100
        t = np.linspace(0, duration_ms / 1000,
                        int(sample_rate * duration_ms / 1000), False)
        wave = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
        sd.play(wave, sample_rate)
        sd.wait()
    except Exception as error:
        print(f"Audio disabled after playback error: {error}")
        AUDIO_ENABLED = False


def open_camera(index):
    if SYSTEM == "Windows":
        return cv2.VideoCapture(index, cv2.CAP_DSHOW)
    return cv2.VideoCapture(index)


def create_filename():
    """
    Creates a photo filename using date and time.
    Example: human_2026-05-19_15-42-10.jpg
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"human_{timestamp}.jpg"


def on_message(client, userdata, message):
    global alarm_status

    payload = message.payload.decode("utf-8").strip()
    print(f"Received message on {message.topic}: {payload}")

    if message.topic == "ALARM/STATUS":
        if payload == "1":
            alarm_status = 1
        else:
            alarm_status = 0


def publish_image(client):
    images = sorted(os.listdir(PHOTO_FOLDER))

    if not images:
        print("No images found, skipping.")
        return

    filepath = os.path.join(PHOTO_FOLDER, images[0])

    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    client.publish("ALARM/IMAGE", encoded, qos=1)
    print(f"Published image: {filepath}")

    os.remove(filepath)
    print(f"Deleted: {filepath}")


# -----------------------------
# MQTT CONNECTION SETTINGS
# -----------------------------

mqttBroker = "broker.hivemq.com"
websocket_path = "/mqtt"
websocket_port = 8000

# SHARED — works on Linux, macOS, and Windows with Paho 2.x.
# Use a different client_id for each simultaneously running edge device.
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id=os.getenv("MQTT_CLIENT_ID") or f"ew-edge-{uuid.uuid4().hex[:16]}",
    transport="websockets",
)

client.ws_set_options(path=websocket_path)
client.on_message = on_message

# Topics:
# ALARM/IMAGE  — outgoing images
# ALARM/STATUS — turning the alarm on/off

print("Connecting to broker via WebSockets...")

try:
    client.connect(mqttBroker, port=websocket_port)
    client.loop_start()
    client.subscribe("ALARM/STATUS")
    print("Successfully connected and loop started!")

except Exception as e:
    print(f"Connection failed: {e}")
    raise SystemExit(1)


# -----------------------------
# MODEL AND CAMERA SETUP
# -----------------------------

os.makedirs(PHOTO_FOLDER, exist_ok=True)

print("Loading YOLO model...")
model = YOLO(MODEL_NAME)

print("Opening USB camera...")

print(f"Detected system: {SYSTEM}; camera index: {CAMERA_INDEX}")
cap = open_camera(CAMERA_INDEX)

if not cap.isOpened():
    print("Error: Could not open USB camera.")
    print("Try another CAMERA_INDEX, such as 0 or 1.")
    raise SystemExit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)

frame_count = 0
last_boxes = []
last_photo_time = 0

print("Edge human photo sender started.")


# -----------------------------
# DETECTION LOOP
# -----------------------------

try:
    while True:
        if alarm_status:
            print("Alarm is currently ON. Waiting for status reset...")
            time.sleep(1)

            beep(555, 1000)

            continue

        ret, frame = cap.read()

        if not ret:
            print("Error: Could not read camera frame.")
            break

        frame_count += 1

        if frame_count % PROCESS_EVERY_N_FRAMES == 0:
            results = model(
                frame,
                imgsz=YOLO_IMAGE_SIZE,
                conf=CONFIDENCE_THRESHOLD,
                classes=[0],  # COCO class 0 = person
                verbose=False,
            )

            last_boxes = []
            human_detected = False
            tooClose = False  # TODO: implement proximity logic.

            for result in results:
                for box in result.boxes:
                    confidence = float(box.conf[0])

                    if confidence >= CONFIDENCE_THRESHOLD:
                        human_detected = True
                        x1, y1, x2, y2 = box.xyxy[0]

                        last_boxes.append(
                            (
                                int(x1),
                                int(y1),
                                int(x2),
                                int(y2),
                                confidence,
                            )
                        )

            current_time = time.time()

            if (
                human_detected
                and current_time - last_photo_time
                >= PHOTO_COOLDOWN_SECONDS
            ):
                if tooClose:
                    print(
                        "PERSON IS TOO CLOSE TO THE EDGE! "
                        "PLAY SOUND ON THIS DEVICE!"
                    )
                else:
                    filename = create_filename()
                    image_path = os.path.join(PHOTO_FOLDER, filename)

                    cv2.imwrite(image_path, frame)
                    print(f"Human detected! Saved: {image_path}")

                    publish_image(client)
                    last_photo_time = current_time
            else:
                print("No person detected")

        # Draw detection boxes.
        for x1, y1, x2, y2, confidence in last_boxes:
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Human {confidence:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

        if not HEADLESS:
            cv2.imshow("Edge Client - Human Detector", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

except KeyboardInterrupt:
    print("\nDisconnecting...")

finally:
    cap.release()
    if not HEADLESS:
        cv2.destroyAllWindows()
    client.loop_stop()
    client.disconnect()