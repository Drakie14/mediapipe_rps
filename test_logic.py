"""
Kiem thu thuat toan va logic game ma KHONG can camera.
Chay: python test_logic.py
"""
import random
from types import SimpleNamespace as P

from game import CAPTURE, COUNTDOWN, GAME_OVER, IDLE, RESULT, RPSGame, judge
from gesture import (PAPER, ROCK, SCISSORS, GestureStabilizer, classify,
                     finger_states)


def fake_hand(extended):
    """
    Tao 21 landmark gia: co tay o (0.5, 0.9), ngon huong len tren.
    Ngon duoi: TIP cao hon PIP. Ngon co: TIP gap xuong gan co tay.
    """
    lm = [P(x=0.5, y=0.9) for _ in range(21)]
    for i, (pip, tip) in enumerate([(6, 8), (10, 12), (14, 16), (18, 20)]):
        x = 0.4 + i * 0.06
        lm[pip] = P(x=x, y=0.6)
        lm[tip] = P(x=x, y=0.4 if extended[i] else 0.72)
    return lm


def test_gestures():
    assert classify(finger_states(fake_hand([0, 0, 0, 0]))) == ROCK
    assert classify(finger_states(fake_hand([1, 1, 1, 1]))) == PAPER
    assert classify(finger_states(fake_hand([1, 1, 0, 0]))) == SCISSORS
    assert classify(finger_states(fake_hand([1, 0, 0, 0]))) is None


def test_rotated_hand():
    # Xoay ban tay 90 do (ngon huong sang ngang): (x, y) -> (y, x)
    lm = [P(x=p.y, y=p.x) for p in fake_hand([1, 1, 0, 0])]
    assert classify(finger_states(lm)) == SCISSORS


def test_judge():
    assert judge(ROCK, SCISSORS) == 1
    assert judge(PAPER, ROCK) == 1
    assert judge(SCISSORS, PAPER) == 1
    assert judge(ROCK, PAPER) == -1
    for m in (ROCK, PAPER, SCISSORS):
        assert judge(m, m) == 0


def test_stabilizer():
    s = GestureStabilizer(n_frames=3)
    assert s.update(ROCK) is None
    assert s.update(ROCK) is None
    assert s.update(ROCK) == ROCK
    assert s.update(PAPER) is None  # vua doi -> chua on dinh


def play_round(game, t, gesture):
    """Mo phong 1 van: dem nguoc -> ra tay -> ket qua."""
    assert game.state == COUNTDOWN
    t += 3.01
    game.update(t, gesture)
    assert game.state == CAPTURE
    for _ in range(10):
        t += 0.1
        game.update(t, gesture)
    assert game.state == RESULT
    t += 2.51
    game.update(t, None)
    return t


def test_full_match():
    game = RPSGame(rng=random.Random(0))
    assert game.state == IDLE
    game.start(0.0)
    t = 0.0
    while game.state != GAME_OVER:
        t = play_round(game, t, ROCK)
    assert game.winner() in ("PLAYER", "COMPUTER")
    assert max(game.player_score, game.computer_score) == 3


def test_no_hand_round_not_counted():
    game = RPSGame(rng=random.Random(0))
    game.start(0.0)
    play_round(game, 0.0, None)
    assert game.player_score == game.computer_score == 0
    assert game.round_no == 1  # van bi huy, van tiep theo van la van 1


class FixedRng:
    """rng gia: may luon ra theo danh sach cho truoc (de kiem thu co dinh)."""

    def __init__(self, moves):
        self.moves = list(moves)

    def choice(self, _):
        return self.moves.pop(0)


def test_win_score_option():
    game = RPSGame(rng=random.Random(0))
    game.set_win_score(1)
    game.start(0.0)
    t = 0.0
    while game.state != GAME_OVER:  # van hoa thi choi tiep
        t = play_round(game, t, ROCK)
    assert max(game.player_score, game.computer_score) == 1
    game.set_win_score(4)  # khong nam trong 1/3/5 -> bo qua
    assert game.win_score == 1


def test_streak_and_stats():
    # Nguoi luon ra BUA; may: Keo, Keo, Bua, Keo, Bao, Keo
    game = RPSGame(rng=FixedRng([SCISSORS, SCISSORS, ROCK, SCISSORS,
                                 PAPER, SCISSORS]), win_score=5)
    game.start(0.0)
    streaks, t = [], 0.0
    for _ in range(6):
        t = play_round(game, t, ROCK)
        streaks.append(game.streak)
    # thang, thang, hoa (giu chuoi), thang, thua (ve 0), thang
    assert streaks == [1, 2, 2, 3, 0, 1]
    st = game.stats()
    assert (st["wins"], st["losses"], st["draws"]) == (4, 1, 1)
    assert st["favorite"] == (ROCK, 6)
    assert st["best_streak"] == 3
    assert abs(st["win_rate"] - 4 / 6) < 1e-9


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
