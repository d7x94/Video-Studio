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
- Tốc độ chỉnh bằng `speed` (0.85 đến 1.15), áp bằng bộ lọc atempo của ffmpeg sau khi đọc. `speed` ở đầu `scenes.json` áp cho cả bài; một cảnh có thể có `speed` riêng (cùng khoảng) để đọc chậm câu quan trọng hoặc nhanh câu chuyển ý. `--speed` khi chạy lệnh ghi đè mọi cảnh. Đổi `speed` của một cảnh thì phải đọc lại cảnh đó bằng `--only`.

## Chỉ đạo giọng theo cảnh

Giọng máy nghe "đọc" thay vì "nói" chủ yếu vì nhịp đều đều. Hai trường tùy chọn của từng cảnh trong `scenes.json` sửa việc này mà không cần mô hình hỗ trợ gì thêm:

- `pause_before`: số giây nghỉ trước cảnh, thay khoảng nghỉ mặc định (0,35 giây giữa hai cảnh, 0,4 giây trước cảnh đầu). Từ 0 đến 1,5. Đổi trường này không cần đọc lại: chạy `tts.py scenes.json . --retime` (giữ nguyên file tiếng đã có, chỉ tính lại `timeline.json` và `voiceover.wav`) rồi `inject.py` cho từng khổ.
- `speed`: tốc độ riêng của cảnh, như trên.

Dùng có chủ ý, mỗi chỗ một lý do:
- Nghỉ dài hơn (0,6 đến 0,9 giây) trước câu đảo ý ("Nhưng..."), trước con số hay khuyến cáo chính, và trước câu kết. Video 60 giây thường chỉ cần 2 đến 3 chỗ như vậy; nhiều hơn nghe như kịch.
- Nghỉ ngắn hơn (0,15 đến 0,25 giây) giữa hai cảnh cùng một mạch liệt kê.
- `speed` 0,9 đến 0,95 cho cảnh có khuyến cáo, số liệu hay thao tác người xem phải nhớ; không dùng dưới 0,9 cho cả bài.
- Khoảng nghỉ trước cảnh nằm trong thời gian hình của cảnh trước, nên cảnh trước giữ hình lâu hơn tương ứng; rút ngắn khoảng nghỉ thì cảnh trước ngắn lại. Video `ve-net` đổi khoảng nghỉ xong phải chạy lại `ve_net_kiem_tra.sh` (khi thử, cảnh 2,2 giây có hình đồng hồ 8 nét bị báo `KHONG KIP`).
