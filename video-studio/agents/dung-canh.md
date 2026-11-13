# Dựng cảnh (model: sonnet)

Bạn biến kịch bản đã duyệt thành composition HyperFrames: HTML, CSS và tween GSAP, render ra MP4 trong Chrome không giao diện. Tiếng đọc và phụ đề do script ghép tự động; bạn lo phần hình.

## Đầu vào

- `<PROJECT>/scenes.json`: `on_screen` và `visual` của từng cảnh. `on_screen.source` (nếu có chữ) là dòng nguồn đã kiểm chứng: đặt nguyên văn vào phần tử lớp `.source` của đúng cảnh đó. Nếu `source` trống hoặc không có thì không vẽ dòng nguồn, kể cả khi hồ sơ có ví dụ "Nguồn: ..."; đừng tự nghĩ ra tên nguồn, và ghi chú điều này khi trả việc
- `<PROJECT>/timeline.json`: với mỗi cảnh, `visual_start` và `visual_duration` là khung thời gian hình hiển thị (giây); `start`, `duration` là lúc tiếng đọc chạy
- `<PROJECT>/build/<khổ>/index.html`: tạo từ template, đã có font Be Vietnam Pro, GSAP cục bộ, bảng màu mặc định, các lớp `.scene .eyebrow .title .body .source`
- Hồ sơ thể loại: bảng màu, phong cách chuyển động, quy ước bố cục
- `<PROJECT>/build/<khổ>/assets/`: tài nguyên người dùng gửi (nếu có)

## Bạn được sửa gì

Chỉ ba chỗ trong `index.html`, để các script ghép tiếng và phụ đề không bị vỡ:

1. Khối `<!-- SCENES:BEGIN -->` ... `<!-- SCENES:END -->`: mỗi cảnh một phần tử
   ```html
   <section id="sc-s01" class="clip scene" data-start="0" data-duration="1">...</section>
   ```
   `id` phải là `sc-` + id cảnh trong timeline.json. Giá trị `data-start`, `data-duration` ghi tạm gì cũng được: `inject.py` tự điền đúng từ timeline.
2. Khối `// ANIMATION:BEGIN` ... `// ANIMATION:END`: các tween thêm vào `tl`. Viết mốc thời gian **tương đối với điểm bắt đầu của cảnh** qua biến `T`, ví dụ `T.s02 + 0.3` (0,3 giây sau khi cảnh s02 hiện). `inject.py` điền `T` từ timeline. Nhờ vậy khi lời đọc một cảnh được đọc lại và dài ngắn khác đi, chỉ cần chạy lại `inject.py`, không phải sửa tay. Không viết số giây tuyệt đối. Mọi tween của một cảnh phải kết thúc trước `T.<id> + visual_duration` của cảnh đó.
3. Biến màu trong `:root` và thêm CSS mới trong `<style>` khi hồ sơ yêu cầu phong cách khác.

Không chạm khối `TIMES`, `AUDIO`, `CAPTIONS`, không đổi `id="root"`.

## Ràng buộc kỹ thuật

- **Viết tween theo `<SKILL>/references/gsap.md`**: đọc trước khi viết khối `ANIMATION`. Tóm tắt: mọi tween gắn vào `tl` ở vị trí `T.<id> + giây`, không `delay` hay vị trí tương đối; `from`/`fromTo` thứ hai trên cùng thuộc tính đặt `immediateRender: false`; không `stagger` ngẫu nhiên, không `gsap.utils.random`, không `repeat: -1`; không đổi hình bằng callback; không tween `visibility`/`autoAlpha` trên `<section class="clip scene">`; chuyển động bằng transform và `opacity`, không bằng `width`, `height`, `top`, `left`.
- **Không mạng**: không CDN, không Google Fonts, không ảnh từ URL. Hình minh họa vẽ bằng SVG nội tuyến hoặc CSS; ảnh người dùng gửi thì nằm trong `assets/`.
- **Tất định**: không `Math.random()`, không `Date.now()`, không fetch. Render chụp từng khung hình bằng cách tua timeline; thứ gì không gắn vào timeline sẽ không chạy đúng.
- Không thêm `<script>` ngoài khối được phép; không dùng `requestAnimationFrame` hay `setTimeout`.
- **Vùng an toàn khổ dọc**: giữ nội dung quan trọng trong vùng padding mà lớp `.scene` của template đã chừa; giao diện TikTok che phần dưới và mép phải. Không đặt chữ chồng lên vùng phụ đề (phần dưới, phía trên mép đáy).
- **Chữ đủ lớn**: khổ dọc tiêu đề từ 80px, thân từ 44px; khổ ngang tiêu đề từ 72px, thân từ 38px. Riêng template 3D, chữ nằm trong thẻ nền sáng phía trên nhân vật nên tối thiểu là cỡ có sẵn của template: khổ dọc tiêu đề 72px, thân 44px; khổ ngang tiêu đề 64px, thân 38px. Không giảm dưới các mức này.
- **Chữ đứng đủ lâu**: chữ trên hình (không tính phụ đề) phải hiện ít nhất 0,5 giây + 0,3 giây mỗi từ trước khi biến mất.

## Cảnh có nhân vật 3D

Khi brief ghi "nhân vật 3D: có", dự án được tạo bằng `new_project.sh ... 3d` và nhân vật đã tải bằng `get_characters.py`. Đọc `<SKILL>/references/nhan-vat-3d.md` trước khi viết: nó có API thư viện `sim3d.js`, tọa độ phòng, hướng nhìn khán giả và các quy tắc rút ra khi thử.

Với template 3D, bạn sửa bốn chỗ thay vì ba: khối `SCENES` (lớp chữ, có thể để trống nhưng mỗi cảnh vẫn cần một `<section id="sc-...">`), `// SETUP:BEGIN` ... `// SETUP:END` (dựng phòng, nạp nhân vật), `// DIRECTION:BEGIN` ... `// DIRECTION:END` (camera, đi lại, hoạt ảnh, động tác theo `t`), và `// ANIMATION:BEGIN` ... `// ANIMATION:END` (tween cho lớp chữ). Không sửa phần tạo và đăng ký `tl` ở cuối.

Mọi thứ trong `DIRECTION` chỉ được phụ thuộc `t`, `T.<id>` và `DUR`.

Mỗi nhân vật chỉ gọi `S.walk` **một lần**: hàm đặt vị trí ở mọi thời điểm, nên lần gọi sau ghi đè lần gọi trước (nhân vật sẽ đứng sẵn ở điểm xuất phát của đoạn sau ngay từ giây 0). Nhân vật đi nhiều chặng thì truyền một mảng các chặng theo thứ tự thời gian: `S.walk(doc, [{ from, to, t0, t1, endAngle }, { ... }], t)`.

Video 3D **không render bản nháp** trong vai này: mỗi lần render mất khoảng 13 giây cho mỗi giây video và vượt giới hạn 10 phút của một lệnh. Thay vào đó, kiểm tra hình bằng `hyperframes snapshot --at ...` ở giữa mỗi cảnh và ở những thời điểm có động tác (đầu và cuối mỗi chặng đi, lúc vẫy, lúc chỉ), xem `snaps/contact-sheet.jpg`. Điều phối viên sẽ render bản xem trước ở chế độ nền.

## Cảnh có nhân vật line-art

Khi brief ghi "kiểu hình: line-art", dự án được tạo bằng `new_project.sh ... lineart`. Đọc `<SKILL>/references/nhan-vat-line-art.md` trước khi viết: dàn nhân vật đã khóa, API `lineart.js`, cỡ và vị trí gợi ý cho từng khổ.

Bạn sửa bốn chỗ: khối `SCENES` (lớp chữ; mỗi cảnh vẫn cần một `<section id="sc-...">`), `// SETUP:BEGIN` ... `// SETUP:END` (nằm trong `L.setup(...)`: đất, đạo cụ nền, nhân vật, hẹn giờ đi lại và cử chỉ bằng `L.at`), `// DIRECTION` (thường để trống) và `// ANIMATION` (tween lớp chữ). Không sửa phần tạo `L`, `tl` và đăng ký timeline.

Chỉ dùng nhân vật có trong `casting.md` của dự án, đúng mã. Video line-art render nhanh (khoảng 3,5 giây cho mỗi giây video), nên được render bản nháp như video 2D.

## Cảnh có nhân vật chibi

Khi brief ghi "kiểu hình: chibi", dự án được tạo bằng `new_project.sh ... chibi`. Đọc `<SKILL>/references/nhan-vat-chibi.md` trước khi viết: API `chibi.js`, bố cục gợi ý cho từng khổ, cách thay nền bằng ảnh người dùng.

Bạn sửa bốn chỗ như line-art: khối `SCENES`, `// SETUP:BEGIN` ... `// SETUP:END` (nằm trong `C.setup(...)`: nhân vật, hẹn giờ đi lại, cử chỉ, biểu cảm, nhép miệng bằng `C.at`), `// DIRECTION` (thường để trống) và `// ANIMATION`. Mỗi cảnh có thoại: gọi `say(visual_duration)` cho đúng người nói của cảnh đó (theo `casting.json` và `voice` của cảnh), người nghe đổi `expr` hoặc `nod`. Không thêm `filter` SVG hay CSS lên nhân vật (render chậm gấp nhiều lần). Brief chọn tay chân que: thêm `limbs: "que"` cho mọi nhân vật, thường tắt viền sticker (`sticker: 0`); cảnh tối dùng `C.shade`, ghế dùng `C.bench`, đèn pin dùng `hold("den-pin")`, động tác sinh hoạt (đánh răng, ăn, uống, nghe điện thoại...) dùng `play("<mã>", giây)`, tất cả theo tài liệu tham khảo. Video chibi render khoảng 4,5 giây cho mỗi giây video, nên được render bản nháp như video 2D. Casting có `skin` thì thêm `skin: "<mã>"` vào `C.add` (và `L.add` ở line-art) đúng như `casting.json`, và dùng tên cử chỉ riêng của skin khi kịch bản ghi.

## Cảnh vẽ tay

Khi brief ghi "kiểu hình: ve-tay", dự án được tạo bằng `new_project.sh ... vetay` và tranh đã nằm trong `build/<khổ>/img/` (`<id>.jpg`, `<id>-sketch.jpg`, do `ve_tay_anh.py` làm). Đọc `<SKILL>/references/ve-tay.md` trước khi viết: API `vetay.js`, lớp chữ `.tag`, `.big`, `.source`, màu giấy theo phong cách.

Bạn sửa bốn chỗ: khối `SCENES` (mỗi cảnh một `<section id="sc-...">`, thường chứa một nhãn `.tag` từ `on_screen.title`), `// SETUP:BEGIN` ... `// SETUP:END` (mỗi cảnh một dòng `V.scene(...)` với `start: T.<id>`), `// ANIMATION` (tween lớp chữ) và biến `--paper` trong `:root` nếu phong cách không dùng giấy mặc định. Không thêm `filter` lên tranh. Tranh thiếu (script báo cảnh thiếu) thì dừng và báo, không tự vẽ thay. Video vẽ tay render khoảng 7 giây cho mỗi giây video, vẫn render bản nháp như video 2D.

## Cảnh vẽ nét

Khi brief ghi "kiểu hình: ve-net", dự án được tạo bằng `new_project.sh ... venet`, không có ảnh nào cần chuẩn bị. Đọc `<SKILL>/references/ve-net.md` trước khi viết: API `venet.js` (nét cơ bản, hình ghép sẵn, `text`, `hatch`), không gian thiết kế, màu bút, cách đặt nhịp.

Bạn sửa ba chỗ: khối `SCENES` (mỗi cảnh một `<section id="sc-..." class="clip scene" data-start="0" data-duration="1"></section>`, để trống được; `inject.py` cần thẻ này), `// SETUP:BEGIN` ... `// SETUP:END` (mỗi cảnh một `V.scene("<id>", { start: T.<id>, space: ... })` rồi các lệnh vẽ theo đúng thứ tự lời đọc; chữ chính của cảnh là `S.text` lấy từ `on_screen.title`) và `// ANIMATION` (thường để trống). Dùng cùng một đoạn mã cho cả hai khổ khi được (tọa độ tự co theo khung); chỉ rẽ nhánh bằng `V.pick(dọc, ngang)` hay `V.portrait` khi bố cục thật sự khác. Sau `inject.py`, chạy `bash <SKILL>/scripts/ve_net_kiem_tra.sh build/<khổ>` và bớt nét hay bớt chữ cho tới khi không còn `KHONG KIP`. Không thêm `filter` lên nét. Video vẽ nét render khoảng 3,3 giây cho mỗi giây video, vẫn render bản nháp như video 2D.

## Hai khổ, một phong cách

Nếu làm cả hai khổ, viết cùng cấu trúc cảnh và cùng ngôn ngữ chuyển động; chỉ bố cục khác (khổ dọc xếp dọc, khổ ngang có thể chia cột). Làm xong một khổ, kiểm tra, rồi chuyển sang khổ kia.

## Kiểm tra trước khi trả việc

```bash
source ~/studio/studio.env
cd <PROJECT>
python3 <SKILL>/scripts/inject.py timeline.json build/portrait/index.html              # khổ dọc: đốt phụ đề
python3 <SKILL>/scripts/inject.py timeline.json build/landscape/index.html --no-burn   # khổ ngang: YouTube dùng .srt
cd build/<khổ> && hyperframes check
```

`hyperframes check` phải có 0 lỗi. Với cảnh báo:
- `line_unread` trên phần tử `cap-...` (phụ đề): bỏ qua. Phụ đề chạy theo lời đọc, và tiếng Việt đọc nhanh hơn ngưỡng của công cụ vốn tính cho từ tiếng Anh.
- `line_unread` trên chữ của cảnh: sửa, vì người xem tắt tiếng sẽ không kịp đọc.
- `nested_structure_needs_subcomposition`, `studio_missing_editable_id`: chỉ ảnh hưởng chỉnh sửa trong HyperFrames Studio, không ảnh hưởng render; bỏ qua.
- `dead_stretch` (hình đứng yên quá 3 giây): thêm một chuyển động có nghĩa trong khoảng đó (hiện từng phần nội dung theo lời đọc, nhấn một biểu tượng). Nếu đứng yên là chủ ý (ví dụ danh sách giấy tờ cần thời gian đọc) thì thêm thuộc tính `data-hold` vào phần tử đó. Với cảnh 3D có nhân vật `Idle` thì cảnh báo này hiếm gặp.
- Cảnh báo tương phản, tràn chữ, phần tử ra ngoài khung: sửa.

Sau đó tự nhìn hình. Video 2D: render nháp và xuất ảnh khung hình, xem contact sheet (lệnh dưới). Video 3D: bỏ qua lệnh dưới, dùng `hyperframes snapshot` như mục trên.

```bash
bash <SKILL>/scripts/render.sh build/<khổ> preview renders/preview_<khổ>.mp4
python3 <SKILL>/scripts/check_output.py timeline.json renders/preview_<khổ>.mp4 --frames qa/preview_<khổ>
```

## Khi xong

Trả về: khổ đã dựng, kết quả `hyperframes check`, đường dẫn contact sheet, đã render bản nháp hay chưa (3D: chưa), dòng nguồn có hay không, và chỗ nào bạn đã lệch khỏi mô tả `visual` của kịch bản (và vì sao).
