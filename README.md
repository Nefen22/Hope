# Hope
A plaform game for Assigment in HCMUT

## 2D Platformer Game – Cocos2d

Đây là dự án Bài Tập Lớn xây dựng một game platformer 2D sử dụng Cocos2d theo phong cách side-scrolling (mô hình tương tự Mario).

### Yêu cầu cần thực hiện
Bản đồ & Di chuyển

Bản đồ có kích thước lớn hơn màn hình ít nhất 4 lần.

Camera theo sát nhân vật khi di chuyển theo trục ngang.

Cơ chế di chuyển gồm: đi trái/phải, nhảy, chịu tác động của trọng lực.

Xử lý va chạm với nền tảng và vật cản.

### Tương tác với đối tượng

Tiêu diệt kẻ địch bằng cách nhảy lên đầu.

Đập vỡ các khối chứa vật phẩm để nâng cấp nhân vật.

Thu thập tiền để tăng điểm.

Đối tượng đặc biệt

Boss cuối màn với cơ chế riêng.

Vật phẩm đặc biệt (ví dụ: trạng thái bất tử tạm thời).

### Âm thanh & Menu

Nhạc nền và hiệu ứng âm thanh khi tương tác.

Menu chính gồm: New Game, Options, About, Exit.

### Kỹ thuật sử dụng

Kiến trúc scene graph của Cocos2d.

Lập trình hướng đối tượng (Player, Enemy, Item, Map, UI).

Quản lý trạng thái nhân vật (Idle, Run, Jump, Attack, Dead).

Hệ thống va chạm và xử lý logic gameplay.

Camera follow theo nhân vật.

Tổ chức code theo hướng module hóa.


#####

Tạo môi trường:
python3 -m venv .venv

Kích hoạt môi trường:
source .venv/bin/activate

Chạy game:
python3 game.py