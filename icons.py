"""
Icon ve bang OpenCV (khong can file anh): BUA / BAO / KEO va mat cuoi
THANG / THUA / HOA, cup cho nguoi thang tran, ngon lua cho chuoi thang.

Moi icon la anh BGRA (co kenh alpha) kich thuoc BASE x BASE, ve 1 lan roi
cache lai; khi hien thi thi resize va tron (alpha blend) len frame camera.
"""
from functools import lru_cache

import cv2
import numpy as np

BASE = 200          # kich thuoc goc cua icon (ve to roi thu nho cho net)
AA = cv2.LINE_AA

_cache = {}


def _canvas():
    return np.zeros((BASE, BASE, 4), np.uint8)


def _c(bgr):
    return (*bgr, 255)


def _rock():
    img = _canvas()
    pts = np.array([[40, 120], [55, 70], [95, 45], [145, 55], [170, 95],
                    [165, 140], [130, 165], [70, 162]], np.int32)
    cv2.fillPoly(img, [pts], _c((120, 120, 128)), AA)
    # mat sang phia tren tao khoi
    hi = np.array([[62, 85], [98, 60], [140, 68], [120, 95], [80, 100]], np.int32)
    cv2.fillPoly(img, [hi], _c((165, 165, 172)), AA)
    cv2.polylines(img, [pts], True, _c((60, 60, 66)), 5, AA)
    # vet nut
    cv2.polylines(img, [np.array([[110, 110], [125, 128], [118, 145]], np.int32)],
                  False, _c((70, 70, 76)), 3, AA)
    cv2.polylines(img, [np.array([[70, 125], [85, 135]], np.int32)],
                  False, _c((70, 70, 76)), 3, AA)
    return img


def _paper():
    img = _canvas()
    body = np.array([[50, 25], [125, 25], [155, 55], [155, 175], [50, 175]], np.int32)
    cv2.fillPoly(img, [body], _c((250, 250, 250)), AA)
    cv2.polylines(img, [body], True, _c((90, 90, 90)), 4, AA)
    # goc gap
    fold = np.array([[125, 25], [125, 55], [155, 55]], np.int32)
    cv2.fillPoly(img, [fold], _c((200, 200, 200)), AA)
    cv2.polylines(img, [fold], True, _c((90, 90, 90)), 3, AA)
    # dong ke
    for y in range(80, 165, 20):
        cv2.line(img, (65, y), (140, y), _c((220, 170, 90)), 3, AA)
    return img


def _scissors():
    img = _canvas()
    silver, dark, red = _c((200, 200, 205)), _c((80, 80, 90)), _c((50, 50, 220))
    # hai luoi keo cheo nhau
    for blade in ([[100, 115], [40, 30], [55, 25], [108, 108]],
                  [[100, 115], [160, 30], [145, 25], [92, 108]]):
        p = np.array(blade, np.int32)
        cv2.fillPoly(img, [p], silver, AA)
        cv2.polylines(img, [p], True, dark, 3, AA)
    # can cam va vong tay cam
    cv2.line(img, (100, 112), (70, 140), red, 10, AA)
    cv2.line(img, (100, 112), (130, 140), red, 10, AA)
    for cx in (62, 138):
        cv2.circle(img, (cx, 155), 24, red, 10, AA)
    cv2.circle(img, (100, 112), 7, dark, -1, AA)
    return img


def _face(kind):
    img = _canvas()
    c, r = (100, 100), 85
    cv2.circle(img, c, r, _c((40, 210, 255)), -1, AA)
    cv2.circle(img, c, r, _c((20, 140, 200)), 5, AA)
    ink = _c((40, 40, 60))
    if kind == "WIN":
        # mat cuoi: mat cong ^ ^ va mieng cuoi to
        for x in (68, 132):
            cv2.ellipse(img, (x, 85), (16, 14), 0, 180, 360, ink, 6, AA)
        cv2.ellipse(img, (100, 115), (45, 38), 0, 0, 180, _c((60, 60, 200)), -1, AA)
        cv2.ellipse(img, (100, 115), (45, 38), 0, 0, 180, ink, 4, AA)
        cv2.line(img, (55, 115), (145, 115), ink, 4, AA)
    elif kind == "LOSE":
        # mat buon: long may xech, mieng meu, giot nuoc mat
        for x, d in ((68, 1), (132, -1)):
            cv2.circle(img, (x, 85), 9, ink, -1, AA)
            cv2.line(img, (x - 18 * d, 70), (x + 14 * d, 58), ink, 5, AA)
        cv2.ellipse(img, (100, 150), (35, 25), 0, 200, 340, ink, 6, AA)
        tear = np.array([[132, 98], [124, 120], [140, 120]], np.int32)
        cv2.fillPoly(img, [tear], _c((255, 170, 60)), AA)
        cv2.circle(img, (132, 123), 9, _c((255, 170, 60)), -1, AA)
    else:  # DRAW
        for x in (68, 132):
            cv2.circle(img, (x, 85), 10, ink, -1, AA)
        cv2.line(img, (65, 135), (135, 135), ink, 7, AA)
    return img


def _trophy():
    img = _canvas()
    gold, dark = _c((0, 200, 255)), _c((0, 120, 180))
    cup = np.array([[45, 30], [155, 30], [150, 80], [130, 110], [100, 120],
                    [70, 110], [50, 80]], np.int32)
    for x in (45, 155):  # quai cup
        cv2.circle(img, (x, 60), 25, gold, 9, AA)
    cv2.fillPoly(img, [cup], gold, AA)
    cv2.polylines(img, [cup], True, dark, 4, AA)
    cv2.rectangle(img, (90, 118), (110, 150), gold, -1, AA)
    cv2.rectangle(img, (60, 150), (140, 175), gold, -1, AA)
    cv2.rectangle(img, (60, 150), (140, 175), dark, 4, AA)
    cv2.putText(img, "1", (86, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.6, _c((255, 255, 255)), 5, AA)
    return img


def _fire():
    img = _canvas()
    outer = np.array([[100, 15], [122, 55], [150, 90], [160, 130], [148, 165],
                      [100, 188], [52, 165], [40, 128], [55, 88], [78, 112],
                      [80, 65]], np.int32)
    inner = np.array([[100, 88], [118, 118], [130, 145], [120, 170], [100, 180],
                      [80, 170], [70, 145], [86, 120]], np.int32)
    cv2.fillPoly(img, [outer], _c((0, 110, 255)), AA)
    cv2.polylines(img, [outer], True, _c((0, 60, 200)), 4, AA)
    cv2.fillPoly(img, [inner], _c((60, 220, 255)), AA)
    return img


_MAKERS = {"ROCK": _rock, "PAPER": _paper, "SCISSORS": _scissors,
           "WIN": lambda: _face("WIN"), "LOSE": lambda: _face("LOSE"),
           "DRAW": lambda: _face("DRAW"), "TROPHY": _trophy, "FIRE": _fire}


def get_icon(name):
    if name not in _cache:
        _cache[name] = _MAKERS[name]()
    return _cache[name]


@lru_cache(maxsize=512)
def _scaled(name, size):
    """Icon da thu nho + kenh alpha dang so thuc (cache theo kich thuoc)."""
    icon = cv2.resize(get_icon(name), (size, size), interpolation=cv2.INTER_AREA)
    return icon[:, :, :3].astype(np.float32), icon[:, :, 3:4].astype(np.float32) / 255.0


def draw_icon(frame, name, center, size):
    """Tron icon `name` len frame, tam tai `center`, canh dai `size` pixel."""
    if name is None or size < 4:
        return
    rgb, alpha = _scaled(name, size)
    h, w = frame.shape[:2]
    x0, y0 = center[0] - size // 2, center[1] - size // 2
    # cat phan icon nam ngoai khung hinh
    fx0, fy0, fx1, fy1 = max(x0, 0), max(y0, 0), min(x0 + size, w), min(y0 + size, h)
    if fx0 >= fx1 or fy0 >= fy1:
        return
    sy, sx = slice(fy0 - y0, fy1 - y0), slice(fx0 - x0, fx1 - x0)
    a = alpha[sy, sx]
    roi = frame[fy0:fy1, fx0:fx1]
    roi[:] = (rgb[sy, sx] * a + roi * (1 - a)).astype(np.uint8)
