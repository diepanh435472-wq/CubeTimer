# CubeTimer (CT) - Thiết kế Giai đoạn 1: Timer cốt lõi

## Mục tiêu
Cửa sổ PyQt6 hiển thị đồng hồ bấm giờ Rubik kiểu cstimer:
giữ Space -> đỏ -> (0.3s) xanh -> thả Space -> chạy -> bấm Space -> dừng.

## Nguyên tắc kiến trúc
- Logic timer nằm trong `core/`, KHÔNG import PyQt6 (để test được bằng pytest).
- `ui/` chỉ lo hiển thị và chuyển sự kiện phím cho engine.
- Engine nhận đồng hồ qua tham số (`clock`), mặc định `time.perf_counter`, để test giả lập thời gian.

## Cấu trúc file
```
src/cubetimer/
  __init__.py
  __main__.py            # python -m cubetimer -> khởi chạy app
  core/
    __init__.py
    timer_engine.py      # TimerState, TimerEngine
    formatting.py        # format_time(ms) -> str
  ui/
    __init__.py
    main_window.py       # MainWindow (QMainWindow)
tests/
  test_timer_engine.py
  test_formatting.py
```

## core/timer_engine.py

### TimerState (Enum)
IDLE, HOLDING, READY, RUNNING, STOPPED

### TimerEngine
- `__init__(self, clock=time.perf_counter, hold_threshold=0.3)`
- Thuộc tính đọc: `state`, `last_time_ms` (kết quả lần giải gần nhất, None nếu chưa có)
- `on_space_press()`
- `on_space_release()`
- `on_other_key_press()`  # phím khác trong lúc RUNNING cũng dừng timer
- `reset()`  # về IDLE, xóa thời gian hiển thị
- `elapsed_ms() -> int`   # RUNNING: tính từ lúc bắt đầu; STOPPED: thời gian đã chốt; còn lại: 0
- `update()`  # gọi định kỳ từ UI; nếu HOLDING và đã giữ >= hold_threshold -> READY

### Bảng chuyển trạng thái
| Trạng thái | Sự kiện | -> Trạng thái | Ghi chú |
|---|---|---|---|
| IDLE | space_press | HOLDING | ghi mốc thời gian bắt đầu giữ |
| HOLDING | space_release | IDLE | thả sớm, hủy |
| HOLDING | update (đủ 0.3s) | READY | |
| READY | space_release | RUNNING | ghi mốc start |
| RUNNING | space_press hoặc phím khác | STOPPED | chốt `last_time_ms`; dừng NGAY khi nhấn, không đợi thả |
| STOPPED | space_press | HOLDING | bắt đầu lượt mới |
| STOPPED | space_release | STOPPED | bỏ qua (đây là lần thả của phím vừa dừng timer) |
| bất kỳ | reset | IDLE | |

Mọi (trạng thái, sự kiện) không có trong bảng thì bỏ qua, không báo lỗi.

## core/formatting.py
`format_time(ms: int) -> str`
- dưới 60s: `S.cc` -> 0 ms = `0.00`, 9876 ms = `9.87`, 12340 ms = `12.34`
- từ 60s: `M:SS.cc` -> 61230 ms = `1:01.23`
- làm tròn xuống (cắt) phần trăm giây, KHÔNG làm tròn lên.

## ui/main_window.py
- `QMainWindow`, tiêu đề "CubeTimer", kích thước tối thiểu 600x400, nền tối.
- Một `QLabel` lớn ở giữa hiển thị thời gian, font monospace khoảng 96pt.
- Màu chữ theo trạng thái: IDLE/STOPPED trắng, HOLDING đỏ, READY xanh lá, RUNNING trắng.
- `QTimer` chu kỳ 10 ms: gọi `engine.update()` rồi cập nhật label bằng `format_time(engine.elapsed_ms())`.
- Khi HOLDING hoặc READY: label hiển thị `0.00`.
- Xử lý phím trong `keyPressEvent` / `keyReleaseEvent`:
  - BỎ QUA mọi sự kiện có `event.isAutoRepeat() == True`.
  - Space -> `on_space_press` / `on_space_release`.
  - Esc -> `reset()`.
  - Phím khác khi RUNNING -> `on_other_key_press()`.
- Thanh trạng thái (statusbar) có dòng hướng dẫn: "Giữ Space -> thả để bắt đầu | Esc: reset".

## __main__.py
Tạo `QApplication`, hiện `MainWindow`, chạy event loop.
Cách chạy: `PYTHONPATH=src python -m cubetimer`

## Test (pytest)
Dùng clock giả (biến thời gian tự tăng tay). Phải có các case:
1. Giữ đủ 0.3s rồi thả -> RUNNING.
2. Giữ 0.1s rồi thả -> về IDLE, không chạy.
3. RUNNING + space_press -> STOPPED, `last_time_ms` đúng theo clock giả.
4. Sau STOPPED, space_release không đổi trạng thái.
5. STOPPED + space_press -> HOLDING (lượt mới).
6. Phím khác khi RUNNING cũng dừng.
7. reset() từ mọi trạng thái về IDLE.
8. `format_time`: 0, 9876, 12340, 59999, 60000, 61230.

## Ngoài phạm vi Giai đoạn 1 (KHÔNG làm)
Scramble, lưu kết quả, thống kê, +2/DNF, nhiều session, cài đặt, inspection 15s.

## Tiêu chí hoàn thành
- `pytest` xanh toàn bộ.
- Chạy app: giữ Space thấy đỏ rồi xanh, thả thì số chạy, bấm Space dừng và hiện đúng thời gian.