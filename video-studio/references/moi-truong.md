# Môi trường workspace

Kiểm chứng ngày 2026-11-12 trên workspace của Claude chat (Linux, 2 nhân CPU, 7,8 GB RAM, không GPU). Khi môi trường đổi, chạy `bash SKILL/scripts/setup.sh --check` trước.

## Mạng

Shell của workspace ra ngoài qua proxy có danh sách cho phép. Tại thời điểm kiểm:

| Đích | Trạng thái | Hệ quả |
|---|---|---|
| registry.npmjs.org, pypi.org | Được | Cài HyperFrames, GSAP, font, VieNeu |
| github.com (Release của repo) | Được | Tải mô hình giọng VieNeu (Release `vieneu-v3-turbo-61b85e3`, danh mục `assets/voice-models.json`) |
| huggingface.co | Được | Dự phòng khi không tải được từ Release; không bắt buộc |
| cdn.jsdelivr.net, unpkg, Google Fonts | Bị chặn | Template mặc định của HyperFrames lấy GSAP từ CDN: animation **âm thầm không chạy**. Skill cài GSAP và font cục bộ |
| Kho ảnh, nhạc (Pixabay...) | Bị chặn | Hình vẽ bằng code, hoặc người dùng gửi kèm |
| Dịch vụ giọng đọc đám mây | Bị chặn | Dùng VieNeu chạy cục bộ |
| quaternius.com, drive.google.com, drive.usercontent.google.com | Được sau khi người dùng mở (2026-11-12) | Tải nhân vật 3D. Gói Free không mở được tên miền ngoài kho gói |

Danh sách cho phép do người dùng chỉnh trong claude.ai trên trình duyệt (Settings > Capabilities); gói Team/Enterprise do quản trị viên chỉnh. Công cụ tìm kiếm và đọc trang web của Claude không đi qua proxy này, nên agent kiểm chứng vẫn tra cứu được.

## Trình duyệt

HyperFrames cố tải chrome-headless-shell riêng và thất bại vì mạng. `studio.env` đặt `HYPERFRAMES_BROWSER_PATH` trỏ vào Chrome hệ thống. Hệ quả: render dùng đường chụp màn hình (chậm hơn BeginFrame) và GPU giả lập phần mềm. Cảnh nặng (nhiều lớp mờ, WebGL, shader) có thể chậm hoặc treo: giữ hiệu ứng đơn giản.

## Lỗi đã biết

**onnxruntime 1.29 từ chối nạp VieNeu từ bộ nhớ đệm HuggingFace.** Lỗi "External data path escapes model directory": file `.onnx` và `.data` nằm ở hai thư mục blobs khác nhau qua symlink. `tts.py` đã vá bằng cách đặt mô hình vào thư mục thường `~/studio/.tools/models/` (tự tải theo `assets/voice-models.json`, kiểm sha256, rồi chạy offline với `HF_HUB_OFFLINE=1`). Nếu vieneu đổi danh sách file cần nạp, `tts.py` báo lỗi "vieneu doi hoi file chua co trong assets/voice-models.json": cập nhật danh mục và Release. Nếu bản vieneu mới đổi cấu trúc nội bộ (`_v3_turbo_engine.onnx_runtime_lite.OnnxV3LiteEngine._fetch`) thì vá này cần cập nhật.

**Render báo `[non-blocking] Failed to load resource: 404`.** Trình duyệt hỏi favicon. `hyperframes check` không báo lỗi console nào; bỏ qua.

**`hyperframes check` cảnh báo `line_unread` cho phụ đề.** Ngưỡng tính 0,3 giây mỗi từ cho tiếng Anh; tiếng Việt đọc khoảng 3,5 tiếng mỗi giây nên phụ đề theo lời đọc luôn dưới ngưỡng. Bỏ qua với phần tử `cap-...`; vẫn sửa với chữ trên cảnh.

## Hiệu năng đo được

| Việc | Thời gian |
|---|---|
| setup.sh lần đầu (cài + tải mô hình) | vài phút, tùy tốc độ mạng |
| VieNeu int8, giọng Mai Anh | 0,5 đến 0,85 giây cho mỗi giây âm thanh |
| Render HyperFrames 1080p, cảnh ít chuyển động | khoảng 1,3 giây cho mỗi giây video |
| Render cảnh 3D, 2 đến 3 nhân vật | khoảng 13 đến 15 giây cho mỗi giây video, bản nháp và bản cuối như nhau |
| `hyperframes snapshot` 5 khung hình cảnh 3D | khoảng 9 giây |
| Render Remotion (dự phòng, chưa tích hợp vào skill) | khoảng 7 giây cho mỗi giây video ở lần đầu, phần lớn là đóng gói |

Render càng nhiều chuyển động liên tục càng chậm (HyperFrames bỏ qua khung hình tĩnh trùng lặp).

**Lệnh render dài hơn 10 phút bị cắt.** Một lệnh Bash chạy thường tối đa 10 phút. Video 3D dài hơn khoảng 40 giây vượt mức này ở cả bản nháp lẫn bản cuối: chạy `render.sh` ở chế độ nền.

**`render.sh` báo "Bo qua render".** File đích đã có và mới hơn mọi file của composition, nên không render lại. Muốn ép render: `FORCE=1 bash render.sh ...`.

## Phiên bản đã kiểm chung với nhau

hyperframes 0.9.38, gsap 3.15.0, @fontsource/be-vietnam-pro 5.3.0, three 0.184.0, vieneu 3.8.4, onnxruntime 1.29.0, Node 22, ffmpeg 6.1. Pin trong `setup.sh`. Muốn nâng phiên bản: đổi pin, chạy một video thử 3 cảnh qua đủ các bước, rồi mới dùng thật.
