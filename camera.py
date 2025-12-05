import cv2
import time
import subprocess
import os



class Camera:
    def __init__(self, device="/dev/video0", width=640, height=480, fps=30):
        self.device = device
        self.cap = self._open_capture(device)
        self.ffmpeg = None
        if not self.cap or not getattr(self.cap, 'isOpened', lambda: False)():
            self.cap = None
            self.ffmpeg = self._open_ffmpeg(device, width, height, fps)
        if width:
            if self.cap:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height:
            if self.cap:
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if fps:
            if self.cap:
                self.cap.set(cv2.CAP_PROP_FPS, fps)

    def _device_index(self, dev):
        # OpenCV on Linux typically maps /dev/videoN -> index N
        try:
            return int(str(dev).strip().split("video")[-1])
        except Exception:
            return 0

    def _open_capture(self, device):
        # Try GStreamer pipeline first (more reliable on Raspberry Pi)
        gst_pipeline = self._build_gstreamer_pipeline(device)
        if gst_pipeline:
            cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            if cap.isOpened():
                print(f"Opened camera via GStreamer: {gst_pipeline}")
                return cap
        # Try opening by path with V4L2 backend
        cap = cv2.VideoCapture(str(device), cv2.CAP_V4L2)
        if cap.isOpened():
            print(f"Opened camera via V4L2 path: {device}")
            return cap
        # Try opening by integer index derived from path
        idx = self._device_index(device)
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if cap.isOpened():
            print(f"Opened camera via V4L2 index: {idx}")
            return cap
        # Try a few common indices
        for i in range(0, 4):
            cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
            if cap.isOpened():
                print(f"Opened camera via fallback index: {i}")
                return cap
        # Final fallback without specifying backend
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("Opened camera via final fallback index 0")
        return cap

    def _build_gstreamer_pipeline(self, device):
        # Detect supported formats to choose MJPEG or YUY2
        try:
            out = subprocess.run([
                "v4l2-ctl", "-d", str(device), "--list-formats-ext"
            ], capture_output=True, text=True, check=True).stdout.lower()
        except Exception:
            out = ""
        use_mjpeg = "mjpeg" in out or "jpeg" in out
        if use_mjpeg:
            return f"v4l2src device={device} ! image/jpeg,framerate=30/1 ! jpegdec ! videoconvert ! appsink"
        # Default to YUY2 raw if MJPEG not available
        return f"v4l2src device={device} ! video/x-raw,format=YUY2,framerate=30/1 ! videoconvert ! appsink"

    def _open_ffmpeg(self, device, width, height, fps):
        # Use ffmpeg to grab frames and output as MJPEG to stdout
        ffmpeg = [
            'ffmpeg',
            '-hide_banner', '-loglevel', 'warning',
            '-f', 'v4l2', '-framerate', str(fps), '-video_size', f'{width}x{height}', '-i', str(device),
            '-vf', 'format=yuv420p',
            '-f', 'image2pipe', '-vcodec', 'mjpeg', '-'
        ]
        try:
            proc = subprocess.Popen(ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Opened camera via FFmpeg pipe: {' '.join(ffmpeg)}")
            return proc
        except Exception as e:
            print(f"FFmpeg fallback failed: {e}")
            return None

    def mjpeg_stream(self):
        if self.cap:
            while True:
                ok, frame = self.cap.read()
                if not ok or frame is None:
                    time.sleep(0.05)
                    continue
                ok, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if not ok:
                    continue
                buf = encoded.tobytes()
                header = b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(buf)).encode() + b"\r\n\r\n"
                yield header + buf + b"\r\n"
        elif self.ffmpeg and self.ffmpeg.stdout:
            # Parse individual JPEG images from FFmpeg stdout
            buffer = b''
            try:
                while True:
                    chunk = self.ffmpeg.stdout.read(4096)
                    if not chunk:
                        time.sleep(0.01)
                        continue
                    buffer += chunk
                    # Look for JPEG start/end markers
                    start = buffer.find(b'\xff\xd8')
                    end = buffer.find(b'\xff\xd9')
                    if start != -1 and end != -1 and end > start:
                        jpeg = buffer[start:end+2]
                        buffer = buffer[end+2:]
                        header = b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
                        yield header + jpeg + b"\r\n"
            finally:
                try:
                    self.ffmpeg.terminate()
                except Exception:
                    pass
