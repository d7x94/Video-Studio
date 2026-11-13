# Giọng đọc VieNeu-TTS v3 Turbo

Giấy phép Apache-2.0. Âm thanh 48 kHz. Chạy CPU qua ONNX (int8 nếu CPU có VNNI, không thì fp32). Có watermark âm thanh mặc định. Liệt kê lại trong môi trường hiện tại: `python3 SKILL/scripts/tts.py --list-voices`.

Mặc định của người dùng: **Mai Anh**.

| Giọng | Giới | Miền | Phong cách | Gợi ý dùng |
|---|---|---|---|---|
| Mai Anh | Nữ | Bắc | Tin tức | Mặc định; sức khỏe |
| Minh Đức | Nam | Bắc | Tin tức | Thủ tục |
| Thùy Dung | Nữ | Nam | Tin tức | Sức khỏe, khán giả phía Nam |
| Minh Triết | Nam | Nam | Tin tức | Thủ tục, khán giả phía Nam |
| Trúc Ly | Nữ | Bắc | Tự nhiên | Kiến thức, review |
| Hải Đăng | Nam | Bắc | Tự nhiên | Kiến thức |
| Adam bựa | Nam | Bắc | Tự nhiên | Review phong cách vui |
| Ngọc Huyền | Nữ | Bắc | Giọng đọc tự nhiên | |
| Đoan Trang | Nữ | Bắc | Tự nhiên | |
| Phạm Tuyên | Nam | Bắc | Tự nhiên | |
| Xuân Vĩnh | Nam | Bắc | Tự nhiên | |
| Quốc Tuấn | Nam | Bắc | Tự nhiên | |
| Quang Sơn | Nam | Trung | Tự nhiên | Khán giả miền Trung |
| Ngọc Trân | Nữ | Trung | Tự nhiên | Khán giả miền Trung |
| Adam | Nam | Nam | Giọng đọc tự nhiên | |
| Thiện Minh | Nam | Bắc | Kể chuyện | Kể chuyện |
| Thiền Tâm Đức | Nam | Bắc | Kể chuyện | |
| Thanh Bình | Nam | Bắc | Kể chuyện | |
| Ngọc Linh | Nữ | Bắc | Kể chuyện | Kể chuyện |
| Thái Sơn | Nam | Nam | Kể chuyện | Kể chuyện, phía Nam |
| Thục Đoan | Nữ | Nam | Kể chuyện | Kể chuyện, phía Nam |
| Quỳnh Anh | Nữ | Bắc | Đọc truyện | |
| Mỹ Duyên | Nữ | Nam | Đọc truyện | |
| Đức Trí | Nam | Nam | Đọc truyện | |
| Kim Thanh | Nữ | Nam | Đọc truyện | |

## Lưu ý

- Mỗi lần đọc lại một câu cho kết quả hơi khác (lấy mẫu ngẫu nhiên): thời lượng có thể lệch vài trăm ms. Luôn chạy lại `inject.py` sau khi đọc lại.
- Đọc sai một từ: sửa cách viết trong `narration` (viết đầy đủ, viết số bằng chữ, tách từ ghép nước ngoài) rồi đọc lại cảnh đó với `--only`.
- VieNeu hỗ trợ nhân bản giọng từ đoạn thu âm 3 đến 8 giây (`ref_audio`), chưa tích hợp vào `tts.py`. Chỉ dùng giọng của người đã đồng ý.
- Tốc độ chỉnh bằng `speed` (0.85 đến 1.15), áp bằng bộ lọc atempo của ffmpeg sau khi đọc.
