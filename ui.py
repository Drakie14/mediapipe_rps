"""
Cac ham ve giao dien: chu tieng Viet co dau (qua Pillow), khung nen trong suot
bo goc, vong tien do, vien loe sang va phao giay (confetti).

OpenCV cv2.putText khong ve duoc dau tieng Viet, nen chu duoc gom lai trong
TextLayer roi ve 1 lan moi frame bang Pillow voi font TrueType cua he thong.
"""
import math
import os
import random
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Mau (BGR cho OpenCV)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK = (35, 30, 30)
GREY = (150, 150, 150)
GREEN = (110, 210, 80)
RED = (90, 80, 240)
YELLOW = (40, 205, 255)
CYAN = (230, 200, 60)
ORANGE = (0, 140, 255)

FONT_PATHS = {
    True: ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
           "/System/Library/Fonts/Supplemental/Arial Bold.ttf"],
    False: ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf"],
}


@lru_cache(maxsize=None)
def get_font(size, bold=True):
    for path in FONT_PATHS[bold]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def ease_out_back(t):
    """0 -> 1 co vuot qua 1 mot chut roi thu ve: hieu ung "nay" khi hien ra."""
    t = min(max(t, 0.0), 1.0) - 1
    return 1 + 2.70158 * t ** 3 + 1.70158 * t ** 2


class TextLayer:
    """Gom cac lenh ve chu trong 1 frame, cuoi frame ve het bang Pillow."""

    def __init__(self):
        self.items = []

    def text(self, txt, pos, size, color=WHITE, anchor="mm", bold=True,
             alpha=255, stroke=2):
        """anchor theo Pillow: 'mm' = tam, 'lm' = canh trai, 'rm' = canh phai."""
        if size >= 4 and alpha > 0:
            self.items.append((txt, pos, int(size), color, anchor, bold,
                               int(alpha), stroke))

    def flush(self, frame):
        if not self.items:
            return
        base = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA))
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        for txt, pos, size, (b, g, r), anchor, bold, alpha, stroke in self.items:
            draw.text(pos, txt, font=get_font(size, bold), anchor=anchor,
                      fill=(r, g, b, alpha), stroke_width=stroke,
                      stroke_fill=(0, 0, 0, alpha * 3 // 4))
        base.alpha_composite(layer)
        frame[:] = cv2.cvtColor(np.asarray(base), cv2.COLOR_RGBA2BGR)
        self.items = []


@lru_cache(maxsize=64)
def _round_mask(pw, ph, r):
    """Mat na hinh chu nhat bo goc (cache lai vi kich thuoc it khi doi)."""
    mask = np.zeros((ph, pw), np.uint8)
    cv2.rectangle(mask, (r, 0), (pw - 1 - r, ph - 1), 255, -1)
    cv2.rectangle(mask, (0, r), (pw - 1, ph - 1 - r), 255, -1)
    for cx, cy in ((r, r), (pw - 1 - r, r), (r, ph - 1 - r), (pw - 1 - r, ph - 1 - r)):
        cv2.circle(mask, (cx, cy), r, 255, -1)
    return mask[:, :, None] > 0


def panel(frame, x0, y0, x1, y1, color=DARK, alpha=0.6, radius=18):
    """Khung chu nhat bo goc, trong suot `alpha`, ve de len frame."""
    h, w = frame.shape[:2]
    x0, y0, x1, y1 = max(int(x0), 0), max(int(y0), 0), min(int(x1), w), min(int(y1), h)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    roi = frame[y0:y1, x0:x1]
    r = min(radius, (x1 - x0) // 2, (y1 - y0) // 2)
    solid = np.empty_like(roi)
    solid[:] = color
    blended = cv2.addWeighted(roi, 1 - alpha, solid, alpha, 0)
    np.copyto(roi, blended, where=_round_mask(x1 - x0, y1 - y0, r))


def progress_ring(frame, center, radius, fraction, color, thickness=10):
    """Vong tron tien do: nen xam mo + cung mau chay theo `fraction` (0..1)."""
    overlay = frame.copy()
    cv2.circle(overlay, center, radius, GREY, thickness, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)
    end = -90 + 360 * min(max(fraction, 0.0), 1.0)
    cv2.ellipse(frame, center, (radius, radius), 0, -90, end, color,
                thickness, cv2.LINE_AA)


def flash_border(frame, color, strength, thickness=22):
    """Vien man hinh loe sang, `strength` 0..1 (giam dan de tao hieu ung mo)."""
    if strength <= 0:
        return
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w - 1, h - 1), color, thickness * 2)
    cv2.addWeighted(overlay, strength, frame, 1 - strength, 0, frame)


def score_dots(frame, x_start, y, score, total, color, step=24, r=8):
    """Hang `total` cham tron bat dau tu x_start (step am = ve sang trai),
    `score` cham dau duoc to mau."""
    for i in range(total):
        c = (x_start + i * step, y)
        if i < score:
            cv2.circle(frame, c, r, color, -1, cv2.LINE_AA)
            cv2.circle(frame, c, r, WHITE, 2, cv2.LINE_AA)
        else:
            cv2.circle(frame, c, r, GREY, 2, cv2.LINE_AA)


def text_width(txt, size, bold=True):
    return get_font(int(size), bold).getlength(txt)


def speech_bubble(frame, text, txt, center, size=16, max_right=None):
    """Bong bong loi noi (cho may "noi") co duoi nhon chi len tren."""
    tw = text_width(txt, size)
    x, y = center
    if max_right is not None:
        x = min(x, int(max_right - tw / 2 - 14))
    x0, x1 = int(x - tw / 2 - 14), int(x + tw / 2 + 14)
    y0, y1 = y - size, y + size
    color = (245, 245, 245)
    tail = np.array([[center[0] - 8, y0 + 1], [center[0] + 8, y0 + 1],
                     [center[0], y0 - 10]], np.int32)
    cv2.fillPoly(frame, [tail], color, cv2.LINE_AA)
    panel(frame, x0, y0, x1, y1, color=color, alpha=0.95, radius=size)
    text.text(txt, (x, y), size, (40, 30, 30), stroke=0)


def chip(frame, text, label, center, selected, size=18):
    """O lua chon nho (vd so van 1/3/5), o dang chon duoc to vang."""
    x, y = center
    panel(frame, x - 17, y - 15, x + 17, y + 15,
          color=YELLOW if selected else (90, 85, 85), alpha=0.95, radius=8)
    text.text(label, (x, y), size, (30, 30, 30) if selected else WHITE,
              stroke=0)


class Confetti:
    """Phao giay roi khi nguoi choi thang tran."""

    COLORS = [(60, 200, 255), (90, 80, 240), (110, 210, 80), (230, 160, 60),
              (200, 90, 220), (255, 255, 255)]

    def __init__(self, count=160):
        self.count = count
        self.parts = []
        self.rng = random.Random()

    def _spawn(self, w, h, top_only):
        rnd = self.rng
        return {"x": rnd.uniform(0, w),
                "y": rnd.uniform(-h * 0.3, 0) if top_only else rnd.uniform(-h, 0),
                "vx": rnd.uniform(-40, 40), "vy": rnd.uniform(120, 260),
                "ang": rnd.uniform(0, 360), "spin": rnd.uniform(-360, 360),
                "size": rnd.uniform(6, 12), "color": rnd.choice(self.COLORS),
                "phase": rnd.uniform(0, 6.28)}

    def start(self, w, h):
        self.parts = [self._spawn(w, h, False) for _ in range(self.count)]

    def stop(self):
        self.parts = []

    def update_and_draw(self, frame, dt):
        h, w = frame.shape[:2]
        for i, p in enumerate(self.parts):
            p["phase"] += dt * 4
            p["x"] += (p["vx"] + 30 * math.sin(p["phase"])) * dt
            p["y"] += p["vy"] * dt
            p["ang"] += p["spin"] * dt
            if p["y"] > h + 20:  # roi het man hinh -> tai sinh o tren
                self.parts[i] = p = self._spawn(w, h, True)
            s = p["size"]
            box = cv2.boxPoints(((p["x"], p["y"]), (s, s * 0.55), p["ang"]))
            cv2.fillPoly(frame, [box.astype(np.int32)], p["color"], cv2.LINE_AA)
