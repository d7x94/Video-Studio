# Cảnh có nhân vật chibi

Nhân vật hoạt hình đầu to nhìn chính diện: viền nâu đậm, màu phẳng có một lớp bóng, má hồng, viền trắng kiểu sticker, nền mờ phía sau, phụ đề chữ trắng viền đen. Dựng bằng SVG trong HyperFrames theo kiểu cut-out (các mảnh vẽ một lần, chỉ đổi tư thế và nét mặt), có nhép miệng theo lời đọc. Kiểm chứng chạy trọn quy trình ngày 2026-11-13 (lồng tiếng 2 giọng, `inject.py`, `hyperframes check` 0 lỗi, render hai khổ, `check_output.py` ĐẠT).

## Khi nào dùng

Khi brief ghi "kiểu hình: chibi", hoặc người dùng muốn kiểu hoạt hình dễ thương, đầu to, có biểu cảm và nhép miệng (clip hội thoại ngắn kiểu TikTok). So với các kiểu khác:

| Loại | Render đo được (workspace 2 nhân) |
|---|---|
| 2D chữ và biểu tượng | khoảng 1,3 giây cho mỗi giây video |
| Line-art, 2 nhân vật | khoảng 3,5 giây cho mỗi giây video |
| Chibi, 2 nhân vật | khoảng 4,5 giây cho mỗi giây video (video 10,3 giây: 46 giây mỗi khổ, 1080p) |
| 3D, 2 đến 3 nhân vật | khoảng 13 đến 15 giây cho mỗi giây video |

Không cần tải gì từ mạng. Video 60 giây hai khổ, mỗi khổ 1 bản nháp và 1 bản cuối: khoảng 18 phút render; bản dài hơn khoảng 2 phút một khổ thì chạy nền.

Giới hạn hiện có (đừng viết kịch bản đòi những thứ này):
- Chỉ nhìn chính diện, hơi nghiêng về một phía; quay trái hoặc phải bằng cách lật gương nhanh (đồ cầm tay đổi bên theo).
- Đi lại theo chiều ngang kiểu nhún nhảy hoạt hình, không chạy, không ngồi, không nằm, không cúi nhặt đồ.
- Không đổi trang phục, màu, đạo cụ trong video.

## Dàn nhân vật

Dùng chung dàn 12 nhân vật đã khóa với line-art (`references/nhan-vat-line-art.md`): cùng mã, tên, trang phục, màu, đạo cụ. Bản chibi chỉ thêm màu da và màu tóc (bảng `LOOKS` trong `assets/chibi/src/rig.ts`). Một người có thể xuất hiện ở cả hai kiểu hình mà vẫn nhận ra. Thêm hay sửa nhân vật thì sửa `assets/lineart/src/cast/roster.ts` (đã khóa, chỉ sửa khi người dùng yêu cầu), thêm màu da vào `LOOKS`, rồi build lại cả hai thư viện (`tools/build_lineart.sh`, `tools/build_chibi.sh`). Trang phục mới chưa có trong rig thì thư viện báo lỗi "chua ve ban chibi", không vẽ sai.

Đồ cầm tay luôn ở tay sau (bên trái hình khi `dir` 1): Chị Thu ôm bìa hồ sơ, Cô Hoa ôm sách, Anh Khoa kéo vali, Anh Đức xách cặp, Bà Sáu xách giỏ, Ông Bảy chống gậy, Chị Năm gánh đòn gánh trên vai, Bé An đeo ba lô. Cử chỉ làm bằng tay trước.

## Thư viện `chibi.js`

Template chibi đã nạp sẵn. Agent dựng cảnh viết khối `SETUP` (nằm trong `C.setup(...)`), lớp chữ `SCENES` và tween `ANIMATION`; khối `DIRECTION` thường để trống.

```js
// SETUP: chạy lại từ đầu mỗi khi tua lùi, nên chỉ được dựng cảnh và hẹn giờ ở đây
const thu = C.add("can-bo-thu", { x: 300, y: 1900, scale: 3.3, dir: 1 });     // dir 1: hướng sang phải
const khoa = C.add("anh-khoa", { x: 1400, y: 1900, scale: 3.3, dir: -1 });  // bắt đầu ngoài khung
C.at(0, () => khoa.walkTo(790));                                            // đi vào rồi tự dừng
C.at(T.s01, () => { thu.say(3.23); thu.expr("wink", 1.6); khoa.expr("deadpan", 3.2); });
C.at(T.s01 + 1.4, () => thu.act("present", 1.6));
C.at(T.s02, () => { khoa.say(2.67); khoa.expr("surprised", 1.2); thu.expr("neutral"); });
```

- `C.add(mã, { x, y, scale, dir })`: `y` là mặt đất dưới chân; `scale` 1 tương ứng người lớn cao khoảng 300 px (đầu khoảng 160 px), trẻ em khoảng 230 px. Gợi ý bố cục kiểu clip hội thoại: khổ dọc `scale` 3 đến 3,4, `y` 1850 đến 1950 (đầu ở giữa khung, phụ đề đè lên thân), hai người cách nhau khoảng 490 px; khổ ngang `scale` 3,2 đến 3,6, `y` 1300 đến 1400 (cắt ngang hông), hai người cách nhau khoảng 680 px. Nửa trên khổ dọc để trống cho lớp chữ.
- `c.say(giây)`: nhép miệng trong khoảng này theo âm lượng lời đọc (`speech.js` do `inject.py` sinh từ `voiceover.wav`). Gọi ở `T.<id>` với giây bằng `visual_duration` của cảnh trong `timeline.json`; lúc im lặng miệng tự khép. Chỉ người đang nói trong cảnh được gọi `say`. Nhân vật đeo khẩu trang thì khẩu trang co giãn theo lời.
- `c.expr(tên, giây?)`: `neutral`, `happy` (mắt cười, miệng mở), `wink` (nháy mắt), `deadpan` (mắt dẹt, chán), `surprised` (mắt tròn), `worried` (lo). Không ghi giây thì giữ đến khi đổi. Mắt tự chớp khi `neutral`, `surprised`, `worried`.
- `c.act(tên, giây)`: `wave` vẫy tay, `point` chỉ về hướng đang nhìn, `present` mời hoặc giới thiệu, `talk` tay đưa trước ngực theo nhịp nói, `bow` cúi chào, `nod` gật đầu. Cử chỉ chỉ chạy khi đứng yên.
- `c.walkTo(x)`: đi tới hoành độ `x` rồi dừng, tự quay theo hướng đi. Tốc độ: người lớn khoảng 120 × scale px/giây, trẻ em khoảng 105 × scale, người già khoảng 70 × scale. Muốn đến đúng lúc thì tính giờ xuất phát.
- `c.face(1 | -1)`: quay sang phải hoặc trái (lật gương trong 0,16 giây).
- `C.at(t, fn)`: hẹn một việc ở giây `t` (dùng `T.<id> + ...`, không viết số giây tuyệt đối).
- Vẽ thêm vào `C.back` (sau nhân vật) hoặc `C.front` (trước) bằng `CB.fill(lớp, d, màu)`, `CB.line(lớp, d, độ dày)`; viền dùng màu `CB.OUT` cho hợp nét nhân vật.

## Nền

Mặc định là nền vẽ phong cảnh mờ (khối `BG` trong template). Muốn nền ảnh thật kiểu clip quay ngoài trời: chỉ dùng ảnh người dùng tự chụp hoặc gửi kèm (không lấy ảnh trên mạng), làm mờ sẵn một lần bằng ffmpeg rồi thay khối `BG`:

```bash
ffmpeg -y -i anh-goc.jpg -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=18" -q:v 3 build/portrait/bg.jpg
ffmpeg -y -i anh-goc.jpg -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=18" -q:v 3 build/landscape/bg.jpg
```

rồi trong `index.html` thay nội dung giữa `<!-- BG:BEGIN -->` và `<!-- BG:END -->` bằng `<img src="bg.jpg" alt="" />`. Làm mờ trước (không dùng CSS `filter: blur` lúc render) để render không chậm thêm. Ghi ảnh vào `credits.md` là ảnh của người dùng.

## Quy tắc đã rút ra khi thử

- **Tất định**: thư viện mô phỏng tiến từng bước 1/60 giây và dựng lại từ đầu khi tua lùi. Không dùng `Math.random`, `Date.now`; mọi thứ khởi tạo trong `SETUP`.
- **Viền sticker** vẽ bằng một bản bóng trắng nằm sau nhân vật, không dùng bộ lọc SVG: thử `feMorphology` làm render chậm gấp gần 4 lần (63 giây so với 17 giây cho 4 giây video). Đừng thêm `filter` lên nhân vật hay toàn sân khấu.
- **Hai người nói chuyện**: quay mặt vào nhau (`dir` ngược nhau), người nghe dùng `nod` hoặc đổi `expr` xen giữa câu của người nói; viền sticker của người đứng sau tự tách hai người ra.
- **Vào khung**: xuất phát ngoài mép và `walkTo` vào; dừng trước khi câu thoại bắt đầu ít nhất 0,3 giây.
- **Vẫy tay** ở `scale` lớn có thể đưa tay sát mặt người đứng cạnh; giữ khoảng cách gợi ý ở trên.
- Phụ đề khổ dọc nằm cách đáy 380 px (chừa giao diện TikTok) và đè lên thân nhân vật, giống clip mẫu; không đặt mặt nhân vật dưới y 1450 ở khổ dọc.

## Kiểm tra

`hyperframes check` phải 0 lỗi. Cảnh báo có thể bỏ qua: `container_overflow` của `#bg` (nền cố ý tràn khung) và của nhân vật đi vào từ ngoài khung, `off_pivot_rotation` ở tay nhân vật (khớp vai xoay đúng, trình kiểm tra hiểu nhầm là kim đồng hồ). Xem nhanh tư thế trước khi render: `cd build/<khổ> && hyperframes snapshot --at 1,3.5,5 --no-end -o snaps` rồi xem `snaps/contact-sheet.jpg`.

## Ghi công

Nhân vật, rig và nền chibi do studio tự vẽ bằng code, không dùng thư viện hay hình của bên thứ ba. Ghi vào `credits.md`: "Nhân vật chibi: đồ họa tự vẽ của studio (SVG)". Nếu nền là ảnh người dùng, ghi thêm "Ảnh nền: của người dùng".
