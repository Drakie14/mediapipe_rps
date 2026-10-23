"""
Buoc 3 cua pipeline: THUAT TOAN NHAN DIEN CU CHI (phan tu thiet ke).

Tu 21 landmark cua ban tay -> xac dinh moi ngon dang DUOI hay CO
-> phan loai thanh ROCK / PAPER / SCISSORS.

Chi so landmark cua MediaPipe Hand:
    0  = co tay (WRIST)
    Ngon tro   : 5 (MCP), 6 (PIP), 7 (DIP), 8  (TIP)
    Ngon giua  : 9,  10, 11, 12
    Ngon ap ut : 13, 14, 15, 16
    Ngon ut    : 17, 18, 19, 20
"""
import math
from collections import deque

ROCK, PAPER, SCISSORS = "ROCK", "PAPER", "SCISSORS"

WRIST = 0
# (khop PIP, dau ngon TIP) cua 4 ngon: tro, giua, ap ut, ut
FINGERS = [(6, 8), (10, 12), (14, 16), (18, 20)]

# Dau ngon phai xa co tay hon khop PIP it nhat 10% moi tinh la "duoi"
EXTEND_RATIO = 1.1


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def finger_states(landmarks):
    """
    Tra ve list 4 gia tri True/False: ngon tro, giua, ap ut, ut co duoi khong.

    Y tuong: khi ngon DUOI, dau ngon (TIP) nam xa co tay hon khop giua (PIP).
    Khi ngon CO, dau ngon gap vao long ban tay nen lai GAN co tay hon PIP.
    So sanh KHOANG CACH (thay vi so sanh toa do y) giup thuat toan dung
    ca khi ban tay nghieng hoac xoay ngang.
    Ngon cai bi bo qua vi ca 3 cu chi deu phan biet duoc bang 4 ngon con lai,
    va ngon cai rat de nhan sai.
    """
    wrist = landmarks[WRIST]
    states = []
    for pip, tip in FINGERS:
        d_tip = dist(landmarks[tip], wrist)
        d_pip = dist(landmarks[pip], wrist)
        states.append(d_tip > d_pip * EXTEND_RATIO)
    return states


def classify(states):
    """
    Luat phan loai tu trang thai 4 ngon [tro, giua, ap ut, ut]:
      - 0 ngon duoi                        -> ROCK (bua)
      - ca 4 ngon duoi                     -> PAPER (bao)
      - chi tro + giua duoi                -> SCISSORS (keo)
      - truong hop khac                    -> None (khong ro)
    """
    index, middle, ring, pinky = states
    count = sum(states)
    if count == 0:
        return ROCK
    if count == 4:
        return PAPER
    if index and middle and not ring and not pinky:
        return SCISSORS
    return None


class GestureStabilizer:
    """
    Chong nhieu: landmark co the rung giua cac frame, lam ket qua nhay lung tung.
    Chi chap nhan mot cu chi khi no giu NGUYEN trong N frame lien tiep.
    """

    def __init__(self, n_frames=5):
        self.history = deque(maxlen=n_frames)

    def update(self, gesture):
        self.history.append(gesture)
        if len(self.history) == self.history.maxlen and \
                len(set(self.history)) == 1:
            return gesture
        return None

    def reset(self):
        self.history.clear()
