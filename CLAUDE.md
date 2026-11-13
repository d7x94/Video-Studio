# Quy tắc khi sửa repo này

Repo là bản gốc của skill `video-studio`. Thư mục `video-studio/` phải luôn đúng như sẽ cài vào claude.ai.

- Trao đổi và viết tài liệu bằng tiếng Việt. Ghi chú trong script viết không dấu (giữ như các file hiện có).
- Không sửa tay `video-studio/assets/lineart/lineart.js`. Sửa nguồn trong `assets/lineart/src/` rồi chạy `bash tools/build_lineart.sh`, commit cả nguồn và file build.
- Dàn nhân vật line-art (`assets/lineart/src/cast/roster.ts`) và dàn 3D đã khóa: chỉ đổi khi người dùng yêu cầu rõ, và cập nhật bảng trong `references/nhan-vat-line-art.md` cùng lúc.
- Đổi quy trình, script hay template thì chạy thử trọn một video mẫu trước khi commit: `setup.sh`, `tts.py`, `new_project.sh` (khổ và kiểu hình bị ảnh hưởng), `inject.py`, `hyperframes check` 0 lỗi, `render.sh`, `check_output.py` ĐẠT. Ghi số đo thời gian render mới vào tài liệu nếu khác.
- Không ghi số liệu, phiên bản, cờ lệnh chưa kiểm chứng. Phiên bản công cụ ghim trong `scripts/setup.sh` và `tools/build_lineart.sh`; đổi pin thì chạy lại thử đầu cuối.
- Không đưa vào repo: video, file giọng đọc, dự án từng video, mô hình tải về, thông tin cá nhân.
- Sau khi gộp vào `main`, Actions tự đóng gói Release `latest`; nhắc người dùng tải zip lên claude.ai.
