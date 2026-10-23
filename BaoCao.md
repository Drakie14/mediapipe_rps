# Báo cáo Assignment: Xây dựng ứng dụng tương tác với camera sử dụng MediaPipe

**Đề tài:** Oẳn Tù Tì (Búa – Bao – Kéo) bằng cử chỉ tay
**Framework:** MediaPipe Hand Landmarker
**Ngôn ngữ:** Python 3.9+
**Mã nguồn:** thư mục `mediapipe_rps/` (xem `README.md` để cài đặt và chạy)

---

## 1. Ý tưởng và mục tiêu

Người chơi đưa tay ra trước webcam và ra **Búa**, **Bao** hoặc **Kéo**. Máy ra tay ngẫu nhiên. Chương trình nhận diện cử chỉ của người chơi, tính kết quả từng ván và ai thắng đủ số ván đã chọn (mặc định 3) trước thì thắng trận.

Mục tiêu:

- Dùng MediaPipe chỉ để lấy **vị trí 21 điểm trên bàn tay** từ camera.
- Tự thiết kế thuật toán để chuyển 21 điểm đó thành **trạng thái từng ngón** rồi thành **cử chỉ**.
- Tự thiết kế logic game: máy trạng thái, chống nhiễu, bỏ phiếu cử chỉ, phân định thắng thua, tính điểm.

## 2. Input và Output

| | Mô tả |
|---|---|
| **Input** | Khung hình (frame) từ webcam, cộng với thao tác phím: `SPACE` bắt đầu, `1/3/5` chọn số ván thắng, `M` bật/tắt âm, `R` reset, `Q`/`ESC` thoát |
| **Output** | Hình ảnh trên màn hình: đếm ngược, cử chỉ đang nhận diện, trạng thái ngón tay, kết quả ván, bảng thống kê cuối trận; âm thanh; file `records.json` lưu kỷ lục chuỗi thắng |

Luồng xử lý tổng quát:

```
Camera → MediaPipe Hand → 21 landmark → Thuật toán nhận diện ngón tay → Cử chỉ → Logic game → Màn hình
```

## 3. Chức năng MediaPipe được sử dụng

- **Hand Landmarker** (`hand_tracker.py`), chế độ ảnh video, tối đa 1 bàn tay, ngưỡng tin cậy phát hiện và theo dõi 0.6 / 0.6 / 0.5.
- **Dữ liệu MediaPipe cung cấp:** 21 landmark cho mỗi bàn tay, mỗi landmark có tọa độ `x`, `y` chuẩn hóa về [0, 1] theo kích thước ảnh.

MediaPipe không biết gì về Búa, Bao hay Kéo. Toàn bộ phần đó do thuật toán của nhóm/sinh viên quyết định.

## 4. Thuật toán và logic xử lý tự xây dựng

### 4.1. Xác định ngón duỗi hay co (`gesture.py`, hàm `finger_states`)

Với mỗi ngón trỏ, giữa, áp út, út (ngón cái bị bỏ qua), so sánh khoảng cách từ đầu ngón (TIP) và khớp giữa (PIP) tới cổ tay (landmark 0):

```
ngón DUỖI  ⇔  khoảng_cách(TIP, cổ_tay) > 1.1 × khoảng_cách(PIP, cổ_tay)
```

Lý do thiết kế:

- **Dùng khoảng cách, không dùng tọa độ `y`.** Khi bàn tay nghiêng hoặc xoay ngang, so sánh `y` sẽ sai. Khoảng cách tới cổ tay vẫn đúng. Có test `test_rotated_hand` kiểm chứng.
- **Hệ số 1.1** là ngưỡng an toàn để ngón hơi cong không bị tính là duỗi.
- **Bỏ qua ngón cái.** Ngón cái chuyển động ngang nên hay bị nhận sai. Ba cử chỉ đều phân biệt được chỉ bằng 4 ngón còn lại.

### 4.2. Phân loại cử chỉ (`gesture.py`, hàm `classify`)

| Trạng thái 4 ngón (trỏ, giữa, áp út, út) | Cử chỉ |
|---|---|
| Không ngón nào duỗi | Búa (ROCK) |
| Cả 4 ngón duỗi | Bao (PAPER) |
| Chỉ trỏ và giữa duỗi | Kéo (SCISSORS) |
| Trường hợp khác | Không rõ, bỏ qua |

### 4.3. Chống nhiễu (`GestureStabilizer`)

Landmark dao động nhẹ giữa các frame nên kết quả có thể nhảy liên tục. Một cử chỉ chỉ được chấp nhận khi **giữ nguyên trong 5 frame liên tiếp**. Nếu mất tay, bộ đệm bị xóa.

### 4.4. Máy trạng thái của game (`game.py`)

```
IDLE ──SPACE──► COUNTDOWN ──3s──► CAPTURE ──0.8s──► RESULT ──2.5s──► COUNTDOWN (ván mới)
                                                       │
                                                       └── có người đạt đủ số ván ──► GAME_OVER
```

- **COUNTDOWN (3 giây):** đếm ngược "Oẳn… tù… tì!". Máy chọn cử chỉ ngẫu nhiên đúng lúc hết đếm, nên máy không "đọc" được tay người chơi trước.
- **CAPTURE (0.8 giây):** ghi lại mọi cử chỉ đã ổn định. Cử chỉ của người chơi là cử chỉ **xuất hiện nhiều nhất** (bỏ phiếu đa số), nên ra tay chậm hoặc vài frame sai không ảnh hưởng.
- Nếu trong CAPTURE không thấy tay, ván đó **không được tính** và phải chơi lại.
- **RESULT (2.5 giây):** hiển thị kết quả, rồi tự chuyển sang ván mới.
- **GAME_OVER:** khi một bên đạt đủ số ván thắng.

### 4.5. Phân định thắng thua (`game.py`, hàm `judge`)

Đánh số Búa = 0, Bao = 1, Kéo = 2. Mỗi lựa chọn thắng lựa chọn đứng ngay trước nó theo vòng tròn (Bao thắng Búa, Kéo thắng Bao, Búa thắng Kéo). Vì vậy chỉ cần tính:

```
d = (người − máy) mod 3
d = 0  → hòa
d = 1  → người thắng
d = 2  → máy thắng
```

### 4.6. Tính điểm và sự kiện

- Thắng một ván được 1 điểm, hòa hoặc không thấy tay thì không ai được điểm.
- Người đầu tiên đạt số điểm mục tiêu (1, 3 hoặc 5, chọn bằng phím) thắng trận.
- Chuỗi thắng liên tiếp được theo dõi, và kỷ lục được lưu vào `records.json`.
- Sự kiện âm thanh (thắng, thua, hòa, không thấy tay) phát theo kết quả ván (`sound.py`).

## 5. Chuyển đổi dữ liệu từ MediaPipe thành hành động trong ứng dụng

Một khung hình đi qua chuỗi biến đổi sau:

1. **21 landmark** (tọa độ chuẩn hóa) → **4 trạng thái ngón** (duỗi/co), theo khoảng cách tới cổ tay.
2. **4 trạng thái ngón** → **1 cử chỉ** (Búa/Bao/Kéo/không rõ) theo bảng ở mục 4.2.
3. **Chuỗi cử chỉ theo thời gian** → **1 cử chỉ ổn định** (qua bộ lọc 5 frame liên tiếp, rồi bỏ phiếu trong 0.8 giây).
4. **Cử chỉ người chơi + cử chỉ máy** → **kết quả ván** (hàm `judge`) → **cập nhật điểm** → **màn hình và âm thanh**.

Giao diện bên góc dưới hiển thị trạng thái từng ngón và cử chỉ đang nhận diện, để người xem thấy trực tiếp dữ liệu được xử lý như thế nào.

## 6. Kiểm thử

### 6.1. Kiểm thử tự động (không cần camera)

Chạy `python test_logic.py`. Kết quả lần chạy gần nhất:

```
PASS test_gestures
PASS test_rotated_hand
PASS test_judge
PASS test_stabilizer
PASS test_full_match
PASS test_no_hand_round_not_counted
PASS test_win_score_option
PASS test_streak_and_stats
```

8/8 test đạt. Các test bao gồm: phân loại 3 cử chỉ, bàn tay xoay 90°, luật thắng thua, bộ chống nhiễu, mô phỏng trọn một trận, ván không thấy tay không được tính, chọn số ván thắng, và thống kê chuỗi thắng.

### 6.2. Kiểm thử thuật toán trên ảnh mẫu

| Ảnh | Trạng thái 4 ngón | Kết quả |
|---|---|---|
| Tay giơ chữ V | duỗi, duỗi, co, co | Kéo, đúng |
| Bàn tay xòe | duỗi × 4 | Bao, đúng |
| Nắm tay giơ ngón cái | co × 4 | Búa, đúng (bỏ qua ngón cái) |
| Chỉ giơ ngón trỏ | duỗi, co, co, co | Không rõ, đúng |

### 6.3. Thực nghiệm với camera

> **[Cần bổ sung]** Ghi lại kết quả thử thật với webcam: số lần thử, số lần nhận đúng từng cử chỉ, điều kiện ánh sáng, khoảng cách tới camera. Ví dụ một bảng:
>
> | Cử chỉ ra tay | Số lần thử | Nhận đúng | Tỉ lệ |
> |---|---|---|---|
> | Búa | | | |
> | Bao | | | |
> | Kéo | | | |

> **[Cần bổ sung]** Ảnh chụp màn hình: đếm ngược, lúc nhận diện cử chỉ, màn hình kết quả ván, bảng thống kê cuối trận.

## 7. Khó khăn gặp phải

- **Ngưỡng duỗi/co:** ngưỡng 1.1 là một lựa chọn cần kiểm chứng với camera thật. Ngưỡng thấp quá thì ngón hơi cong dễ bị nhận là duỗi, còn ngưỡng cao quá thì ngón duỗi nhẹ lại bị nhận là co.
- **Ngón cái:** chuyển động ngang nên nhận sai, nên nhóm quyết định bỏ qua ngón cái.
- **Nhiễu theo frame:** kết quả nhảy liên tục giữa các frame, giải quyết bằng bộ lọc 5 frame và bỏ phiếu đa số.
- **Thiếu sáng hoặc che khuất:** khi bàn tay quay mu tay hoặc cạnh tay về camera, các ngón che nhau nên nhận diện kém.
- **Đồng bộ thời gian:** máy phải ra tay ngẫu nhiên đúng lúc, và chỉ đọc cử chỉ người chơi trong một khoảng thời gian cố định. Trạng thái máy chờ đảm bảo việc này.

## 8. Hướng phát triển

- Cho máy "học" thói quen người chơi, ví dụ đếm tần suất cử chỉ người hay ra để chọn nước khắc chế.
- Thêm chế độ 2 người chơi (`num_hands=2`).
- Dùng thêm các điểm của ngón cái để nhận diện chính xác hơn.
- Thêm bảng xếp hạng và thêm hiệu ứng âm thanh/hình ảnh.

## 9. Video demo

> **[Cần bổ sung]** Link video demo: _(dán link vào đây)_

---

*Tài liệu tham khảo:* MediaPipe Solutions Guide, https://developers.google.com/edge/mediapipe/solutions/guide
