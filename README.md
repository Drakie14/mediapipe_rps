# Oẳn Tù Tì bằng cử chỉ tay — MediaPipe Hand

Ứng dụng chơi Oẳn Tù Tì (Rock – Paper – Scissors) với máy tính. Người chơi ra **Búa / Bao / Kéo** bằng tay thật trước camera, chương trình dùng **MediaPipe Hand Landmarker** lấy vị trí các khớp tay, rồi dùng thuật toán tự xây dựng để nhận diện cử chỉ và phân định thắng thua. Ai thắng 3 ván trước thì thắng trận.

```
Camera → MediaPipe Hand → 21 landmark → Thuật toán nhận diện ngón tay → Cử chỉ → Logic game → Màn hình
```

Video demo: _(dán link vào đây)_

## Cài đặt

Yêu cầu Python 3.9 trở lên và một webcam.

```bash
pip install -r requirements.txt
```

Thư viện sử dụng: `mediapipe`, `opencv-python`, `numpy`, `pillow` (vẽ chữ tiếng Việt có dấu).

## Chạy chương trình

```bash
python main.py        # dùng camera mặc định (số 0)
python main.py 1      # dùng camera khác
```

Lần chạy đầu, chương trình tự tải model `hand_landmarker.task` (~7.8 MB) vào thư mục `models/`.

Chạy kiểm thử thuật toán (không cần camera):

```bash
python test_logic.py
```

## Hướng dẫn chơi

| Phím | Chức năng |
|---|---|
| `SPACE` | Bắt đầu trận / chơi lại sau khi kết thúc |
| `1` / `3` / `5` | Chọn số ván cần thắng để thắng trận (ở màn hình chờ hoặc sau khi hết trận) |
| `M` | Bật / tắt âm thanh |
| `R` | Reset về màn hình chờ |
| `Q` / `ESC` | Thoát |

1. Nhấn `SPACE`, màn hình đếm ngược **3 – 2 – 1** ("Oẳn… tù… tì!").
2. Khi hiện **"RA TAY!"**, đưa tay ra trước camera:
   - **Búa**: nắm tay lại
   - **Bao**: xòe cả bàn tay
   - **Kéo**: duỗi ngón trỏ và ngón giữa, gập ngón áp út và ngón út
3. Máy ra tay ngẫu nhiên, màn hình hiện kết quả ván. Ván tiếp theo tự bắt đầu.
4. Ai thắng đủ số ván đã chọn (mặc định 3) trước thì thắng trận. Cuối trận có bảng thống kê; kỷ lục chuỗi thắng liên tiếp được lưu vào `records.json`.

Góc dưới màn hình hiển thị trạng thái từng ngón (DUỖI / co) và cử chỉ đang nhận diện, để thấy rõ dữ liệu từ camera được xử lý thế nào.

## Cấu trúc source code

| File | Vai trò |
|---|---|
| `hand_tracker.py` | Gọi MediaPipe: nhận frame camera, trả về 21 landmark của bàn tay |
| `gesture.py` | **Thuật toán tự xây dựng**: landmark → trạng thái ngón → cử chỉ, và bộ lọc chống nhiễu |
| `game.py` | **Logic game tự xây dựng**: máy trạng thái, bỏ phiếu cử chỉ, phân định thắng thua, tính điểm |
| `main.py` | Vòng lặp camera, nối các bước lại và vẽ giao diện |
| `test_logic.py` | Kiểm thử thuật toán và logic game bằng dữ liệu giả lập |

## Thuật toán

### 1. Dữ liệu từ MediaPipe

MediaPipe Hand Landmarker trả về 21 điểm (landmark) cho mỗi bàn tay, tọa độ `x, y` chuẩn hóa về [0, 1] theo kích thước ảnh:

- `0`: cổ tay
- Mỗi ngón có 4 điểm: MCP (gốc ngón), PIP (khớp giữa), DIP, TIP (đầu ngón).
  Ngón trỏ: 5–8, ngón giữa: 9–12, ngón áp út: 13–16, ngón út: 17–20.

### 2. Xác định ngón duỗi hay co (`finger_states`)

Với mỗi ngón (trỏ, giữa, áp út, út):

```
ngón DUỖI  ⇔  khoảng_cách(TIP, cổ tay) > 1.1 × khoảng_cách(PIP, cổ tay)
```

- Khi ngón **duỗi**, đầu ngón nằm xa cổ tay hơn khớp giữa.
- Khi ngón **co**, đầu ngón gập vào lòng bàn tay nên gần cổ tay hơn khớp giữa.
- Dùng **khoảng cách** thay vì so sánh tọa độ `y` nên thuật toán vẫn đúng khi bàn tay nghiêng hoặc xoay ngang (có test `test_rotated_hand`).
- Hệ số 1.1 là ngưỡng an toàn để ngón hơi cong không bị tính là duỗi.
- **Bỏ qua ngón cái**: ba cử chỉ đều phân biệt được bằng 4 ngón còn lại, còn ngón cái hay bị nhận sai do nó chuyển động ngang.

### 3. Phân loại cử chỉ (`classify`)

| Trạng thái 4 ngón (trỏ, giữa, áp út, út) | Cử chỉ |
|---|---|
| Không ngón nào duỗi | Búa (ROCK) |
| Cả 4 ngón duỗi | Bao (PAPER) |
| Chỉ trỏ + giữa duỗi | Kéo (SCISSORS) |
| Trường hợp khác | Không rõ → bỏ qua |

### 4. Chống nhiễu (`GestureStabilizer`)

Landmark rung nhẹ giữa các frame làm kết quả có thể nhảy liên tục. Một cử chỉ chỉ được chấp nhận khi nó **giữ nguyên trong 5 frame liên tiếp**; nếu mất tay thì bộ đệm bị xóa.

### 5. Logic game (`game.py`) — máy trạng thái

```
IDLE ──SPACE──► COUNTDOWN ──3s──► CAPTURE ──0.8s──► RESULT ──2.5s──► COUNTDOWN (ván mới)
                                                       │
                                                       └── có người đạt 3 điểm ──► GAME_OVER
```

- **CAPTURE**: trong 0.8 giây sau khi đếm xong, ghi lại mọi cử chỉ đã ổn định. Cử chỉ của người chơi là cử chỉ **xuất hiện nhiều nhất** (bỏ phiếu đa số), để lỡ ra tay chậm hoặc có vài frame sai cũng không ảnh hưởng.
- **Máy chọn ngẫu nhiên đúng lúc ra tay**, nên máy không "đọc" được tay người chơi trước.
- Không thấy tay trong lúc CAPTURE thì ván đó **không tính**, chơi lại.

### 6. Phân định thắng thua (`judge`)

Đánh số Búa = 0, Bao = 1, Kéo = 2. Mỗi lựa chọn thắng lựa chọn đứng ngay trước nó theo vòng tròn (Bao > Búa, Kéo > Bao, Búa > Kéo), nên chỉ cần tính:

```
d = (người − máy) mod 3
d = 0 → hòa,   d = 1 → người thắng,   d = 2 → máy thắng
```

Thắng một ván được 1 điểm, hòa không ai được điểm.

## Kết quả kiểm thử

- `test_logic.py`: kiểm tra phân loại 3 cử chỉ, bàn tay xoay 90°, luật thắng thua, bộ chống nhiễu, mô phỏng trọn một trận, và ván không thấy tay không được tính.
- Chạy thuật toán trên ảnh mẫu của MediaPipe:

| Ảnh | Trạng thái 4 ngón | Kết quả |
|---|---|---|
| Tay giơ chữ V (victory) | duỗi, duỗi, co, co | Kéo ✔ |
| Bàn tay xòe | duỗi × 4 | Bao ✔ |
| Nắm tay giơ ngón cái | co × 4 | Búa ✔ (bỏ qua ngón cái) |
| Chỉ giơ ngón trỏ | duỗi, co, co, co | Không rõ ✔ |

## Hạn chế và hướng phát triển

- Nhận diện kém khi thiếu sáng hoặc bàn tay quay mu tay/cạnh tay về camera, vì các ngón che nhau.
- Máy đang chọn hoàn toàn ngẫu nhiên. Có thể cho máy "học" thói quen người chơi (ví dụ đếm tần suất cử chỉ người chơi hay ra để chọn nước khắc chế).
- Có thể thêm chế độ 2 người chơi (`num_hands=2`), âm thanh, hoặc lưu bảng xếp hạng.
