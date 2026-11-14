# Cảnh có nhân vật nét mực (line-art)

Nhân vật vẽ bằng một nét mực mảnh trên nền giấy, nhìn nghiêng, không mặt, dựng bằng SVG trong HyperFrames. Dàn 12 nhân vật người Việt đã làm sẵn và khóa trong `assets/lineart/lineart.js`. Kiểm chứng chạy trọn quy trình ngày 2026-11-13 (lồng tiếng, `inject.py`, `hyperframes check`, snapshot, render hai khổ, `check_output.py` ĐẠT).

## Khi nào dùng

Khi brief ghi "kiểu hình: line-art", hoặc người dùng muốn nhân vật mà không cần 3D. So với 3D:

| Loại | Render đo được (workspace 2 nhân) |
|---|---|
| 2D chữ và biểu tượng | khoảng 1,3 giây cho mỗi giây video |
| Line-art, 2 nhân vật | khoảng 3,5 giây cho mỗi giây video (video 7,9 giây: 25 đến 30 giây mỗi khổ, bản nháp và bản cuối như nhau) |
| 3D, 2 đến 3 nhân vật | khoảng 13 đến 15 giây cho mỗi giây video |

Không cần tải gì từ mạng: nhân vật nằm sẵn trong skill. Video line-art 60 giây hai khổ render khoảng 10 phút tổng cộng; bản dài hơn khoảng 2 phút một khổ thì chạy nền.

Giới hạn hiện có (đừng viết kịch bản đòi những thứ này):
- Chỉ nhìn nghiêng (quay trái hoặc phải), không quay mặt ra khán giả.
- Không có miệng: nói bằng cử chỉ `talk` (tay mời, đầu gật theo nhịp).
- Chưa có tư thế ngồi, nằm, cúi nhặt đồ, chạy.
- Không tự đổi trang phục, màu, đạo cụ giữa video. Muốn mặc đồ theo vai thì chọn skin ở casting; muốn đổi đồ theo cảnh thì chốt `skin_theo_canh` ở casting (xem mục Skin theo vai cuối tài liệu).

## Dàn nhân vật (đã khóa)

| Mã | Tên | Vai trò | Nhóm | Nhận diện |
|---|---|---|---|---|
| `bac-si-minh` | Bác sĩ Minh | Bác sĩ | nam, người lớn | áo blouse trắng, ống nghe, kính |
| `dieu-duong-lan` | Điều dưỡng Lan | Điều dưỡng | nữ, người lớn | đồng phục xanh ngọc, mũ điều dưỡng, khẩu trang |
| `can-bo-thu` | Chị Thu | Cán bộ kiểm dịch y tế | nữ, người lớn | áo xanh nhạt, quần xanh đậm, mũ kê-pi, thẻ đeo, bìa hồ sơ |
| `co-giao-hoa` | Cô Hoa | Giáo viên | nữ, người lớn | áo dài xanh, tóc dài, ôm sách |
| `anh-duc` | Anh Đức | Nhân viên văn phòng | nam, người lớn | sơ mi, cà vạt đỏ, cặp da |
| `anh-tuan` | Anh Tuấn | Công nhân | nam, người lớn | mũ bảo hộ vàng, áo phản quang cam |
| `chi-nam` | Chị Năm | Bán hàng rong | nữ, người lớn | áo bà ba nâu đỏ, nón lá, đòn gánh hai thúng |
| `anh-khoa` | Anh Khoa | Hành khách | nam, người lớn | áo khoác xanh rêu, mũ lưỡi trai, khẩu trang, vali kéo |
| `ong-bay` | Ông Bảy | Người cao tuổi | nam, cao tuổi | tóc bạc, kính, chống gậy, lưng còng |
| `ba-sau` | Bà Sáu | Người cao tuổi | nữ, cao tuổi | áo bà ba tím, búi tóc bạc, giỏ đi chợ |
| `be-an` | Bé An | Học sinh | nam, trẻ em | sơ mi trắng, quần short xanh, khăn quàng đỏ, ba lô |
| `be-mai` | Bé Mai | Em nhỏ | nữ, trẻ em | váy cam hồng, tóc buộc |

Tên riêng chỉ là tên gọi trong dàn; trong video có thể gọi theo vai ("chị cán bộ kiểm dịch") nếu kịch bản muốn. Không tự đổi màu, trang phục, đạo cụ của nhân vật đã khóa. Vai không có trong dàn (vd cảnh sát, người nước ngoài): dùng nhân vật gần nhất, báo người dùng, và đề nghị bổ sung vào dàn bằng cách cập nhật skill (sửa `assets/lineart/src/cast/roster.ts`, build lại theo `assets/lineart/src/BUILD.md`).

## Thư viện `lineart.js`

Template line-art đã nạp sẵn. Agent dựng cảnh viết khối `SETUP` (nằm trong `L.setup(...)`), lớp chữ `SCENES` và tween `ANIMATION`; khối `DIRECTION` thường để trống.

```js
// SETUP: chạy lại từ đầu mỗi khi tua lùi, nên chỉ được dựng cảnh và hẹn giờ ở đây
L.ground(900);                                            // đường đất (y = chân nhân vật)
const thu = L.add("can-bo-thu", { x: 1200, y: 900, scale: 4, dir: -1 });   // dir -1: quay trái
const khoa = L.add("anh-khoa", { x: -150, y: 900, scale: 4 });            // bắt đầu ngoài khung
L.at(0.3, () => khoa.walkTo(850));                        // đi tới x = 850 rồi tự dừng
L.at(T.s01 + 2.6, () => thu.act("nod", 1.4));
L.at(T.s02 + 0.2, () => thu.act("talk", 2.6));          // nói gần hết câu (lấy duration của cảnh trong timeline.json)
L.at(T.s03, () => thu.face(1));                           // quay sang phải (khi đang đứng)
```

- `L.add(mã, { x, y, scale, dir })`: `y` là mặt đất dưới chân; `scale` 1 tương ứng người lớn cao khoảng 95 px. Gợi ý: khổ ngang `scale` 3,6 đến 4,5 (người lớn cao 340 đến 430 px, đất ở y 880 đến 920); khổ dọc `scale` 4,5 đến 5,5, đất ở y 1350 đến 1450 (phụ đề nằm dưới đất, lớp chữ ở trên). Trẻ em và người già tự nhỏ hơn theo tỉ lệ, dùng cùng `scale` với người lớn.
- `c.walkTo(x)`: đi tới hoành độ `x` rồi dừng; tự quay theo hướng đi. Tốc độ cố định theo dáng (người lớn khoảng 39 × scale px/giây, người già khoảng 17 × scale, trẻ em khoảng 33 × scale), chân không trượt. Muốn đến đúng lúc thì tính giờ xuất phát, không chỉnh tốc độ.
- `c.act(tên, giây)`: `wave` vẫy tay, `point` chỉ tay về phía trước, `present` mời hoặc giới thiệu, `talk` nói, `bow` cúi chào, `nod` gật đầu. Cử chỉ chỉ chạy khi đứng yên (đang đi thì chờ dừng hẳn). Người cầm đồ (Chị Thu, Cô Hoa, Chị Năm, Anh Khoa, Ông Bảy) làm cử chỉ bằng tay còn lại.
- `c.face(1 | -1)`: quay phải hoặc trái khi đang đứng.
- `L.at(t, fn)`: hẹn một việc ở giây `t` (dùng `T.<id> + ...`, không viết số giây tuyệt đối).
- Đạo cụ, khung cảnh vẽ thêm vào `L.back` (sau nhân vật) hoặc `L.front` (trước) bằng `LA.pen(L.back, độ dày)`, `LA.shape`, `LA.paint(L.back, màu)`; đặt `d` của path một lần trong `SETUP`. Nét cảnh nên dày 0,8 đến 1,2 để hợp nét nhân vật.

## Quy tắc đã rút ra khi thử

- **Tất định**: thư viện tự mô phỏng tiến từng bước 1/60 giây và dựng lại từ đầu khi tua lùi. Không dùng `Math.random`, `Date.now`; mọi thứ khởi tạo trong `SETUP`.
- **Hai người nói chuyện**: đứng cách nhau khoảng 250 đến 350 px ở `scale` 4, quay mặt vào nhau (`dir` ngược nhau). Người nghe dùng `nod` xen giữa câu của người nói.
- **Vào khung**: cho nhân vật xuất phát ngoài mép (x âm hoặc lớn hơn chiều rộng) và `walkTo` vào; người lớn đi 400 px ở `scale` 4 mất khoảng 2,6 giây, tính để dừng trước khi câu thoại bắt đầu.
- **Cử chỉ sau khi dừng**: hẹn `act` sau thời điểm dự kiến dừng ít nhất 0,4 giây.
- Khổ dọc: lớp chữ ở trên, nhân vật giữa khung, không đặt nhân vật dưới y 1450 (vùng phụ đề). Khổ ngang: lớp chữ góc trên trái.
- Nền mặc định là giấy trắng ngà. Muốn bối cảnh (quầy kiểm dịch, phòng khám) thì vẽ khối đơn giản bằng nét mực vào `L.back`, giữ nhiều khoảng trống.

## Kiểm tra

`hyperframes check` phải qua. Xem nhanh tư thế trước khi render: `cd build/<khổ> && hyperframes snapshot --at 1,3.5,5 --no-end -o snaps` (4 khung mất khoảng 5 giây) rồi xem `snaps/contact-sheet.jpg`.

## Ghi công

Thư viện nét vẽ gốc: github.com/JDhruv14/line-art-animation (giấy phép MIT, `assets/lineart/LICENSE-line-art-animation.txt`). Ghi vào `credits.md` của mọi video line-art: "Nhân vật nét mực dựng trên thư viện line-art-animation của JDhruv14 (MIT)".

## Skin theo vai

Nhân vật cố định (khuôn mặt, dáng, màu da, tóc, kính, giọng). Mỗi vai mặc một **skin**: trang phục, màu, mũ, đồ đeo, đạo cụ, kèm tên cử chỉ riêng của vai. Không ghi `skin` thì nhân vật mặc bộ đồ khóa trong roster như trước. Nguồn: `assets/lineart/src/cast/skins.ts` (dùng chung line-art và chibi).

```js
const sep = C.add("bac-si-minh", { x: 405, y: 1100, scale: 1, skin: "sep" });   // L.add cho line-art, cùng tùy chọn
C.at(T.s04, () => { sep.say(3.4); sep.act("ra-lenh", 3.4); });                 // "ra-lenh" -> point
```

| Skin | Đồ | Cử chỉ theo vai (-> cử chỉ có sẵn) |
|---|---|---|
| `sep` | áo vest tối, cà vạt, quần tối | `ra-lenh` -> point, `thuyet-phuc` -> present, `tra-loi` -> talk |
| `luat-su` | áo vest xám, quần tối, cầm hồ sơ (đạo cụ `books`) | `trinh-ho-so` -> present, `phan-tich` -> talk, `chi-dieu-khoan` -> point |
| `nhan-vien-van-phong` | sơ mi, cà vạt, cặp da | (dùng cử chỉ chung) |
| `bac-si` | áo blouse, ống nghe | `kham` -> point, `giai-thich` -> present |
| `dieu-duong` | đồng phục xanh ngọc, mũ, khẩu trang | `huong-dan` -> present |
| `can-bo-kiem-dich` | áo xanh nhạt, mũ kê-pi, thẻ đeo, bìa hồ sơ | `kiem-tra` -> point, `huong-dan` -> present |
| `cong-nhan` | mũ bảo hộ, áo phản quang | (chung) |
| `hanh-khach` | áo khoác, mũ lưỡi trai, khẩu trang, vali | (chung) |

Quy tắc:
- Kính thuộc về nhân vật, không thuộc skin: ai đeo kính vẫn đeo kính khi đổi skin, ai không đeo thì không có.
- Skin chốt ở cổng casting (`casting.json` mỗi vai ghi `character` và `skin`) rồi khóa như nhân vật. Vai cần đổi đồ theo cảnh thì ghi `skin_theo_canh` (mã cảnh -> mã skin, `goc` là bộ đồ khóa) ở casting; chỉ đổi ở ranh giới hai cảnh, không đổi giữa một cảnh, và không thêm bộ đồ nào chưa chốt.
- Cách dựng khi đổi skin theo cảnh: thêm cùng nhân vật nhiều lần, mỗi bản một skin, với khung hiện `from`/`until` (giây) nối tiếp nhau ở đầu cảnh đổi đồ. `python3 SKILL/scripts/vai.py kiem-casting casting.json` in sẵn các dòng này. Hai bản của cùng nhân vật trùng khung hiện thì thư viện báo lỗi.

```js
const hung = L.add("anh-duc", { x: 960, y: 900, scale: 4, skin: "sep", until: T.s03 });   // s01-s02: đi làm
const hungNha = L.add("anh-duc", { x: 960, y: 900, scale: 4, from: T.s03 });               // s03 trở đi: bộ đồ gốc
L.at(T.s03 + 0.2, () => hungNha.act("talk", 2));   // hẹn giờ cho đúng bản đang hiện
```
- Skin chỉ dùng được mẫu đồ đã có trong rig (xem `SUPPORTED` trong `assets/chibi/src/rig.ts`). Muốn đồ mới (vest dài, đồng phục cảnh sát...) phải vẽ vào cả hai rig rồi mới thêm skin; thư viện báo lỗi "chua ve ban chibi" nếu thiếu.
- Tên cử chỉ riêng chỉ là biệt danh; không thêm động tác mới. Thêm skin: viết vào `LIST` trong `skins.ts`, build lại (xem `assets/lineart/src/BUILD.md`).
- Cặp nhân vật và skin không bị giới hạn theo giới, nhưng đồ mặc kiểu `aodai`, `baba`, `dress` chưa có skin nên chỉ có trong bộ đồ khóa của nhân vật.
