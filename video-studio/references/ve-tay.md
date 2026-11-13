# Cảnh vẽ tay (kiểu hình `ve-tay`)

Mỗi cảnh là một bức tranh minh họa. Tranh hiện dần theo vệt cọ ngoằn ngoèo, có bàn tay cầm bút chạy theo đầu vệt, kiểu "whiteboard animation". Mỗi cảnh vẽ hai lượt: lượt phác chì (nét mực trên giấy, mảng màu rất nhạt), rồi lượt tô màu. Chuyển động, bàn tay và giấy do studio tự vẽ bằng code. **Tranh do người dùng tạo** bằng công cụ tạo ảnh AI (ChatGPT, Gemini...) theo câu lệnh studio viết, vì studio không tạo được ảnh dạng này.

Kiểm chứng ngày 2026-11-13: chạy trọn quy trình với 3 tranh thử (lồng tiếng, `inject.py`, `hyperframes check` 0 lỗi, render hai khổ, `check_output.py` ĐẠT).

## Khi nào dùng

Khi brief ghi "kiểu hình: ve-tay", hoặc người dùng nói "vẽ tay", "whiteboard", "tranh hiện dần", "bàn tay vẽ". Hợp mọi thể loại; chỉ phong cách tranh đổi theo chủ đề (mục Phong cách tranh).

| Loại | Render đo được (workspace 2 nhân, 1080p) |
|---|---|
| Vẽ tay, có phóng chậm `zoom` mặc định | khoảng 6 đến 7 giây cho mỗi giây video (video 11,1 giây: 68 đến 79 giây mỗi khổ qua các lần chạy) |
| Vẽ tay, `zoom: 0` | khoảng 5,1 giây cho mỗi giây video (57 giây khổ ngang) |

Video 60 giây hai khổ, mỗi khổ 1 bản nháp và 1 bản cuối: khoảng 28 phút render. Mỗi lần render một khổ quá khoảng 7 phút thì chạy nền.

## Quy trình riêng của kiểu này

1. **Bước 2, biên kịch**: trường `visual` của mỗi cảnh mô tả **một** bức tranh (bối cảnh, người, hành động, góc nhìn, màu chủ đạo); thêm `focus` (0 đến 1) là vị trí ngang của chủ thể chính, dùng khi cắt tranh ngang cho khổ dọc. Chữ trên hình (`on_screen.title`) chỉ là nhãn ngắn (mốc thời gian, địa danh). Không có chữ trong tranh.
2. **Bước 3c, tranh** (sau khi duyệt kịch bản): viết `cau-lenh-tranh.md` theo mẫu dưới, gửi người dùng, dừng chờ. Người dùng tạo ảnh, gửi lại; lưu vào `<PROJECT>/tranh/<id>.jpg` (ngang 16:9, bắt buộc) và `<id>-doc.jpg` (dọc 9:16, không bắt buộc).
3. **Soát tranh** (điều phối viên, trước khi dựng): xem từng ảnh. Lỗi nhỏ ở một vùng nhỏ (ký hiệu lạc thời đại trên lá cờ, chữ giả trên tờ giấy) có thể tự xóa bằng cách tô lấp từ màu xung quanh (Python, numpy và scipy có sẵn), xem kỹ vùng đã sửa và báo người dùng đã sửa gì; lỗi lớn thì nhờ tạo lại. Trả lại người dùng để tạo lại nếu: có chữ hay chữ ký trong tranh; chi tiết chuyên môn sai so với `kiem-chung.md` (trang phục, thao tác y tế, đồ bảo hộ, quầy, phương tiện); nhân vật lặp lại trông khác hẳn giữa các cảnh; người thật có thể nhận ra; logo, nhân vật có bản quyền. Gom các ảnh cần làm lại vào một lần hỏi, kèm câu lệnh đã sửa.
4. **Bước 5**: `new_project.sh <PROJECT> <khổ> vetay` cho từng khổ, rồi `python3 SKILL/scripts/ve_tay_anh.py <PROJECT>` (cắt, phóng tranh cho đúng khung và tạo bản phác chì vào `build/<khổ>/img/`). Chưa có đủ tranh thì script báo cảnh thiếu.

## Câu lệnh tạo tranh (`cau-lenh-tranh.md`)

Viết bằng tiếng Anh (công cụ tạo ảnh hiểu tốt hơn), kèm một dòng tiếng Việt tóm tắt cho người dùng. Mỗi câu lệnh ghép theo thứ tự:

1. **Khối phong cách**: chép nguyên văn khối của phong cách đã chọn (mục dưới), giống hệt ở mọi cảnh để các tranh cùng một tay vẽ.
2. **Khối nhân vật** (nếu có người lặp lại qua nhiều cảnh): mô tả cố định một lần trong `cau-lenh-tranh.md` (tuổi, dáng, trang phục, màu, đạo cụ), chép nguyên văn vào mọi cảnh có người đó. Dù vậy các tranh vẫn lệch chút ít; dặn người dùng tạo các cảnh trong cùng một cuộc chat với công cụ tạo ảnh.
3. **Cảnh**: dịch `visual` sang tiếng Anh, cụ thể (ai, làm gì, ở đâu, góc nhìn, ánh sáng).
4. **Khối kỹ thuật** luôn có: `Wide 16:9 landscape image. Keep the main subject inside the central third of the width so a vertical crop still works. No text, no letters, no numbers, no captions, no signature, no watermark, no frame or border.`

Mẫu gửi người dùng, mỗi cảnh một khối:

```
### Cảnh s03: lưu thành s03.jpg
(Ba anh em dựng cờ khởi nghĩa dưới gốc cây lớn)
<câu lệnh tiếng Anh>
```

Tranh có thể nhỏ hơn khung video (đã gặp 1168x784 với tranh Grok gửi qua chat, chưa rõ do công cụ hay do nén khi gửi): nhắc người dùng chọn độ phân giải cao nhất và thử gửi dạng tệp; `ve_tay_anh.py` vẫn phóng được, tranh màu nước chịu mờ nhẹ tốt.

Kèm hướng dẫn: dán từng câu lệnh vào công cụ tạo ảnh, chọn khổ ngang 16:9 nếu công cụ có tùy chọn, tải ảnh về đúng tên file, gửi lại cả bộ. Muốn khổ dọc đẹp hơn thì tạo thêm bản dọc (thay câu cuối bằng `Tall 9:16 portrait image.`) và lưu `<id>-doc.jpg`.

Quy tắc nội dung:
- Người thật (nhân vật lịch sử, người nổi tiếng): không có ảnh đương thời thì vẽ từ xa, từ phía sau hoặc nghiêng, không cận mặt kiểu chân dung tả thực. Người đang sống: không dựng hình khi chưa có sự đồng ý của họ (quy tắc chung của repo).
- Không yêu cầu bắt chước phong cách của một họa sĩ, xưởng phim hay thương hiệu cụ thể; không nhắc tên nhân vật có bản quyền.
- Lịch sử: mô tả cụ thể trang phục, vũ khí, kiến trúc Việt Nam của thời đó (vd nón dấu, áo vải nâu, giáo, khiên mây; mái ngói cong kiểu Huế), và ghi `not Chinese, not Japanese style` nếu dễ lẫn. Phe đối địch vẽ đúng trang phục của họ, không bôi xấu.
- Chiến tranh, tai nạn, bệnh tật: gợi bằng khói, cờ, bối cảnh; không máu, không thương vong, không vết thương.
- Sức khỏe, thủ tục: thao tác, đồ bảo hộ, quy trình phải đúng `kiem-chung.md`; mô tả kỹ trong câu lệnh (vd cách đeo khẩu trang che kín mũi và cằm).

## Phong cách tranh

Chọn ở bước 0 theo thể loại, ghi vào brief. Mỗi phong cách đi với màu giấy (`--paper` trong `index.html`, cũng là `--paper` của `ve_tay_anh.py`).

| Mã | Hợp với | Giấy |
|---|---|---|
| `mau-nuoc` | lịch sử, kể chuyện, văn hóa | `#efe5d2` (mặc định) |
| `mau-phang` | sức khỏe, khuyến cáo cộng đồng | `#f6f1e7` |
| `phac-chi` | kiến thức, giải thích cơ chế | `#f2efe8` |
| `muc-den` | thủ tục, quy trình từng bước | `#fbfaf6` |

Khối phong cách (chép nguyên văn vào đầu mỗi câu lệnh):

- `mau-nuoc`: `Hand-painted watercolor and ink illustration on warm cream paper, fine dark-brown pen outlines, soft washes in muted earth tones (ochre, sienna, olive green, slate blue) with touches of vermilion, gentle natural light, detailed but calm composition, storybook historical illustration.`
- `mau-phang`: `Friendly flat illustration with clean rounded shapes and a light watercolor texture, bright soft palette (teal, coral, warm yellow, cream), simple faces without exaggerated features, Vietnamese people in everyday Vietnamese settings, clear readable composition.`
- `phac-chi`: `Graphite pencil sketch with light colored-pencil wash on off-white paper, visible hatching, clean technical clarity, a few accent colors only (blue and orange), diagram-like but hand-drawn.`
- `muc-den`: `Black ink line drawing on white paper, confident even line weight, minimal shading, one accent color (teal) for the key object only, lots of empty space, instructional illustration.`

Thêm phong cách mới: thêm một dòng vào bảng và một khối ở đây; giữ chữ "no text" ở khối kỹ thuật.

## Thư viện `vetay.js`

Template đã nạp sẵn. Agent dựng cảnh viết khối `SETUP` (mỗi cảnh một dòng), lớp chữ `SCENES` và tween `ANIMATION`.

```js
// SETUP: moi canh mot buc tranh, moc theo T.<id>
V.scene("s01", { start: T.s01, color: "img/s01.jpg", sketch: "img/s01-sketch.jpg" });
V.scene("s02", { start: T.s02, color: "img/s02.jpg", sketch: "img/s02-sketch.jpg", draw: 4 });
```

Tùy chọn của `V.scene(id, {...})`:
- `start` (bắt buộc): `T.<id>`. Cảnh kéo dài đến khi cảnh sau bắt đầu, rồi mờ dần trong `fadeOut` giây (mặc định 0,45) dưới tranh mới.
- `color` (bắt buộc), `sketch` (bỏ thì chỉ có lượt tô màu).
- `draw`: số giây vẽ (mặc định 62% thời lượng cảnh, trong khoảng 2,2 đến 5,5); `delay`: giây chờ trước khi vẽ (0,25); `sketchShare`: phần thời gian của lượt phác (0,42).
- `zoom`: phóng chậm trong suốt cảnh (0,035). `zoom: 0` render nhanh hơn khoảng 20%.
- `margin`: lề giấy quanh tranh theo tỷ lệ khung (0,045); `box: [x, y, w, h]` để vẽ tranh vào một vùng (vd nửa khung, chừa chỗ cho chữ).
- `rows`: số hàng vệt cọ (tự tính theo chiều cao); `seed`: đổi hình vệt cọ.
- `hand: false`: không có bàn tay (vd cảnh cuối chỉ hiện chữ).

Lớp chữ: `.tag` (mảnh giấy góc trên trái, có `<small>` cho dòng nhỏ màu nhấn), `.big` (tiêu đề lớn giữa khung, cho cảnh mở đầu hoặc kết), `.source` (dòng nguồn). Ví dụ:

```html
<section id="sc-s07" class="clip scene" data-start="0" data-duration="1"><div class="tag"><small>1789</small>Ngọc Hồi – Đống Đa</div></section>
```

```js
// ANIMATION: nhan hien sau khi tay bat dau ve
tl.from("#sc-s07 .tag", { y: -40, opacity: 0, duration: 0.5, ease: "back.out(2)" }, T.s07 + 0.6);
```

## Quy tắc đã rút ra khi thử

- **Tất định**: vệt cọ sinh từ hạt giống cố định; không dùng `Math.random`, `Date.now`.
- Không thêm `filter` SVG hay CSS lên tranh (blur, grayscale): bản phác chì đã làm sẵn bằng `ve_tay_anh.py` để render không chậm.
- Bỏ mặt nạ sau khi vẽ xong không làm render nhanh hơn (đã thử: 74 so với 73 giây), nên mép tranh luôn giữ đường vệt cọ.
- Khổ dọc: chữ nhãn nằm dưới mép trên 230 px, dòng nguồn ngay dưới nhãn (top 410 px) để không chồng lên phụ đề cách đáy 380 px (chừa giao diện TikTok). Chủ thể chính của tranh nên ở giữa khung (ghi rõ trong câu lệnh và `focus`).

## Kiểm tra

`hyperframes check` phải 0 lỗi. Cảnh báo có thể bỏ qua: `container_overflow` của nhóm tranh (do phóng chậm `zoom`), `nested_structure_needs_subcomposition`. Xem nhanh trước khi render: `cd build/<khổ> && hyperframes snapshot --at <giữa lượt phác>,<giữa lượt tô>,<cuối cảnh> --no-end -o snaps`.

## Ghi công

Ghi vào `credits.md`: "Tranh minh họa: do người dùng tạo bằng <công cụ>"; "Hiệu ứng vẽ tay, bàn tay: đồ họa tự vẽ của studio (SVG)". Nhãn nội dung AI khi đăng do người dùng quyết; nhắc họ rằng tranh là ảnh do AI tạo.
