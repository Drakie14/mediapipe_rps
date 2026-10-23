"""
Oan Tu Ti (Rock - Paper - Scissors) dieu khien bang cu chi tay qua camera.

Pipeline:
    Camera -> MediaPipe Hand (hand_tracker.py) -> 21 landmark
           -> Thuat toan nhan dien cu chi (gesture.py)
           -> Logic game (game.py) -> Hien thi (file nay)

Phim: SPACE = bat dau / choi lai,  1/3/5 = so van de thang tran,
      M = bat/tat am thanh,  R = reset,  Q hoac ESC = thoat
"""
import json
import math
import os
import random
import sys
import time
from types import SimpleNamespace

import cv2

from game import (CAPTURE, COUNTDOWN, COUNTDOWN_TIME, GAME_OVER, IDLE, RESULT,
                  WIN_SCORE_OPTIONS, RPSGame)
from gesture import GestureStabilizer, classify, finger_states
from hand_tracker import HandTracker, draw_hand
from icons import draw_icon
from sound import Sound
from ui import (CYAN, GREEN, GREY, ORANGE, RED, WHITE, YELLOW, Confetti,
                TextLayer, chip, ease_out_back, flash_border, panel,
                progress_ring, score_dots, speech_bubble)

VN_NAME = {"ROCK": "Búa", "PAPER": "Bao", "SCISSORS": "Kéo", None: "—"}
RESULT_STYLE = {1: ("BẠN THẮNG!", GREEN, "WIN"),
                -1: ("BẠN THUA!", RED, "LOSE"),
                0: ("HÒA!", YELLOW, "DRAW")}

# Cau "noi" cua may sau moi van ({p} = tay nguoi choi, {c} = tay may)
TAUNTS = {
    1: ["Hên thôi!", "Ván sau không dễ vậy đâu!", "Ơ… chơi lại đi!",
        "{p} à? Hay đấy!", "Được, lần này thôi nhé"],
    -1: ["Dễ quá!", "Đoán trúng rồi nhé!", "{c} thắng {p}, hehe",
         "Thử lại xem nào!", "Máy là số một!"],
    0: ["Tâm đầu ý hợp!", "Lại {p} à?", "Hòa rồi, làm lại!",
        "Nghĩ giống nhau ghê"],
}
RESULT_SOUND = {1: "win", -1: "lose", 0: "draw", None: "miss"}

# Ky luc chuoi thang luu vao file de lan sau van con
RECORD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "records.json")


def load_record():
    try:
        with open(RECORD_PATH, encoding="utf-8") as f:
            return int(json.load(f).get("best_streak", 0))
    except (OSError, ValueError, AttributeError):
        return 0


def save_record(best_streak):
    try:
        with open(RECORD_PATH, "w", encoding="utf-8") as f:
            json.dump({"best_streak": best_streak}, f)
    except OSError:
        pass


def draw_hud(frame, game, gesture, states, now, text, info):
    h, w = frame.shape[:2]
    cx = w // 2
    elapsed = now - game.state_start
    # Hieu ung "bat ra": icon/chu phong to co nay nhe trong 0.35s dau moi trang thai
    pop = ease_out_back(elapsed / 0.35)

    # --- Thanh diem so phia tren: cham tron sang len theo so van thang ---
    panel(frame, 10, 10, w - 10, 64)
    text.text("Bạn", (28, 37), 24, GREEN, anchor="lm")
    score_dots(frame, 92, 37, game.player_score, game.win_score, GREEN)
    text.text("Máy", (w - 28, 37), 24, RED, anchor="rm")
    score_dots(frame, w - 92, 37, game.computer_score, game.win_score, RED, step=-24)
    text.text(f"Ván {max(game.round_no, 1)}", (cx, 30), 22, WHITE)
    text.text(f"chạm {game.win_score} ván thắng", (cx, 52), 13, GREY,
              bold=False, stroke=0)

    # --- Du lieu tu MediaPipe + ket qua thuat toan (phia duoi) ---
    panel(frame, 10, h - 74, w - 10, h - 10)
    if states is not None:
        names = ["Trỏ", "Giữa", "Áp út", "Út"]
        txt = "   ".join(f"{n}: {'duỗi' if s else 'co'}" for n, s in zip(names, states))
        text.text(txt, (28, h - 55), 15, CYAN, anchor="lm", bold=False, stroke=0)
    else:
        text.text("Chưa thấy tay", (28, h - 55), 15, GREY, anchor="lm", bold=False, stroke=0)
    text.text(f"Cử chỉ: {VN_NAME[gesture]}", (28, h - 30), 22, YELLOW, anchor="lm")
    draw_icon(frame, gesture, (w - 50, h - 42), 54)
    # Chuoi thang lien tiep (tu 2 van tro len)
    if game.streak >= 2:
        grow = pop if game.state == RESULT and game.round_result == 1 else 1.0
        draw_icon(frame, "FIRE", (w - 250, h - 42), int(34 * grow))
        text.text(f"Chuỗi thắng x{game.streak}", (w - 230, h - 42), 18, ORANGE,
                  anchor="lm")

    # --- Noi dung chinh theo trang thai game ---
    if game.state == IDLE:
        panel(frame, cx - 215, h // 2 - 128, cx + 215, h // 2 + 125)
        for i, move in enumerate(("ROCK", "PAPER", "SCISSORS")):
            bob = int(8 * math.sin(now * 3 + i * 1.2))  # icon nhun nhay
            draw_icon(frame, move, (cx + (i - 1) * 90, h // 2 - 82 + bob), 60)
        text.text("Oẳn Tù Tì", (cx, h // 2 - 18), 52, YELLOW, stroke=3)
        # Chon so van can thang: phim 1 / 3 / 5
        text.text("Chạm mấy ván thắng?", (cx - 5, h // 2 + 32), 17, WHITE,
                  anchor="rm", bold=False, stroke=0)
        for i, n in enumerate(WIN_SCORE_OPTIONS):
            chip(frame, text, str(n), (cx + 25 + i * 42, h // 2 + 32),
                 n == game.win_score)
        blink = int(160 + 95 * math.sin(now * 4))
        text.text("Nhấn SPACE để bắt đầu", (cx, h // 2 + 72), 22, WHITE, alpha=blink)
        snd = "tắt" if info.muted else "bật"
        text.text(f"Kỷ lục chuỗi thắng: {info.record}   ·   M: âm thanh ({snd})",
                  (cx, h // 2 + 105), 14, GREY, bold=False, stroke=0)

    elif game.state == COUNTDOWN:
        words = {3: "Oẳn…", 2: "Tù…", 1: "Tì!"}
        n = game.countdown_value(now)
        t = elapsed % 1.0                   # thoi gian trong giay hien tai
        center = (cx, h // 2 - 10)
        progress_ring(frame, center, 95, elapsed / COUNTDOWN_TIME, YELLOW)
        size = 130 * (0.5 + 0.5 * ease_out_back(t / 0.35))
        fade = 255 * min(1.0, (1.0 - t) / 0.25)  # mo dan truoc khi sang so moi
        text.text(str(n), center, size, YELLOW, alpha=fade, stroke=4)
        text.text(words[n], (cx, h // 2 + 120), 34, WHITE, stroke=3)

    elif game.state == CAPTURE:
        flash_border(frame, GREEN, 0.45)
        size = 84 * (1 + 0.08 * math.sin(elapsed * 20))  # chu nhip dap
        text.text("RA TAY!", (cx, h // 2), size, GREEN, stroke=4)

    elif game.state == RESULT:
        if game.player_move is None:
            panel(frame, cx - 230, h // 2 - 45, cx + 230, h // 2 + 45)
            text.text("Không thấy tay – chơi lại!", (cx, h // 2), 30, RED)
        else:
            msg, color, face = RESULT_STYLE[game.round_result]
            flash_border(frame, color, 0.7 * max(0.0, 1 - elapsed / 0.8))
            panel(frame, 30, 76, w - 30, h - 86, alpha=0.5)
            # Icon tay cua ban (trai) VS may (phai)
            y, size = 150, int(110 * pop)
            draw_icon(frame, game.player_move, (w // 4, y), size)
            draw_icon(frame, game.computer_move, (3 * w // 4, y), size)
            text.text("VS", (cx, y), 40, WHITE, stroke=3)
            text.text(f"Bạn: {VN_NAME[game.player_move]}", (w // 4, y + 75), 24, GREEN)
            text.text(f"Máy: {VN_NAME[game.computer_move]}", (3 * w // 4, y + 75), 24, RED)
            # May "noi" sau khi hien ket qua 0.4s
            if info.taunt and elapsed > 0.4:
                speech_bubble(frame, text, info.taunt, (3 * w // 4, y + 124),
                              max_right=w - 40)
            # Mat cuoi / mat buon / mat binh thuong theo ket qua
            draw_icon(frame, face, (cx, y + 135), int(80 * pop))
            text.text(msg, (cx, y + 205), 50 * min(pop, 1.1), color, stroke=3)

    elif game.state == GAME_OVER:
        won = game.winner() == "PLAYER"
        st = game.stats()
        panel(frame, 30, 76, w - 30, h - 86, alpha=0.6)
        draw_icon(frame, "TROPHY" if won else "LOSE", (cx, 120), int(72 * pop))
        text.text("BẠN THẮNG TRẬN!" if won else "MÁY THẮNG TRẬN!",
                  (cx, 185), 40, GREEN if won else RED, stroke=3)
        # Bang tong ket tran
        text.text(f"Thắng {st['wins']}   ·   Thua {st['losses']}   ·   Hòa {st['draws']}",
                  (cx, 228), 20, WHITE)
        fav, count = st["favorite"]
        text.text(f"Tỉ lệ thắng: {st['win_rate']:.0%}   ·   Bạn hay ra: "
                  f"{VN_NAME[fav]} ({count} lần)", (cx, 257), 17, CYAN, bold=False)
        if info.new_record:
            glow = int(190 + 65 * math.sin(now * 6))
            text.text(f"KỶ LỤC MỚI: {info.record} ván thắng liên tiếp!",
                      (cx, 290), 20, YELLOW, alpha=glow)
        else:
            text.text(f"Chuỗi thắng dài nhất: {st['best_streak']}   ·   "
                      f"Kỷ lục: {info.record}", (cx, 290), 17, ORANGE, bold=False)
        text.text("SPACE: chơi lại   ·   1/3/5: đổi số ván   ·   Q: thoát",
                  (cx, 340), 16, WHITE, bold=False)


def main():
    cam_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print(f"Khong mo duoc camera {cam_index}")
        return

    tracker = HandTracker()
    stabilizer = GestureStabilizer(n_frames=5)
    game = RPSGame()
    text = TextLayer()
    confetti = Confetti()
    sound = Sound()
    rng = random.Random()
    info = SimpleNamespace(record=load_record(), new_record=False, taunt=None,
                           muted=False)
    record_at_match_start = info.record
    prev_state, prev_count, prev_now = game.state, None, 0.0
    t0 = time.monotonic()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)  # lat nhu guong cho de dieu khien
        now = time.monotonic() - t0

        # 1) MediaPipe: lay 21 landmark cua ban tay
        landmarks = tracker.detect(frame, int(now * 1000))

        # 2) Thuat toan: landmark -> trang thai ngon -> cu chi (da chong nhieu)
        states, gesture = None, None
        if landmarks is not None:
            draw_hand(frame, landmarks)
            states = finger_states(landmarks)
            gesture = stabilizer.update(classify(states))
        else:
            stabilizer.reset()

        # 3) Logic game
        game.update(now, gesture)

        # Ky luc chuoi thang: cap nhat va luu ngay khi bi vuot
        if game.streak > info.record:
            info.record = game.streak
            save_record(info.record)
        info.new_record = info.record > record_at_match_start

        # Su kien khi doi trang thai: am thanh, cau noi cua may, phao giay
        if game.state != prev_state:
            if game.state == CAPTURE:
                sound.play("go")
            elif game.state == RESULT:
                sound.play(RESULT_SOUND[game.round_result])
                info.taunt = None
                if game.round_result is not None:
                    info.taunt = rng.choice(TAUNTS[game.round_result]).format(
                        p=VN_NAME[game.player_move], c=VN_NAME[game.computer_move])
            elif game.state == GAME_OVER:
                won = game.winner() == "PLAYER"
                sound.play("match_win" if won else "match_lose")
                if won:
                    confetti.start(frame.shape[1], frame.shape[0])
            if game.state != GAME_OVER:
                confetti.stop()
            prev_state = game.state
        # Tieng "tich" moi nhip dem nguoc 3 - 2 - 1
        count = game.countdown_value(now) if game.state == COUNTDOWN else None
        if count is not None and count != prev_count:
            sound.play("tick")
        prev_count = count

        # 4) Hien thi
        draw_hud(frame, game, gesture, states, now, text, info)
        confetti.update_and_draw(frame, now - prev_now)
        text.flush(frame)  # ve tat ca chu (co dau) len tren cung
        prev_now = now
        cv2.imshow("Oan Tu Ti - MediaPipe Hand", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key == ord(" ") and game.state in (IDLE, GAME_OVER):
            record_at_match_start = info.record
            game.start(now)
        if key == ord("r"):
            game.reset()
        if key == ord("m"):
            sound.toggle()
            info.muted = sound.muted
        if key in (ord("1"), ord("3"), ord("5")):
            old = game.win_score
            game.set_win_score(int(chr(key)))
            if game.win_score != old:
                sound.play("select")

    tracker.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
