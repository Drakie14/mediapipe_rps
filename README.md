# Oẳn Tù Tì bằng cử chỉ tay — MediaPipe Hand

Chơi Oẳn Tù Tì (Búa – Bao – Kéo) với máy tính bằng **tay thật trước webcam**. Chương trình dùng **MediaPipe Hand Landmarker** lấy vị trí các khớp tay, rồi dùng thuật toán tự xây dựng để nhận diện cử chỉ và phân định thắng thua.

```
Camera → MediaPipe Hand → 21 landmark → Thuật toán nhận diện ngón tay → Cử chỉ → Logic game → Màn hình
```

## Cần chuẩn bị

- Máy tính **Windows, macOS hoặc Linux** có **webcam**.
- **Python 3.9 – 3.13** (khuyên dùng 3.12). Tải tại <https://www.python.org/downloads/>.
  - Trên Windows, khi cài nhớ tick ô **"Add python.exe to PATH"**.
  - Kiểm tra đã cài: mở Terminal / PowerShell và gõ `python --version` (macOS/Linux dùng `python3 --version`).
- Kết nối Internet cho lần chạy đầu (để tải thư viện và model ~7.8 MB).

## Bước 1 — Tải game về

**Cách A: dùng Git**

```bash
git clone https://github.com/Drakie14/mediapipe_rps.git
cd mediapipe_rps
```

**Cách B: không cần Git**

1. Vào <https://github.com/Drakie14/mediapipe_rps>, bấm nút xanh **Code → Download ZIP**.
2. Giải nén, rồi mở Terminal / PowerShell **bên trong thư mục vừa giải nén**
   (Windows: mở thư mục, gõ `powershell` vào thanh địa chỉ rồi Enter).

## Bước 2 — Cài thư viện (chỉ làm một lần)

Tạo môi trường ảo riêng cho game để không ảnh hưởng các chương trình Python khác.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Thư viện được cài: `mediapipe`, `opencv-python`, `numpy`, `pillow`.

## Bước 3 — Chạy game

**Windows:**

```powershell
.venv\Scripts\python.exe main.py
```

**macOS / Linux:**

```bash
.venv/bin/python main.py
```

- Lần chạy đầu, game tự tải model `hand_landmarker.task` vào thư mục `models/`.
- Máy có nhiều camera: thêm số thứ tự camera vào cuối lệnh, ví dụ `main.py 1`.

## Cách chơi

| Phím | Chức năng |
|---|---|
| `SPACE` | Bắt đầu trận / chơi lại sau khi kết thúc |
| `1` / `3` / `5` | Chọn số ván cần thắng để thắng trận (ở màn hình chờ hoặc sau khi hết trận) |
| `M` | Bật / tắt âm thanh |
| `R` | Reset về màn hình chờ |
| `Q` / `ESC` | Thoát |

1. Nhấn `SPACE`, màn hình đếm ngược **3 – 2 – 1** ("Oẳn… tù… tì!").
2. Khi hiện **"RA TAY!"**, đưa tay ra trước camera, lòng bàn tay hướng về camera:
   - **Búa**: nắm tay lại
   - **Bao**: xòe cả bàn tay
   - **Kéo**: duỗi ngón trỏ và ngón giữa, gập ngón áp út và ngón út
3. Màn hình hiện kết quả ván, ván tiếp theo tự bắt đầu.
4. Ai thắng đủ số ván đã chọn (mặc định 3) trước thì thắng trận. Cuối trận có bảng thống kê; kỷ lục chuỗi thắng được lưu vào `records.json`.

Góc dưới màn hình hiển thị trạng thái từng ngón (duỗi / co) và cử chỉ đang nhận diện.

**Mẹo:** ngồi chỗ đủ sáng, để cả bàn tay nằm trong khung hình.

## Gặp lỗi?

| Hiện tượng | Cách xử lý |
|---|---|
| `python` không được nhận ra (Windows) | Cài lại Python và tick **"Add python.exe to PATH"**, rồi mở PowerShell mới. |
| Báo `Khong mo duoc camera 0` | Đóng các app đang dùng camera (Zoom, Meet, Camera…). Thử `main.py 1`. Kiểm tra quyền camera: Windows *Settings → Privacy & security → Camera*; macOS *System Settings → Privacy & Security → Camera* (cho phép Terminal). |
| Chạy trong **WSL** không thấy camera | WSL không truy cập được webcam. Hãy chạy bằng PowerShell trên Windows theo hướng dẫn ở trên. |
| `pip install` báo không tìm thấy bản `mediapipe` phù hợp | Phiên bản Python quá mới hoặc quá cũ. Cài Python 3.12 rồi làm lại Bước 2. |
| PowerShell chặn script khi chạy `activate` | Không cần activate: dùng trực tiếp `.venv\Scripts\python.exe` như các lệnh ở trên. |

Chạy kiểm thử thuật toán (không cần camera):

```bash
python test_logic.py
```

## Cấu trúc source code

| File | Vai trò |
|---|---|
| `hand_tracker.py` | Gọi MediaPipe: nhận frame camera, trả về 21 landmark của bàn tay |
| `gesture.py` | Thuật toán: landmark → trạng thái ngón → cử chỉ, và bộ lọc chống nhiễu |
| `game.py` | Logic game: máy trạng thái, bỏ phiếu cử chỉ, phân định thắng thua, tính điểm |
| `main.py` | Vòng lặp camera, nối các bước lại và vẽ giao diện |
| `ui.py`, `icons.py`, `sound.py` | Giao diện, biểu tượng và âm thanh |
| `test_logic.py` | Kiểm thử thuật toán và logic game bằng dữ liệu giả lập |

## Thuật toán nhận diện cử chỉ

MediaPipe trả về 21 điểm cho mỗi bàn tay (`0` là cổ tay; mỗi ngón có 4 điểm từ gốc tới đầu ngón). Với mỗi ngón trỏ, giữa, áp út, út:

```
ngón DUỖI  ⇔  khoảng_cách(đầu ngón, cổ tay) > 1.1 × khoảng_cách(khớp giữa, cổ tay)
```

Dùng khoảng cách thay vì tọa độ nên vẫn đúng khi bàn tay nghiêng. Ngón cái được bỏ qua vì hay bị nhận sai.

| Trạng thái 4 ngón (trỏ, giữa, áp út, út) | Cử chỉ |
|---|---|
| Không ngón nào duỗi | Búa |
| Cả 4 ngón duỗi | Bao |
| Chỉ trỏ + giữa duỗi | Kéo |
| Trường hợp khác | Không rõ → bỏ qua |

Một cử chỉ chỉ được chấp nhận khi giữ nguyên **5 frame liên tiếp**; trong 0.8 giây "RA TAY!", cử chỉ xuất hiện nhiều nhất được tính là tay của người chơi. Không thấy tay thì ván đó không tính.

Luật thắng thua: đánh số Búa = 0, Bao = 1, Kéo = 2, tính `d = (người − máy) mod 3`: `0` hòa, `1` người thắng, `2` máy thắng.
