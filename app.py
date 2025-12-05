import os
import subprocess
from flask import Flask, render_template, Response, jsonify, request
from camera import Camera

app = Flask(__name__)
camera = Camera(device=os.environ.get("CAMERA_DEVICE", "/dev/video0"))


def run_v4l2_ctl(args):
    try:
        result = subprocess.run(["v4l2-ctl"] + args, capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return False, str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stream")
def stream():
    return Response(camera.mjpeg_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.get("/health")
def health():
    ok = camera.cap.isOpened()
    return jsonify({"camera_opened": bool(ok)})


@app.get("/api/controls")
def get_controls():
    ok, out = run_v4l2_ctl(["-l"])
    if not ok:
        return jsonify({"error": out}), 500
    # Parse minimal controls: exposure, gain
    controls = {}
    for line in out.splitlines():
        # Example: exposure_absolute (int)    : min=1 max=10000 step=1 default=156 value=156
        if "exposure" in line or "gain" in line:
            controls[line.split("(")[0].strip()] = line
    return jsonify({"raw": out, "summary": controls})


@app.post("/api/controls")
def set_controls():
    data = request.json or {}
    responses = {}
    for key in ["exposure_absolute", "exposure_auto", "gain", "brightness"]:
        if key in data:
            # Clamp exposure to >= 1 since v4l2 expects positive
            if key == "exposure_absolute":
                try:
                    v = int(data[key])
                except Exception:
                    v = 1
                if v < 1:
                    v = 1
                val = str(v)
            else:
                val = str(data[key])
            ok, out = run_v4l2_ctl(["-c", f"{key}={val}"])
            responses[key] = {"ok": ok, "out": out}
    status = 200 if all(r.get("ok") for r in responses.values()) else 400
    return jsonify(responses), status


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug, threaded=True)
