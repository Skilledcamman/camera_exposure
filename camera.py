import cv2
import time


class Camera:
    def __init__(self, device="/dev/video0", width=640, height=480, fps=30):
        self.device = device
        self.cap = cv2.VideoCapture(self._device_index(device))
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

    def mjpeg_stream(self):
        while True:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.02)
                continue
            ok, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ok:
                continue
            buf = encoded.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buf + b"\r\n")
