# Cảnh vẽ nét (kiểu hình `ve-net`)

Mỗi cảnh là một tờ giấy. Bút **vẽ từng nét thật**: đường thẳng, vòng tròn, tia sáng, nét gạch chéo tô bóng, mũi tên, và chữ được viết ra từ trái sang phải; bàn tay cầm bút chạy theo đầu nét, kiểu "whiteboard animation". Mọi nét là SVG do studio tự vẽ bằng code, nên **không cần người dùng tạo ảnh** (khác `ve-tay`) và hợp với mọi chủ đề: giải thích cơ chế, quy trình từng bước, so sánh, định nghĩa, mẹo nhanh.

Kiểm chứng ngày 2026-11-13: chạy trọn quy trình với video mẫu 4 cảnh (lồng tiếng, `inject.py`, `hyperframes check` 0 lỗi, render hai khổ, `check_output.py` ĐẠT).

## Chọn `ve-net` hay `ve-tay`

| | `ve-net` | `ve-tay` |
|---|---|---|
| Hình | Nét đơn giản vẽ bằng code: hình khối, biểu tượng ghép sẵn, chữ | Tranh minh họa phức tạp (màu nước, nhân vật, cảnh vật) |
| Cách hiện | Bút vẽ theo từng nét của hình | Tranh hiện dần theo vệt cọ ngoằn ngoèo phủ vùng ảnh |
| Người dùng phải làm | Không thêm việc | Tạo mỗi cảnh một ảnh bằng công cụ tạo ảnh AI |
| Hợp với | Giải thích, quy trình, so sánh, số liệu đơn giản | Lịch sử, kể chuyện, cảnh có người và bối cảnh chi tiết |

Cần cảnh chi tiết (người thật, kiến trúc, trang phục) thì dùng `ve-tay`. Nội dung nhiều chữ và sơ đồ thì dùng `ve-net`.

## Khi nào dùng

Khi brief ghi "kiểu hình: ve-net", hoặc người dùng nói "vẽ từng nét", "bút vẽ ra", "viết tay lên bảng", "whiteboard vẽ nét", "bàn tay vẽ hình đơn giản". Hợp mọi thể loại.

| Loại | Render đo được (workspace 2 nhân, 1080p) |
|---|---|
| Vẽ nét | khoảng 3,3 giây cho mỗi giây video (video mẫu 16,8 giây: 55 giây mỗi khổ) |

Video 60 giây hai khổ, mỗi khổ 1 bản nháp và 1 bản cuối: khoảng 13 phút render. Mỗi lần render một khổ quá khoảng 7 phút thì chạy nền.

## Quy trình riêng của kiểu này

1. **Bước 2, biên kịch**: trường `visual` mô tả bố cục tờ giấy: những hình nào, ở đâu, vẽ theo thứ tự nào (thứ tự này là thứ tự bút vẽ, nên trùng thứ tự lời đọc). `on_screen.title` là chữ chính sẽ được **viết ra bằng bút** (ngắn, tối đa khoảng 8 từ). Mỗi cảnh nên có từ 2 đến 8 nét hay hình; cảnh quá nhiều hình thì không kịp vẽ.
2. **Không có bước tranh (3c)**: sau khi duyệt kịch bản (và lồng tiếng) thì dựng luôn.
3. **Bước 5**: `new_project.sh <PROJECT> <khổ> venet` cho từng khổ. Agent dựng cảnh viết `V.scene(...)` cho mỗi cảnh, rồi `inject.py`, rồi `ve_net_kiem_tra.sh` (xem mục Kiểm tra thời gian vẽ).

## Thư viện `venet.js`

Template đã nạp sẵn. Agent dựng cảnh viết khối `SETUP` (mỗi cảnh một khối lệnh) và, nếu cần, tween nhãn trong `ANIMATION`. Mỗi cảnh vẫn cần một thẻ `<section id="sc-<id>" class="clip scene" data-start="0" data-duration="1"></section>` trong khối `SCENES` (`inject.py` đồng bộ thời gian qua thẻ này; để trống được).

```js
const poly = VN.poly;
const S = V.scene("s02", { start: T.s02, space: [1000, 1000] });
S.sun(190, 380, 70);                                   // tròn rồi từng tia
S.arrow(330, 380, 470, 380, { w: 7 });                 // mũi tên
S.circle(700, 380, 150, { color: "blue", w: 8 });
S.hatch(poly.circle(700, 380, 142, "bottom"), { gap: 18 });   // gạch chéo nửa dưới
S.text("ngày", 250, 640, { size: 72, anchor: "middle", mark: true });  // chữ có vệt tô vàng
```

**Khung và tọa độ.** Tọa độ là "không gian thiết kế" của cảnh (mặc định 1000 x 1000, gốc ở góc trên trái, y hướng xuống), tự co vào vùng an toàn của khung hình, nên một đoạn mã dùng được cho cả hai khổ. Khổ dọc vùng an toàn là phần giữa (tránh nhãn trên và phụ đề dưới); khổ ngang là toàn khung trừ lề. Khổ ngang có nhiều chỗ thừa hai bên: cảnh rộng khai `space: V.pick([1000, 1000], [1600, 1000])`. Độ dày nét và cỡ chữ tính theo đơn vị thiết kế nên co theo. `V.portrait` cho biết đang dựng khổ nào.

**Tùy chọn của `V.scene(id, {...})`:**
- `start` (bắt buộc): `T.<id>`. Cảnh kéo dài đến khi cảnh sau bắt đầu; ở khoảng `fadeOut` giây cuối (0,35) cảnh mờ đi để cảnh sau vẽ trên giấy sạch. Cảnh cuối giữ đến hết video.
- `space`: `[rộng, cao]` không gian thiết kế (mặc định `[1000, 1000]`).
- `draw`: tổng số giây dành cho vẽ (mặc định: độ dài cảnh trừ lề thở và thời gian bàn tay rời khung). Thư viện tự co giãn tốc độ bút cho vừa `draw` (chậm tối đa 2 lần, nhanh tối đa khoảng 3 lần so với tốc độ tự nhiên).
- `delay`: giây chờ trước nét đầu (0,2); `fadeOut`; `seed`: đổi độ lệch tay vẽ; `hand: false`: không có bàn tay.

**Nét cơ bản** (mỗi hàm là một hay vài nét liên tiếp, vẽ đúng thứ tự gọi). Tùy chọn chung `{ color, w, at, dur }`: màu (tên hoặc mã CSS), độ dày nét, `at` (giây tính từ đầu cảnh, để nét bắt đầu đúng chữ trong lời đọc), `dur` (giây, ép thời gian vẽ nét này).
- `line(x1, y1, x2, y2)`, `arrow(x1, y1, x2, y2, { bend, head })` (`bend` 0,3 cho mũi tên cong), `polyline(points)`, `path(d)` (đường SVG tùy ý, dùng khi cần hình riêng), `rect(x, y, w, h, { r })`, `circle(cx, cy, r)`, `ellipse(cx, cy, rx, ry, { rot })`, `underline(x1, x2, y)`.
- `hatch(shape, { gap, angle, w })`: gạch chéo phủ một đa giác **lồi**; `shape` là `poly.circle(cx, cy, r, part)` (`part` là `"bottom"`, `"top"`, `"left"`, `"right"` để lấy nửa hình tròn, bỏ trống thì lấy cả hình), `poly.ellipse(cx, cy, rx, ry)`, `poly.rect(x, y, w, h)` hay mảng điểm. `shade(shape, { gap, color })` là tô mảng bằng nét to, hơi trong.
- `text(chuỗi, x, y, { size, weight, anchor, color, mark, under, lh })`: chữ **viết ra** từ trái sang phải, bút chạy theo mép chữ. `anchor` là `start`, `middle` hay `end`; xuống dòng bằng `\n` (mỗi dòng viết nối tiếp, `lh` là giãn dòng, mặc định 1,25); `mark: true` hay một mã màu thêm vệt tô bút dạ quang dưới chữ; `under: "red"` thêm nét gạch chân uốn sóng. Chữ dùng font Be Vietnam Pro của template (có đủ dấu tiếng Việt).
- `wait(giây)`: bút nghỉ một lúc, để khớp nhịp lời đọc.
- `write(chuỗi, x, y, { size, anchor, color, w, lh, mark, under, at, dur })`: **chữ viết tay thật**, bút đi theo từng nét chữ cái (kể cả dấu thanh, dấu mũ, dấu ngang, râu ơ ư, dấu nặng), khác `text` là chữ hiện dần từ trái sang phải. Cùng tùy chọn với `text` (`mark`, `under`, `anchor`, `\n` xuống dòng); `w` là độ dày nét (mặc định theo `size`). Mỗi chữ cái lệch nhẹ góc, đường cơ sở và cỡ theo hạt giống của cảnh, nên không giống phông chữ in. Ký tự không có trong bộ nét (ví dụ biểu tượng lạ) bị bỏ qua và ghi vào `warnings` (xem `V.warnings` hay `[venet]` trong console). Dùng cho tiêu đề và nhãn ngắn; câu dài nhiều dòng thì viết lâu hơn `text`, nên dùng `dur` hay `ve_net_kiem_tra.sh` để chắc kịp.

**Hình ghép sẵn** (tham số cuối là cỡ; tất cả nhận `color`, `w`): `sun(cx, cy, r)`, `moon`, `check`, `cross`, `heart`, `star`, `bulb` (bóng đèn), `person` (người que), `doc(x, y, w, h)` (tờ giấy), `clock`, `magnifier` (kính lúp), `house`, `tree`. Hình nào thiếu thì ghép từ nét cơ bản hay `path()`.

**Màu bút**: `ink` (mặc định), `red`, `orange`, `blue`, `green`, `yellow`, `gray`, `pink`, `mark`; hoặc mã CSS bất kỳ. Giấy kem `--paper` đổi được trong `index.html`.

**Thứ tự và nhịp.** Các nét vẽ lần lượt đúng thứ tự gọi hàm; bàn tay vào từ góc dưới phải, nhấc bút đi từ nét này sang nét khác, rồi rời khung sau nét cuối. Muốn một nét bắt đầu đúng lúc lời đọc nhắc tới thì đặt `at` (tính từ đầu cảnh, lấy từ độ dài đoạn lời trong `timeline.json`); khi đã dùng `at`, thư viện không tự co giãn tốc độ bút nữa.

## Biến ý trừu tượng thành hình

Cảnh giải thích dễ thành "chữ và biểu tượng xếp cạnh nhau". Muốn người xem hiểu bằng mắt, biên kịch dựng `visual` theo ba bước:

1. **Ý trừu tượng thành một hành động vật lý**: tắc, rò rỉ, dồn lại, lọc, đẩy, chìm, lan ra, chặn lại.
2. **Hệ thống thành một đồ vật đơn giản**: phễu, cái cân, bình, giếng, băng chuyền, cái thang, cây cầu, cánh cổng, tảng đá.
3. **Người que (`person`) làm hành động đó với đồ vật**. Bỏ người que đi mà hình vẫn đủ nghĩa thì người que chỉ để trang trí: nghĩ lại.

Sáu khuôn cảnh hay dùng (chọn một, nội dung cụ thể thì tự nghĩ):

| Khuôn | Hình | Thứ tự bút vẽ |
|---|---|---|
| Cỗ máy | người que vận hành một hộp có phễu và cửa ra | hộp, phễu, đầu vào rơi vào, mũi tên, kết quả ở cửa ra |
| Trước và sau | trái rối (nét chồng chéo, màu đỏ), phải gọn (khối xếp hàng, màu xanh) | vạch giữa, bên rối, mũi tên cam, bên gọn |
| Hành trình gặp hố | một con đường có hố hay mốc dọc đường | đường, người que, từng hố hay mốc theo thứ tự lời đọc, đích |
| Một thành nhiều | một nguồn tách ra nhiều nhánh | nguồn, các mũi tên tỏa ra, kết quả từng nhánh |
| Đẩy đá lên dốc | người que đẩy tảng đá, qua đỉnh thì đá lăn | dốc, tảng đá, người que, mũi tên đi lên, mũi tên lăn xuống |
| Múc từ giếng | trong đống rối chỉ lấy ra một thứ có giá trị | giếng, đống nét rối, gầu, mũi tên kéo lên, vật lấy được |

Quy ước màu, giữ suốt video: `ink` là cấu trúc và người que; `orange` chỉ dành cho dòng chảy và mũi tên; `red` là vấn đề hay cảnh báo; `blue` hoặc `green` là kết quả tốt. Giữ nhiều giấy trống, chủ thể chiếm khoảng một nửa tờ.

Tất cả khuôn trên dựng được bằng các hàm có sẵn (`person`, `rect`, `circle`, `arrow`, `path`, `hatch`); không cần thư viện mới. Phương pháp này tham khảo ý tưởng từ skill Ink Theater của OpenMontage; không dùng mã hay hình của dự án đó.

## Bố cục gợi ý

- **Tiêu đề trước, hình sau**: nét đầu tiên là `text` (tiêu đề cảnh), kèm `under`, rồi mới vẽ hình minh họa. Người xem tắt tiếng vẫn đọc được ý.
- **Một ý một cảnh**: 2 đến 8 nét. Cảnh dài hơn 8 giây thì chia đôi hay thêm `wait`.
- **So sánh**: hai cột, mỗi cột một `check` hay `cross` và một dòng chữ; kẻ `line` đứng ở giữa trước.
- **Quy trình**: các hình tròn đánh số nối bằng `arrow`, chữ bên cạnh.
- **Giữ khoảng thở**: chừa ít nhất khoảng 60 đơn vị giữa các hình để bút và bàn tay không che nhau.

## Kiểm tra thời gian vẽ

Sau `inject.py` (để có `T`), chạy:

```bash
bash SKILL/scripts/ve_net_kiem_tra.sh build/<khổ>
```

In mỗi cảnh một dòng: số nét, thời điểm vẽ xong và thời điểm cảnh kết thúc. Dòng có `KHONG KIP` hay mục `[CANH BAO]` nghĩa là nét cuối bị cắt khi cảnh kết thúc: bớt nét, bớt chữ, hoặc nhờ biên kịch kéo dài lời đọc. Script thoát mã 1 khi có cảnh báo.

## Tiếng bút (tùy chọn)

Mỗi nét có tiếng bút ma sát trên giấy, chữ viết thành từng đợt ngắn, vệt dạ quang êm và trầm hơn, mỗi cảnh mới có tiếng lật giấy nhẹ. Mọi tiếng tổng hợp bằng numpy (nhiễu trắng lọc dải), không dùng mẫu âm thanh bên ngoài. Mốc thời gian lấy đúng từ composition, nên tiếng khớp nét vẽ.

```bash
bash SKILL/scripts/ve_net_kiem_tra.sh build/<khổ> --json <PROJECT>/venet-report.json   # thêm --json để lưu thời điểm từng nét
python3 SKILL/scripts/tieng_but.py <PROJECT>                                          # ghi audio/hieu-ung.wav
python3 SKILL/scripts/nhac_nen.py <PROJECT> --kieu <kiểu>                              # có hieu-ung.wav thì tự trộn cùng nhạc
python3 SKILL/scripts/nhac_nen.py <PROJECT> --chi-hieu-ung                             # brief ghi không nhạc: chỉ ghép tiếng bút
```

- Tiếng bút không bị bộ nén theo lời đọc như nhạc nền; giữ nhỏ bằng `--muc` của `tieng_but.py` (đỉnh mặc định -18 dBFS). `--khong-hieu-ung` ở `nhac_nen.py` bỏ qua file này; `--bo` gỡ cả nhạc lẫn tiếng bút.
- Hai khổ có thể lệch nhịp vẽ (khác tốc độ co giãn): lấy báo cáo từ khổ nào thì tiếng khớp khổ đó; dùng cho cả hai khổ thì nên lấy báo cáo ở khổ đang giao trước, hoặc chạy riêng từng khổ vào `--bao-cao` khác.
- Đã kiểm chứng: lấy báo cáo thật từ Chrome, tạo file tiếng tất định (chạy lại cho cùng một file), năng lượng chỉ rơi vào các khoảng có nét, ghép vào video mẫu không chồng tiếng khi chạy lại, `--bo` trả đúng bản gốc, nhạc nền một mình cho ra âm thanh giống hệt bản cũ. **Chưa nghe thử bằng tai người** và chưa chạy trên video HyperFrames thật: nghe lại và chỉnh `--muc` trước khi giao.
- `credits.md`: "Tiếng bút: do studio tự tổng hợp bằng code, không dùng mẫu âm thanh bên ngoài".

## Quy tắc đã rút ra khi thử

- **Tất định**: độ lệch tay vẽ sinh từ hạt giống cố định (`seed`); không dùng `Math.random`, `Date.now`.
- Không thêm `filter` SVG hay CSS lên nét (blur, shadow): render chậm gấp nhiều lần.
- `hatch` chỉ đúng với đa giác lồi. Hình lõm thì chia thành các phần lồi, hay dùng `shade` lên hình chữ nhật bao.
- `text` **không** vẽ từng nét chữ cái mà hiện dần từ trái sang phải với bút chạy theo mép; đủ để thấy "đang viết" nhưng không giống nét bút thật. Muốn nét chữ thật thì dùng `write` (bộ nét `assets/venet/venet-chu.js`, sinh từ phông Patrick Hand giấy phép OFL bằng `bash tools/build_venet_chu.sh`; phông chỉ dùng để tạo bộ nét, không cần nạp vào video).
- `write` mới được thử trong trình duyệt (Chrome, ảnh chụp ở nhiều thời điểm, đủ dấu tiếng Việt, đúng thứ tự nét); chưa có số đo thời gian render trong HyperFrames. Chạy thử một video mẫu và ghi số đo vào đây trước khi đặt `write` làm mặc định cho chữ chính của cảnh.
- Chữ dài hơn bề rộng không gian thiết kế sẽ tràn khung: ngắt dòng bằng `\n` hoặc giảm `size`.

## Kiểm tra

`hyperframes check` phải 0 lỗi. Cảnh báo có thể bỏ qua: `nested_structure_needs_subcomposition`; `[non-blocking] Failed to load resource ... 404` khi render (đã gặp ở video mẫu, render vẫn ĐẠT). Xem nhanh trước khi render: `cd build/<khổ> && hyperframes snapshot --at <giữa cảnh>,<cuối cảnh> --no-end -o snaps`; chụp cả thời điểm gần cuối mỗi cảnh để chắc nét cuối đã vẽ xong.

## Ghi công

Ghi vào `credits.md`: "Nét vẽ, chữ viết tay, bàn tay cầm bút: đồ họa tự vẽ của studio (SVG)". Chữ dùng font Be Vietnam Pro cài sẵn trong template, như các kiểu hình khác. Không có tài nguyên ngoài khác.

Video dùng `write` thì ghi thêm: "Chữ viết tay: nét chữ lấy từ phông Patrick Hand (Copyright (c) 2010-2012 Patrick Wagesreiter), SIL Open Font License 1.1". File giấy phép: `assets/venet/LICENSE-patrick-hand-OFL.txt`.
