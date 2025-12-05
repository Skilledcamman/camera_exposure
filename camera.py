import cv2
import time


class Camera:
    def __init__(self, device="/dev/video0", width=640, height=480, fps=30):
        self.device = device
        self.cap = self._open_capture(device)
        if width:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if fps:
            self.cap.set(cv2.CAP_PROP_FPS, fps)

    def _device_index(self, dev):
        # OpenCV on Linux typically maps /dev/videoN -> index N
        try:
            return int(str(dev).strip().split("video")[-1])
        except Exception:
            return 0

    def _open_capture(self, device):
        # Try opening by path with V4L2 backend first
        cap = cv2.VideoCapture(str(device), cv2.CAP_V4L2)
        if cap.isOpened():
            return cap
        # Try opening by integer index derived from path
        idx = self._device_index(device)
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if cap.isOpened():
            return cap
        # Try a few common indices
        for i in range(0, 4):
            cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
            if cap.isOpened():
                return cap
        # Final fallback without specifying backend
        cap = cv2.VideoCapture(0)
        return cap

    def mjpeg_stream(self):
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
