# Camera Exposure & Gain Control (Linux)

Flask + OpenCV web app to preview a UVC camera and adjust exposure and gain using v4l2 controls on Linux.

## Prerequisites
- Linux with a UVC/USB camera (e.g., `/dev/video0`)
- `v4l2-ctl` tool (install with `sudo apt install v4l-utils`)
- Python 3.10+

On Raspberry Pi, install GStreamer for OpenCV capture:
```bash
sudo apt update
sudo apt install -y gstreamer1.0-tools gstreamer1.0-libav gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional environment variables:
- `CAMERA_DEVICE` (default `/dev/video0`)
- `FLASK_HOST` (default `0.0.0.0`)
- `FLASK_PORT` (default `5000`)
- `FLASK_DEBUG` (default `1`)

## Run
```bash
export CAMERA_DEVICE=/dev/video0
python app.py
```
Open `http://localhost:5000` in your browser.

## Notes
- Controls rely on `v4l2-ctl`. Exposure items may vary by camera (e.g., `exposure_auto`, `exposure_absolute`).
- You may need permissions: add your user to `video` group and re-login.
```bash
sudo usermod -a -G video "$USER"
```
- If exposure sliders do not reflect actual ranges, read `/api/controls` output and adjust UI accordingly.
- On Raspberry Pi, the app attempts a GStreamer pipeline `v4l2src device=/dev/video0 ! jpegdec ! videoconvert ! appsink`. Ensure the plugins above are installed.

## Test harness
List current controls:
```bash
v4l2-ctl -l
```
Set example values:
```bash
v4l2-ctl -c exposure_auto=1
v4l2-ctl -c exposure_absolute=200
v4l2-ctl -c gain=32
```
