"""
Buoc 4 cua pipeline: LOGIC GAME (phan tu thiet ke).

Game duoc cai dat bang may trang thai (state machine):

    IDLE --SPACE--> COUNTDOWN --het 3s--> CAPTURE --het 0.8s--> RESULT
                        ^                                         |
                        +--------- sau 2.5s (chua ai du diem) ----+
                                                                  |
                              GAME_OVER <--- co nguoi dat WIN_SCORE

Lop nay khong phu thuoc camera/OpenCV: nhan vao thoi gian hien tai va cu chi
da nhan dien, nen co the kiem thu doc lap (xem test_logic.py).
"""
import random
from collections import Counter

from gesture import PAPER, ROCK, SCISSORS

CHOICES = [ROCK, PAPER, SCISSORS]

IDLE, COUNTDOWN, CAPTURE, RESULT, GAME_OVER = (
    "IDLE", "COUNTDOWN", "CAPTURE", "RESULT", "GAME_OVER")

COUNTDOWN_TIME = 3.0   # dem nguoc "Oan... tu... ti"
CAPTURE_TIME = 0.8     # khoang thoi gian ghi nhan cu chi sau khi dem xong
RESULT_TIME = 2.5      # thoi gian hien ket qua moi van
WIN_SCORE = 3          # mac dinh: ai thang 3 van truoc thi thang tran
WIN_SCORE_OPTIONS = (1, 3, 5)  # nguoi choi chon o man hinh cho (phim 1/3/5)


def judge(player, computer):
    """
    Tra ve 1 neu nguoi thang, -1 neu may thang, 0 neu hoa.

    Danh so ROCK=0, PAPER=1, SCISSORS=2. Moi lua chon thang lua chon dung
    ngay truoc no theo vong tron (PAPER>ROCK, SCISSORS>PAPER, ROCK>SCISSORS),
    nen chi can xet (player - computer) mod 3:
        0 -> hoa,  1 -> nguoi thang,  2 -> may thang
    """
    diff = (CHOICES.index(player) - CHOICES.index(computer)) % 3
    return {0: 0, 1: 1, 2: -1}[diff]


class RPSGame:
    def __init__(self, rng=None, win_score=WIN_SCORE):
        # SystemRandom lay entropy tu he dieu hanh -> may ra tay ngau nhien that su
        self.rng = rng or random.SystemRandom()
        self.win_score = win_score
        # Chuoi thang lien tiep, giu qua nhieu tran: thua thi ve 0, hoa thi giu nguyen
        self.streak = 0
        self.reset()

    def set_win_score(self, n):
        """Doi so van can thang de thang tran (chi khi chua/het tran)."""
        if n in WIN_SCORE_OPTIONS and self.state in (IDLE, GAME_OVER):
            self.win_score = n
            self.reset()

    def reset(self):
        self.state = IDLE
        self.state_start = 0.0
        self.player_score = 0
        self.computer_score = 0
        self.round_no = 0
        self.captured = []          # cac cu chi ghi nhan trong CAPTURE
        self.player_move = None
        self.computer_move = None
        self.round_result = None    # 1 / -1 / 0, hoac None neu khong thay tay
        self.history = []           # (nguoi, may, ket qua) cua cac van da tinh
        self.match_best_streak = 0

    def _enter(self, state, now):
        self.state = state
        self.state_start = now

    def start(self, now):
        """Nhan SPACE: bat dau tran moi (tu IDLE hoac GAME_OVER)."""
        if self.state in (IDLE, GAME_OVER):
            self.reset()
            self._start_round(now)

    def _start_round(self, now):
        self.round_no += 1
        self.captured = []
        self.player_move = self.computer_move = self.round_result = None
        self._enter(COUNTDOWN, now)

    def countdown_value(self, now):
        """So hien tren man hinh khi dem nguoc: 3, 2, 1."""
        return max(1, 3 - int(now - self.state_start))

    def update(self, now, gesture):
        """Goi moi frame. gesture la cu chi da on dinh (hoac None)."""
        elapsed = now - self.state_start

        if self.state == COUNTDOWN and elapsed >= COUNTDOWN_TIME:
            self._enter(CAPTURE, now)

        elif self.state == CAPTURE:
            if gesture is not None:
                self.captured.append(gesture)
            if elapsed >= CAPTURE_TIME:
                self._finish_round(now)

        elif self.state == RESULT and elapsed >= RESULT_TIME:
            if max(self.player_score, self.computer_score) >= self.win_score:
                self._enter(GAME_OVER, now)
            else:
                self._start_round(now)

    def _finish_round(self, now):
        # May chon NGAU NHIEN tai thoi diem ra tay -> khong the "doc" truoc
        self.computer_move = self.rng.choice(CHOICES)

        if self.captured:
            # Bo phieu da so: cu chi xuat hien nhieu nhat trong cua so CAPTURE
            self.player_move = Counter(self.captured).most_common(1)[0][0]
            self.round_result = judge(self.player_move, self.computer_move)
            self.history.append((self.player_move, self.computer_move,
                                 self.round_result))
            if self.round_result == 1:
                self.player_score += 1
                self.streak += 1
                self.match_best_streak = max(self.match_best_streak, self.streak)
            elif self.round_result == -1:
                self.computer_score += 1
                self.streak = 0
        else:
            # Khong nhan ra tay -> van khong tinh, choi lai
            self.round_no -= 1
        self._enter(RESULT, now)

    def winner(self):
        if self.player_score >= self.win_score:
            return "PLAYER"
        if self.computer_score >= self.win_score:
            return "COMPUTER"
        return None

    def stats(self):
        """Thong ke tran hien tai: so van thang/thua/hoa, ti le thang,
        cu chi nguoi choi hay ra nhat va chuoi thang dai nhat."""
        results = [r for _, _, r in self.history]
        total = len(results)
        moves = Counter(p for p, _, _ in self.history)
        favorite = moves.most_common(1)[0] if moves else (None, 0)
        return {"wins": results.count(1), "losses": results.count(-1),
                "draws": results.count(0),
                "win_rate": results.count(1) / total if total else 0.0,
                "favorite": favorite, "best_streak": self.match_best_streak}
