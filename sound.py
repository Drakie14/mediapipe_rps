"""
Am thanh hieu ung: tong hop cac not nhac bang numpy (khong can file am thanh),
ghi ra file WAV tam roi phat khong dong bo bang winsound (co san tren Windows).
Tren he dieu hanh khac, game van chay binh thuong nhung khong co tieng.
"""
import os
import tempfile
import wave

import numpy as np

try:
    import winsound
except ImportError:  # khong phai Windows
    winsound = None

RATE = 22050

# Moi am thanh la chuoi (tan so Hz, thoi luong giay); tan so 0 = khoang lang
MELODIES = {
    "tick": [(880, 0.09)],
    "go": [(1175, 0.07), (1568, 0.16)],
    "win": [(523, 0.09), (659, 0.09), (784, 0.09), (1047, 0.28)],
    "lose": [(392, 0.16), (330, 0.16), (262, 0.4)],
    "draw": [(587, 0.12), (0, 0.04), (587, 0.18)],
    "miss": [(300, 0.12), (250, 0.2)],
    "match_win": [(523, 0.12), (523, 0.12), (523, 0.12), (659, 0.32), (0, 0.05),
                  (587, 0.12), (659, 0.12), (784, 0.6)],
    "match_lose": [(392, 0.28), (370, 0.28), (349, 0.28), (330, 0.7)],
    "select": [(1047, 0.05)],
}


def _note(freq, dur):
    t = np.arange(int(RATE * dur)) / RATE
    if freq == 0:
        return np.zeros_like(t)
    # song sin + hoa am bac 2 cho tieng "tron" hon, bao am: vao nhanh, tat dan
    wave_ = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    env = np.minimum(1.0, t / 0.005) * np.exp(-3.0 * t / dur)
    return wave_ * env


def _write_wav(path, notes):
    samples = np.concatenate([_note(f, d) for f, d in notes])
    pcm = (samples / 1.3 * 0.5 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())


class Sound:
    def __init__(self):
        self.muted = False
        self.paths = {}
        if winsound is None:
            return
        folder = os.path.join(tempfile.gettempdir(), "rps_sounds")
        os.makedirs(folder, exist_ok=True)
        for name, notes in MELODIES.items():
            path = os.path.join(folder, f"{name}.wav")
            _write_wav(path, notes)
            self.paths[name] = path

    @property
    def available(self):
        return bool(self.paths)

    def toggle(self):
        self.muted = not self.muted

    def play(self, name):
        if self.muted or name not in self.paths:
            return
        # SND_ASYNC: phat nen, khong lam dung vong lap camera
        winsound.PlaySound(self.paths[name], winsound.SND_FILENAME |
                           winsound.SND_ASYNC | winsound.SND_NODEFAULT)
