# CubeTimer (CT) - Kiến trúc và thiết kế toàn bộ tính năng cơ bản

Tài liệu này là bản thiết kế tổng thể. Giai đoạn 1 (timer cốt lõi) đã xong, xem `docs/DESIGN.md`.
Từng giai đoạn tiếp theo (2 đến 6) được cài đặt riêng, KHÔNG làm nhiều giai đoạn trong một lần.
Khi làm giai đoạn nào thì chỉ làm đúng phần của giai đoạn đó, các phần khác chỉ là bối cảnh.

---

## 1. Danh sách tính năng

### Bắt buộc (làm trong Giai đoạn 2 đến 6)
1. Timer giữ Space kiểu cstimer (xong ở Giai đoạn 1)
2. Scramble generator cho 2x2, 3x3, 4x4, 5x5, 6x6, 7x7 + hiển thị scramble
3. Lưu kết quả vào SQLite, nhiều session, mỗi session gắn một loại puzzle
4. Danh sách solve, xem chi tiết, đổi penalty (OK, +2, DNF), xóa, ghi chú
5. Thống kê: best, mean of 3, ao5, ao12, ao100, mean của session, đánh dấu kỷ lục (PB)
6. Inspection 15 giây (cảnh báo ở 8s và 12s, tự +2 / DNF)
7. Nhập tay thời gian (manual entry)
8. Cài đặt (inspection, ngưỡng giữ phím, độ chính xác, ẩn thời gian khi giải, giao diện sáng/tối, cỡ chữ)
9. Biểu đồ thời gian theo solve (kèm đường ao5, ao12)
10. Hình minh họa scramble (lưới 2D của khối)
11. Xuất / nhập dữ liệu (CSV, JSON)
12. Đóng gói để chạy bằng lệnh `cubetimer` và có lối tắt trên menu Ubuntu

### Không làm trong phạm vi này
Scramble random-state cho 3x3, các puzzle không phải NxN (pyraminx, skewb, megaminx, clock, square-1),
chế độ đối kháng, đồng bộ đám mây, kết nối Stackmat/Bluetooth, giải thuật hướng dẫn giải.

---

## 2. Nguyên tắc kiến trúc

1. Ba tầng, phụ thuộc một chiều: `ui` -> `services` -> (`core`, `data`). `core` không import `ui`, `data`, hay PyQt6.
2. `core/`: logic thuần Python (timer, scramble, thống kê, định dạng, mô hình dữ liệu). Test được không cần giao diện.
3. `data/`: chỉ lo SQLite. Không chứa logic nghiệp vụ như tính thống kê.
4. `services/`: ghép core + data thành các thao tác cấp ứng dụng (thêm solve, đổi penalty, lấy thống kê). Không import PyQt6.
5. `ui/`: chỉ hiển thị và chuyển sự kiện xuống service/engine. Không tự tính thống kê, không viết SQL.
6. Mọi thứ phụ thuộc ngẫu nhiên hoặc thời gian đều phải tiêm được từ ngoài (`rng`, `clock`, `now`) để test xác định.
7. Mọi thời gian lưu và tính toán dùng số nguyên mili giây (`int`). Chỉ chuyển sang chuỗi khi hiển thị.
8. Mỗi giai đoạn phải có test pytest đi kèm và toàn bộ test phải xanh trước khi commit.

---

## 3. Cấu trúc thư mục đích

```
src/cubetimer/
  __init__.py
  __main__.py
  app.py                      # lắp ráp: tạo DB, service, MainWindow
  core/
    __init__.py
    models.py                 # Penalty, Solve, Session, SolveResult
    timer_engine.py           # TimerState, TimerEngine (mở rộng inspection ở GĐ5)
    formatting.py             # format_time, format_solve, parse_time_input
    stats.py                  # hàm thống kê thuần
    puzzles.py                # PuzzleSpec, danh sách puzzle
    scramble/
      __init__.py
      generator.py            # generate_scramble(puzzle, rng)
      cube_model.py           # mô hình sticker NxN để vẽ hình scramble
  data/
    __init__.py
    database.py               # kết nối, migration (PRAGMA user_version)
    repository.py             # SolveRepository, SessionRepository, SettingsRepository
  services/
    __init__.py
    solve_service.py          # thao tác trên solve + thống kê của session
    session_service.py        # CRUD session
    settings_service.py       # đọc/ghi cài đặt có kiểu và giá trị mặc định
    import_export.py          # CSV / JSON
  ui/
    __init__.py
    main_window.py
    timer_display.py
    scramble_bar.py
    scramble_image.py
    stats_panel.py
    solve_list.py             # model + view danh sách solve
    solve_dialog.py
    graph_widget.py
    settings_dialog.py
    manual_entry.py
    theme.py                  # bảng màu sáng/tối
tests/
  core/  data/  services/  ui/
pyproject.toml                # GĐ6
```

Dữ liệu người dùng lưu ở `$XDG_DATA_HOME/cubetimer/cubetimer.db`
(mặc định `~/.local/share/cubetimer/cubetimer.db`). Test dùng `":memory:"`.

---

## 4. Mô hình dữ liệu

### core/models.py
```python
class Penalty(IntEnum):
    OK = 0
    PLUS2 = 1
    DNF = 2

@dataclass(frozen=True)
class SolveResult:            # kết quả thô do TimerEngine trả về
    time_ms: int              # thời gian chạy, chưa cộng penalty
    penalty: Penalty = Penalty.OK   # penalty do inspection (GĐ5), mặc định OK

@dataclass
class Solve:
    id: int | None
    session_id: int
    time_ms: int
    penalty: Penalty
    scramble: str
    comment: str
    created_at: str           # ISO 8601 UTC, ví dụ "2026-10-12T09:30:00+00:00"

    @property
    def effective_ms(self) -> int | None:
        # DNF -> None; PLUS2 -> time_ms + 2000; OK -> time_ms

@dataclass
class Session:
    id: int | None
    name: str
    puzzle: str               # khóa puzzle: "222","333","444","555","666","777"
    created_at: str
```

### SQLite schema (data/database.py)
```sql
PRAGMA foreign_keys = ON;

CREATE TABLE sessions (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT NOT NULL,
  puzzle     TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE solves (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  time_ms    INTEGER NOT NULL,
  penalty    INTEGER NOT NULL DEFAULT 0,
  scramble   TEXT NOT NULL DEFAULT '',
  comment    TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);
CREATE INDEX idx_solves_session ON solves(session_id, id);

CREATE TABLE settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```
- Phiên bản schema lưu bằng `PRAGMA user_version` (bắt đầu = 1). Có hàm `migrate(conn)` chạy tuần tự các bước nâng cấp.
- Lần chạy đầu tiên nếu chưa có session nào thì tự tạo session "Session 1", puzzle "333".
- Thứ tự solve trong session là thứ tự `id` tăng dần.

---

## 5. Thiết kế core

### 5.1 Định dạng thời gian (core/formatting.py)
- `format_time(ms, digits=2)`: như Giai đoạn 1, thêm tham số `digits` (2 hoặc 3 chữ số thập phân), luôn cắt bớt (truncate), không làm tròn lên.
- `format_solve(solve, digits=2)`:
  - OK: `"12.34"`; PLUS2: `"14.34+"` (đã cộng 2 giây); DNF: `"DNF"`.
- `format_average(ms_or_none, digits=2)`:
  - None -> `"-"`; trung bình được LÀM TRÒN (nửa lên) đến 1/100 giây trước khi hiển thị; DNF -> `"DNF"`.
  - Dùng một giá trị đặc biệt `DNF = float("inf")` để biểu diễn trung bình DNF.
- `parse_time_input(text) -> int | None` (cho nhập tay):
  - `"12.34"` -> 12340; `"1:02.34"` -> 62340; `"1234"` (chỉ chữ số, không dấu chấm) -> 12.34 giây = 12340; `"102"` -> 1.02 giây = 1020.
  - Số nhập chỉ có chữ số được hiểu hai chữ số cuối là phần trăm giây.
  - Không hợp lệ, rỗng, hoặc bằng 0 -> None.

### 5.2 Thống kê (core/stats.py)
Đầu vào là danh sách `effective_ms: list[int | None]` theo thứ tự thời gian, `None` = DNF.
Trong code nội bộ thay `None` bằng `math.inf` để sắp xếp.

- `best_single(values) -> int | None`: nhỏ nhất bỏ qua DNF; nếu toàn DNF hoặc rỗng -> None.
- `mean_of(values, n) -> float | None`: lấy n phần tử CUỐI; thiếu thì None; có bất kỳ DNF -> `inf` (DNF). Dùng cho mo3.
- `average_of(values, n) -> float | None` (ao5, ao12, ao100):
  - Lấy n phần tử cuối; nếu có ít hơn n -> None.
  - Số phần tử bị loại mỗi đầu: `k = ceil(n * 0.05)` (ao5 và ao12: 1; ao100: 5).
  - Sắp xếp tăng dần (DNF = inf ở cuối), bỏ k phần tử đầu và k phần tử cuối, tính trung bình các phần tử còn lại.
  - Nếu sau khi loại vẫn còn DNF (nghĩa là số DNF > k) -> `inf` (DNF).
- `best_average_of(values, n) -> float | None`: giá trị `average_of` nhỏ nhất trên mọi cửa sổ n liên tiếp; bỏ qua cửa sổ DNF; không có cửa sổ hợp lệ -> None.
- `session_mean(values) -> float | None`: trung bình các solve không DNF; không có -> None.
- `Snapshot` (dataclass): `count`, `best`, `current`, `mo3`, `ao5`, `ao12`, `ao100`, `best_mo3`, `best_ao5`, `best_ao12`, `best_ao100`, `mean`.
- `compute_snapshot(values) -> Snapshot`.
- `detect_pbs(before: Snapshot, after: Snapshot) -> set[str]`: trả về tập tên chỉ số vừa lập kỷ lục mới trong `{"single","mo3","ao5","ao12","ao100"}` (chỉ khi `before` đã có giá trị cùng loại hoặc đây là lần đầu có giá trị; lần đầu tiên có single thì không tính là PB).

Quy tắc hiệu năng: tính lại toàn bộ từ đầu là chấp nhận được đến khoảng 10.000 solve.
Không cần tối ưu sớm hơn.

### 5.3 Puzzle và scramble

`core/puzzles.py`:
```python
@dataclass(frozen=True)
class PuzzleSpec:
    key: str        # "333"
    name: str       # "3x3x3"
    size: int       # 3
    length: int     # số nước của scramble

PUZZLES = {"222": (2, 11), "333": (3, 20), "444": (4, 40),
           "555": (5, 60), "666": (6, 80), "777": (7, 100)}
```
Có hàm `get_puzzle(key)` ném `KeyError` rõ ràng nếu khóa lạ.

`core/scramble/generator.py`: `generate_scramble(puzzle_key: str, rng: random.Random | None = None) -> str`

Quy tắc sinh scramble kiểu random-move:
- Ba trục: (U, D), (R, L), (F, B).
- Mỗi nước đi chọn: trục, mặt trong trục, số lớp k, hậu tố (`""`, `"'"`, `"2"`).
- Trục của nước đi KHÔNG được trùng trục của nước đi liền trước.
- 2x2: chỉ dùng các mặt U, R, F (không dùng D, L, B), không có nước lớp trong.
- NxN với N >= 3: các mặt U D R L F B. Với N >= 4 thêm nước nhiều lớp theo ký hiệu WCA:
  - k = 1: `"R"`; k = 2: `"Rw"`; k >= 3: `"3Rw"`, `"4Rw"`...
  - k chạy từ 1 đến `N // 2` (lớp giữa của N lẻ không bao giờ được xoay độc lập).
- Mỗi nước đi chọn đều trong tập (mặt, k) hợp lệ của trục đã chọn, rồi chọn đều hậu tố.
- Kết quả là các nước ngăn bằng một dấu cách, không có dấu cách thừa ở đầu/cuối.
- Cùng `rng` đã seed thì cùng kết quả.

`core/scramble/cube_model.py` (dùng cho hình minh họa, Giai đoạn 6):
- `CubeModel(size)` lưu 6 mặt, mỗi mặt N x N số nguyên 0..5 (U=0, R=1, F=2, D=3, L=4, B=5).
- `apply(scramble: str)`, `apply_move(move: str)` hỗ trợ đầy đủ ký hiệu ở trên, bao gồm nhiều lớp và hậu tố.
- `faces() -> dict[str, list[list[int]]]`.
- Các phép kiểm tra bắt buộc: khối mới tạo là đã giải; `R` rồi `R'` về lại như cũ; 4 lần `R` về lại như cũ;
  `(R U R' U')` lặp 6 lần về lại như cũ (3x3); `Rw` trên 4x4 đổi chỗ đúng hai lớp ngoài cùng.

### 5.4 TimerEngine (mở rộng ở Giai đoạn 3 và 5)
Hợp đồng giữ nguyên Giai đoạn 1, thêm:

Giai đoạn 3:
- Mọi phương thức làm timer DỪNG (`on_space_press`, `on_other_key_press` trong RUNNING) trả về `SolveResult` thay vì `None`. Các trường hợp khác trả `None`.
- Thêm `cancel()` (phím Esc khi RUNNING/INSPECTING/HOLDING/READY): về IDLE và KHÔNG sinh kết quả.

Giai đoạn 5 (inspection), khi `inspection_enabled = True`:
- Thêm hai trạng thái: `ARMING` và `INSPECTING`.
- Bảng chuyển trạng thái bổ sung:

| Trạng thái | Sự kiện | -> Trạng thái | Ghi chú |
|---|---|---|---|
| IDLE hoặc STOPPED | space_press | ARMING | chưa bắt đầu đếm |
| ARMING | space_release | INSPECTING | bắt đầu đếm 15 giây |
| ARMING | cancel | IDLE | |
| INSPECTING | space_press | HOLDING | cho phép giữ để chuẩn bị chạy |
| HOLDING | space_release (chưa đủ 0.3s) | INSPECTING | quay về, đồng hồ inspection vẫn chạy |
| HOLDING (từ INSPECTING) | update đủ 0.3s | READY | |
| READY | space_release | RUNNING | ghi penalty theo thời gian inspection |
| INSPECTING | update khi vượt 17 giây | STOPPED | kết quả DNF, `time_ms = 0` |

- Penalty tính tại thời điểm thả Space để chạy: inspection <= 15 giây -> OK; trên 15 đến 17 giây -> PLUS2; trên 17 giây -> DNF.
- `inspection_remaining_s() -> int`: số giây còn lại (làm tròn lên), nhỏ nhất bằng 0.
- `inspection_elapsed_ms() -> int`.
- Khi `inspection_enabled = False`, mọi hành vi giữ nguyên Giai đoạn 1.
- Engine không phát âm thanh. UI hiển thị cảnh báo ở giây thứ 8 và 12.

---

## 6. Tầng data và services

### data/repository.py
Mỗi repository nhận một `sqlite3.Connection` (đã bật foreign_keys, `row_factory = sqlite3.Row`).

- `SessionRepository`: `create(name, puzzle) -> Session`, `get(id)`, `list_all() -> list[Session]`, `rename(id, name)`, `set_puzzle(id, puzzle)`, `delete(id)`.
- `SolveRepository`: `add(solve) -> Solve` (gán id), `get(id)`, `list_by_session(session_id) -> list[Solve]` (theo id tăng), `update_penalty(id, penalty)`, `update_comment(id, comment)`, `delete(id)`, `delete_by_session(session_id)`, `count(session_id)`.
- `SettingsRepository`: `get(key) -> str | None`, `set(key, value)`, `all() -> dict[str, str]`.
- Mỗi thao tác ghi gọi `commit()` ngay.

### services
`SolveService(solve_repo, clock=utcnow)`:
- `add_result(session_id, result: SolveResult, scramble: str) -> Solve`.
- `add_manual(session_id, time_ms, scramble: str) -> Solve`.
- `set_penalty(solve_id, penalty)`, `set_comment(solve_id, text)`, `delete(solve_id)`, `delete_last(session_id) -> Solve | None`.
- `list(session_id) -> list[Solve]`.
- `snapshot(session_id) -> Snapshot`: gọi `core.stats.compute_snapshot` trên `effective_ms` của session.
- `add_result_with_pbs(...) -> tuple[Solve, set[str]]`: tính snapshot trước và sau, trả về cả tập PB mới.

`SessionService(session_repo, solve_repo)`:
- `ensure_default() -> Session`, `create(name, puzzle)`, `rename`, `change_puzzle`, `delete`, `reset(session_id)` (xóa mọi solve nhưng giữ session), `list()`.
- Không cho xóa session cuối cùng: phải luôn còn ít nhất một session.

`SettingsService(settings_repo)`:
- Đọc/ghi có kiểu, mặc định:

| Khóa | Kiểu | Mặc định |
|---|---|---|
| `inspection_enabled` | bool | False |
| `hold_threshold_ms` | int | 300 (giới hạn 100 đến 1000) |
| `time_digits` | int | 2 (chỉ 2 hoặc 3) |
| `hide_time_while_running` | bool | False |
| `show_scramble_image` | bool | True |
| `manual_entry_mode` | bool | False |
| `confirm_delete` | bool | True |
| `theme` | str | "dark" ("dark" hoặc "light") |
| `timer_font_pt` | int | 96 (giới hạn 40 đến 200) |
| `current_session_id` | int | session đầu tiên |

- Giá trị lưu trong DB không hợp lệ thì dùng mặc định, không ném lỗi.

`import_export.py`:
- CSV: cột `session,puzzle,time_ms,penalty,scramble,comment,created_at`, mã hóa UTF-8, penalty là số 0/1/2.
- JSON: `{"version":1,"sessions":[{"name":..,"puzzle":..,"solves":[{...}]}]}`.
- `export_session_csv(session_id, path)`, `export_all_json(path)`.
- `import_csv(path) -> int` (tạo session mới tên theo tên file, trả số solve nhập được), `import_json(path) -> int`.
- Dòng lỗi định dạng thì bỏ qua và đếm, không làm hỏng toàn bộ lần nhập.

---

## 7. Thiết kế giao diện

### Bố cục cửa sổ chính
```
+--------------------------------------------------------------+
| Menu: File | Session | View | Help                           |
+----------------+---------------------------------------------+
| [Session v]    | Scramble (chữ, tự xuống dòng, cỡ vừa)  [<][>]|
| [Puzzle v]     |                                             |
+----------------+              12.34                          |
| Thống kê       |        (nhãn thời gian cỡ lớn)              |
|  single  cur/best                                            |
|  mo3  ao5 ao12 ao100                                         |
|  mean  count   |  [Hình scramble]      [Biểu đồ]  (tab)     |
+----------------+                                             |
| Danh sách solve|                                             |
|  # | time | ao5| ao12                                        |
+----------------+---------------------------------------------+
| Statusbar: hướng dẫn phím / thông báo PB                     |
+--------------------------------------------------------------+
```
- Dùng `QSplitter` ngang: cột trái (session, thống kê, danh sách) và vùng giữa (scramble, timer, hình/biểu đồ).
- Cột trái ẩn/hiện được qua menu View.

### Vấn đề bắt buộc xử lý: phím Space
Các widget như `QPushButton`, `QTableView`, `QComboBox` sẽ nuốt phím Space khi đang có focus.
Cách làm:
- Đặt `setFocusPolicy(Qt.NoFocus)` cho các widget không cần nhập chữ.
- Cài một event filter lên `MainWindow` để bắt Space và Esc ở cấp cửa sổ, chỉ bỏ qua khi focus đang nằm trong `QLineEdit`, `QTextEdit`, hoặc một hộp thoại đang mở.
- Luôn bỏ qua `event.isAutoRepeat() == True`.

### Phím tắt
| Phím | Tác dụng |
|---|---|
| Space | điều khiển timer như Giai đoạn 1 |
| Esc | `cancel()`: hủy lượt đang chạy, không lưu; ở trạng thái STOPPED thì đưa màn hình về 0.00 |
| Ctrl+1 / Ctrl+2 / Ctrl+3 | đặt OK / +2 / DNF cho solve cuối cùng |
| Ctrl+Z | xóa solve cuối cùng (có xác nhận nếu `confirm_delete`) |
| Ctrl+N | session mới |
| Ctrl+, | mở cài đặt |
| Ctrl+Q | thoát |

Các phím Ctrl+1/2/3 và Ctrl+Z chỉ hoạt động khi timer ở IDLE hoặc STOPPED.

### Quy tắc hiển thị thời gian
- Trạng thái STOPPED hiển thị `format_solve` của solve vừa lưu (có `+` hoặc `DNF` nếu có penalty).
- Khi RUNNING và `hide_time_while_running` bật: hiển thị `...` thay vì số.
- INSPECTING: hiển thị số giây còn lại (15, 14, ...); ở giây 8 và 12 đổi màu cam một lúc để cảnh báo; quá 15 giây hiển thị `+2`; quá 17 giây hiển thị `DNF`.
- Màu: IDLE/STOPPED trắng, ARMING trắng, HOLDING đỏ, READY xanh lá, RUNNING trắng, INSPECTING vàng nhạt. Giao diện sáng dùng cặp màu tương phản tương ứng.

### Các widget
- `ScrambleBar`: nhãn scramble, nút "mới" (tạo scramble mới), nút "trước" (xem scramble trước đó của session, chỉ để xem, không quay lại giải).
- `StatsPanel`: bảng nhỏ với các hàng single, mo3, ao5, ao12, ao100, và dòng mean/count; hai cột "hiện tại" và "tốt nhất". Ô vừa lập kỷ lục được tô nổi bật cho đến lượt giải kế tiếp.
- `SolveListModel` (`QAbstractTableModel`) + `QTableView`: cột #, Thời gian, ao5, ao12; cuộn tới solve mới nhất. Nhấp đúp mở `SolveDialog`. Menu chuột phải: OK, +2, DNF, Xóa.
- `SolveDialog`: hiển thị thời gian, penalty (nhóm nút chọn), scramble, thời điểm giải, ô ghi chú, nút Xóa, nút Lưu.
- `ScrambleImageWidget`: vẽ lưới 2D (dạng chữ thập) bằng `QPainter` từ `CubeModel`.
- `GraphWidget`: vẽ bằng `QPainter`, trục X là thứ tự solve, trục Y là giây; điểm cho từng solve, đường ao5 và ao12; DNF vẽ dạng dấu X ở mức cao nhất. Không thêm thư viện vẽ đồ thị ngoài.
- `ManualEntryWidget`: ô nhập chữ thay thế vùng timer khi `manual_entry_mode` bật; Enter để lưu bằng `parse_time_input`; nhập sai thì viền đỏ.
- `SettingsDialog`: chỉnh toàn bộ các khóa trong bảng cài đặt; áp dụng ngay khi bấm OK.

### Luồng khi hoàn thành một solve
1. Engine trả `SolveResult` (từ `on_space_press` hoặc `on_other_key_press`).
2. UI lấy scramble hiện tại, gọi `SolveService.add_result_with_pbs(...)`.
3. UI cập nhật: nhãn thời gian, danh sách, thống kê, biểu đồ; nếu có PB thì hiển thị trên thanh trạng thái.
4. UI gọi `generate_scramble(session.puzzle)` để lấy scramble mới.

---

## 8. Kế hoạch giai đoạn

Giai đoạn 1: xong.

### Giai đoạn 2: Scramble
Làm: `core/puzzles.py`, `core/scramble/generator.py`, `ScrambleBar` trong `ui/`, tích hợp vào `MainWindow` (hiển thị scramble trên timer, nút "mới", tự tạo scramble mới sau mỗi solve).
Chưa có session/puzzle thật: tạm dùng puzzle "333" cố định.
Test: số nước đúng với `length` của từng puzzle; không có hai nước liên tiếp cùng trục; 2x2 chỉ có U R F; cú pháp mọi nước khớp biểu thức chính quy; cùng seed cho cùng kết quả; 4x4 có xuất hiện nước `Rw`, 5x5 và 6x6 và 7x7 có xuất hiện nước `3Rw` trong ít nhất một scramble khi sinh nhiều lần với seed cố định.
Hoàn thành khi: pytest xanh, chạy app thấy scramble, solve xong thì scramble đổi.

### Giai đoạn 3: Lưu trữ, session, danh sách solve, penalty
Làm: `core/models.py`, `data/` (database + repository), `services/solve_service.py`, `services/session_service.py`, mở rộng `TimerEngine` (trả `SolveResult`, thêm `cancel()`), `SolveListModel`, `SolveDialog`, chọn session và puzzle trong UI, tạo/đổi tên/xóa/reset session, phím Ctrl+1/2/3 và Ctrl+Z, `core/formatting.py` thêm `format_solve`.
Test: repository trên `":memory:"` (thêm, lấy, sửa penalty, xóa, xóa dây chuyền khi xóa session, không cho xóa session cuối); `effective_ms` đúng cho ba loại penalty; `TimerEngine` trả `SolveResult` đúng và `cancel()` không trả gì; `migrate` tạo đúng schema.
Hoàn thành khi: đóng và mở lại app thì solve vẫn còn; đổi puzzle của session thì scramble mới theo puzzle đó.

### Giai đoạn 4: Thống kê
Làm: `core/stats.py`, `SolveService.snapshot`, `add_result_with_pbs`, `StatsPanel`, cột ao5/ao12 trong danh sách, thông báo PB trên thanh trạng thái, `format_average`.
Test: bảng ví dụ cố định cho `average_of` (ao5 với 5 giá trị biết trước, ao12 có một DNF, ao5 có hai DNF -> DNF, thiếu dữ liệu -> None); `best_average_of`; `session_mean` bỏ qua DNF; `detect_pbs`; tất cả solve DNF thì best là None.
Hoàn thành khi: số liệu trong panel khớp với tính tay trên một chuỗi ví dụ do bạn kiểm tra.

### Giai đoạn 5: Inspection, nhập tay, cài đặt
Làm: `services/settings_service.py`, `ui/settings_dialog.py`, mở rộng `TimerEngine` theo mục 5.4, hiển thị inspection, `parse_time_input`, `ManualEntryWidget`, ẩn thời gian khi giải, độ chính xác 2 hoặc 3 chữ số, ngưỡng giữ phím tùy chỉnh, chủ đề sáng/tối (`ui/theme.py`), cỡ chữ.
Test: engine với clock giả cho inspection (thả sớm trong 15s, thả ở 16s -> PLUS2, thả ở 18s -> DNF, giữ chưa đủ ngưỡng thì quay lại INSPECTING); `parse_time_input` với các ví dụ ở mục 5.1; `SettingsService` trả mặc định khi giá trị hỏng và giới hạn đúng khoảng.
Hoàn thành khi: bật inspection thì đếm ngược đúng và kết quả có penalty tự động.

### Giai đoạn 6: Biểu đồ, hình scramble, xuất nhập, đóng gói
Làm: `cube_model.py` + `ScrambleImageWidget`, `GraphWidget`, `services/import_export.py` (menu File), `pyproject.toml` với entry point `cubetimer`, tệp `cubetimer.desktop`, cập nhật `README.md`.
Test: các phép kiểm tra `CubeModel` ở mục 5.3; xuất rồi nhập CSV và JSON cho ra cùng dữ liệu; dòng lỗi khi nhập bị bỏ qua và được đếm.
Hoàn thành khi: `pip install -e .` rồi gõ `cubetimer` mở được app, xuất và nhập dữ liệu hoạt động.

---

## 9. Quy ước code
- Python 3.10 trở lên, có type hints cho hàm công khai, `from __future__ import annotations` ở đầu mỗi file.
- Mỗi module công khai có docstring ngắn; hàm có logic không hiển nhiên thì có comment giải thích vì sao.
- Không dùng biến toàn cục có trạng thái. Không dùng `time.sleep` trong UI; dùng `QTimer`.
- Không bắt `Exception` chung chung; chỉ bắt lỗi cụ thể và chỉ khi có cách xử lý rõ ràng.
- Test UI (nếu viết) dùng `pytest-qt` với `QT_QPA_PLATFORM=offscreen`; test core và data không được import PyQt6.
- Thêm vào `requirements.txt` chỉ những gói thật sự dùng: `PyQt6`, `pytest`, `pytest-qt` (khi bắt đầu viết test UI).
- Mỗi giai đoạn xong: `pytest` xanh, chạy thử app bằng tay, rồi commit và push.
