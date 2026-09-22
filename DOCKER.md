# Docker setup

These files package the current scripts; MQTT still uses their configured public
HiveMQ broker and ALARM topics. No local MQTT broker is included.

## Files

- `Dockerfile`: shared Python 3.11 base, optional `edge` target, default `server` target.
- `compose.yaml`: image names, build targets, interactive server input, camera mapping,
  and persistent data volumes.
- `.dockerignore`: only application scripts and requirements enter the build context.

## Build and run the server

Run from this repository's root with Docker running in Linux-container mode:

```sh
docker compose build server
docker compose up -d server
docker compose attach server
```

Wait for the alarm prompt and press Enter to reset. Detach without stopping the
server using Ctrl+P, then Ctrl+Q. `docker compose logs -f server` shows logs but
cannot accept reset input. Stop with `docker compose stop server`.

The working directory is `/data`, so the existing relative `captured_photos`
folder is stored in the `server-data` volume. Export photos with:

```sh
docker compose cp server:/data/captured_photos ./saved-photos
```

## Optional Linux camera container

```sh
docker compose up -d --build edge
docker compose logs -f edge
```

This explicitly selects the optional edge service without starting the server.
To start both: `docker compose --profile edge up -d --build`.
The edge container runs without a preview or sound. The first model load needs
internet access to download weights, which persist under `/data` along with photos
and model settings. Existing photos/weights on the host are not copied into images.

The Linux host's `/dev/video0` is mapped to `/dev/video0` inside the container.
Set `CAMERA_DEVICE` in your shell to select another host camera; inside the
container the index remains 0. Windows/macOS Docker Desktop camera passthrough
is not configured. On those hosts, initially run the camera script natively and
the server in Docker. This is a CPU image, not a Jetson/CUDA-specific setup.

## Image names and publishing (after testing)

Compose defaults to `local/edge-watchdog-server:v1` and
`local/edge-watchdog-edge:v1`. Set `DOCKERHUB_USERNAME` and optionally `IMAGE_TAG`
in the shell before building/pushing. `local` is only a placeholder image namespace.

PowerShell:
```powershell
$env:DOCKERHUB_USERNAME = "your-dockerhub-username"
$env:IMAGE_TAG = "v1"
```

Linux/macOS:
```sh
export DOCKERHUB_USERNAME=your-dockerhub-username
export IMAGE_TAG=v1
```

After creating the corresponding Docker Hub repository and testing locally:
```sh
docker login
docker compose build server
docker compose push server
```

Another machine with this Compose file and matching image-name variables can run:
```sh
docker compose pull server
docker compose up -d --no-build server
```

Builds target the builder's architecture by default. ARM and x86 distribution
requires appropriate platform builds; this configuration does not promise a
multi-architecture image. Edge dependency versions are not fully locked yet.

`docker compose --profile edge down` removes containers but preserves volumes.
Adding `-v` deletes the stored photos/model data.

The existing image-selection and publish-before-delete behavior is unchanged.
Container packaging does not fix those application-level issues.
