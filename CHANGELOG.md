# Nhật ký thay đổi

Quy ước số phiên bản `MAJOR.MINOR.PATCH`, ghi ở `video-studio/VERSION` và dòng "Phiên bản skill" trong `video-studio/SKILL.md` (hai nơi phải khớp, CI kiểm tra khi đóng gói). Thêm kiểu hình hoặc tính năng thì tăng MINOR; sửa lỗi thì tăng PATCH; đổi lớn làm hỏng cách dùng cũ thì tăng MAJOR. Mỗi lần gộp PR thay đổi skill: tăng số, sửa hai nơi trên và thêm mục mới ở đầu file này.

## [1.1.0] - 2026-11-14

- Kiểu `ve-net`: bàn tay cầm bút đổi từ SVG vẽ bằng code sang ảnh PNG (`assets/venet/hand.png`, `hand-shadow.png`), do người dùng tạo bằng Grok; `new_project.sh` chép ảnh vào `build/<khổ>/assets/`.
- Bàn tay cử động tự nhiên hơn: cổ tay xoay theo vị trí, nhấc bút theo đường cong khi chuyển nét, bóng đổ lùi xa khi nhấc, rung nhẹ tất định.
- Thêm `tools/tach_ban_tay.py` để tách nền ảnh bàn tay mới.
- Ghi công ảnh bàn tay trong README và `references/ve-net.md`.
- Đã chạy thử trọn video mẫu 124 giây (Mac mini M6, 11 cảnh): lồng tiếng, `inject.py`, `hyperframes check` 0 lỗi, `render.sh` bản xem trước khổ dọc khoảng 340 giây (2,7 giây cho mỗi giây video), `check_output.py` ĐẠT. Chưa thử khổ ngang.

## [1.0.0] - 2026-11-14

Mốc phiên bản đầu tiên, tính từ trạng thái `main` tại commit `fcf0306`. Gần nhất trước mốc này:

- Thêm lớp tính cách (cách diễn) cho vai.
- Thêm thư viện hồ sơ vai và đổi skin theo cảnh.
- Sửa `chuan_am.sh` làm hỏng bản gốc không nhạc, `setup.sh` cài lại khi đổi pin, kiểm `venet-chu.js` trong CI.
