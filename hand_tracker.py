"""
Buoc 1-2 cua pipeline: Camera -> MediaPipe -> Du lieu.

Lop HandTracker boc MediaPipe Hand Landmarker (Tasks API).
Dau vao : 1 frame anh BGR tu OpenCV.
Dau ra  : danh sach 21 diem landmark cua ban tay (toa do chuan hoa 0..1),
          hoac None neu khong thay tay.
"""
import os
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
             "hand_landmarker/float16/1/hand_landmarker.task")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "models", "hand_landmarker.task")

HAND_CONNECTIONS = [(c.start, c.end)
                    for c in vision.HandLandmarksConnections.HAND_CONNECTIONS]


def ensure_model():
    """Tai file model cua MediaPipe neu chua co (chi can lan chay dau tien)."""
    if not os.path.exists(MODEL_PATH):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        print("Dang tai model hand_landmarker.task ...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    return MODEL_PATH


class HandTracker:
    def __init__(self):
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=ensure_model()),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.5,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self.last_ts = -1

    def detect(self, frame_bgr, timestamp_ms):
        # MediaPipe can anh RGB, OpenCV doc ra BGR
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # Che do VIDEO yeu cau timestamp tang dan
        timestamp_ms = max(timestamp_ms, self.last_ts + 1)
        self.last_ts = timestamp_ms

        result = self.landmarker.detect_for_video(image, timestamp_ms)
        if not result.hand_landmarks:
            return None
        return result.hand_landmarks[0]  # 21 diem, moi diem co .x .y .z

    def close(self):
        self.landmarker.close()


def draw_hand(frame, landmarks, color=(0, 255, 0)):
    """Ve khung xuong ban tay len frame."""
    h, w = frame.shape[:2]
    pts = [(int(p.x * w), int(p.y * h)) for p in landmarks]
    for a, b in HAND_CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], color, 2)
    for p in pts:
        cv2.circle(frame, p, 4, (255, 255, 255), -1)
