# Cảnh có nhân vật 3D

Nhân vật hoạt hình chibi trong căn phòng cắt tường kiểu "nhà búp bê", dựng bằng Three.js trong HyperFrames. Kiểm chứng chạy trọn quy trình ngày 2026-11-12.

## Khi nào dùng

Chỉ khi brief ghi "nhân vật 3D: có". Mặc định là video 2D (chữ, biểu tượng), vì 3D render chậm hơn nhiều:

| Loại | Thời gian render đo được (workspace 2 nhân) |
|---|---|
| 2D chữ và biểu tượng | khoảng 1,3 giây cho mỗi giây video |
| 3D, 2 nhân vật | khoảng 13 giây cho mỗi giây video |
| 3D, 3 nhân vật | khoảng 15 giây cho mỗi giây video |

Bản nháp (`preview`) không nhanh hơn bản cuối với cảnh 3D: đo 223 giây cho 17,6 giây video, 2 nhân vật, khổ dọc (khoảng 12,7 giây cho mỗi giây video). Quy trình render 1 bản xem trước và 1 bản cuối mỗi khổ, nên video 3D 60 giây cả hai khổ mất khoảng 40 phút render (3 lần, mỗi lần khoảng 13 phút). Báo người dùng con số này ở bước 0 khi họ chọn 3D. Muốn nhanh hơn: một khổ, ít nhân vật, hoặc chỉ dùng 3D cho vài cảnh.

Một lệnh chạy thường bị cắt ở 10 phút, nên video 3D dài hơn khoảng 40 giây phải render ở chế độ nền. Agent dựng cảnh không render 3D; chỉ chụp khung hình bằng `hyperframes snapshot` (5 khung hình mất khoảng 9 giây).

Cần mạng tới `drive.google.com` và `drive.usercontent.google.com` (người dùng cho phép trong claude.ai > Settings > Capabilities). `setup.sh` báo nếu thiếu.

## Nhân vật

Nguồn: Quaternius, Ultimate Animated Character Pack, giấy phép CC0 (không cần ghi công nhưng nên ghi trong `credits.md`). Danh mục trong `assets/sim3d/characters.json`; xem nhanh: `python3 SKILL/scripts/get_characters.py --list`.

Nhóm hay dùng: bác sĩ (`Doctor_Female_Young`, `Doctor_Female_Old`, `Doctor_Male_Young`, `Doctor_Male_Old`), người dân (`Casual_*`, `Casual2_*`, `Casual3_*`, `Casual_Bald`), người lớn tuổi (`OldClassy_*`), nhân viên văn phòng (`Suit_*`), công nhân đội mũ bảo hộ (`Worker_*`), đầu bếp (`Chef_*`). Không có trẻ em: dùng nhân vật thường với `height` khoảng 1,1 đến 1,2.

Đặc điểm cần biết:
- Nguyên bản da và mặt màu đen, mắt trắng. `loadChar` đổi vật liệu `Skin` sang màu da (`S.SKIN.sang`, `vua`, `ngam`, `nau`) và `Face` (mắt) sang nâu đậm. Đổi màu áo bằng `colors: { TenVatLieu: 0x... }`; tên vật liệu của từng nhân vật có trong `ch.materials` (vd `Shirt`, `Pants`, `Hair`, `Main`).
- **Không có miệng**: nhân vật "nói" bằng gật đầu theo âm lượng lời đọc và cử chỉ tay (`S.talk`). Với phong cách này trông vẫn tự nhiên.
- Hoạt ảnh có sẵn: `Idle`, `Walk`, `Run`, `Jump`, `SitDown`, `StandUp`, `PickUp`, `Victory`, `Walk_Carry`, `Run_Carry` (các clip đánh nhau `Punch`, `SwordSlash`, `Shoot_OneHanded`, `Death`, `Defeat`, `RecieveHit`, `Roll` không dùng cho nội dung truyền thông).
- Động tác thêm bằng code (gọi sau `S.animate`): `S.wave` vẫy tay, `S.point` dang tay chỉ sang bên, `S.talk` nói, `S.listen` gật gù nghe.

## Thư viện `sim3d.js`

Template 3D đã nạp sẵn; agent chỉ viết ba khối `SETUP`, `DIRECTION`, `ANIMATION` và lớp chữ `SCENES`.

```js
// SETUP (chạy một lần)
const room = S.buildRoom(stage, "phong-kham");          // "nha" | "phong-kham" | "cua-khau"
const doc = await S.loadChar(stage, "Doctor_Female_Young.gltf", { height: 1.7, skin: S.SKIN.sang });
const dan = await S.loadChar(stage, "Casual_Male.gltf", { height: 1.72, skin: S.SKIN.ngam, colors: { Shirt: 0x2a9d8f } });
S.place(dan, -1.0, 0.7, 0.55);                            // x, z, góc quay

// DIRECTION (chạy mỗi khung hình, chỉ phụ thuộc t)
S.cameraPath(stage.camera, [{ t: 0, pos: [3.4, 4.6, 7.6], look: [-0.2, 0.95, 0.2] },
                            { t: T.s02, pos: [2.6, 3.6, 6.4], look: [0.4, 1.0, 0.6] }], t);
S.walk(doc, { from: [3.0, 0.9], to: [0.4, 0.9], t0: 0, t1: 1.4, endAngle: 0.45 }, t);
S.animate(doc, [["Walk", 0, 1.4], ["Idle", 1.4, DUR]], t);
S.wave(doc, t, 1.4 + S.TURN, 3.2);
S.talk(doc, t, T.s02, T.s02 + 4.0);
S.animate(dan, [["Idle", 0, DUR]], t + 1.3);            // lệch pha để hai người không thở đồng loạt
S.listen(dan, t, T.s01);
```

Quy tắc đã rút ra khi thử:
- **Phòng 7 x 7**, tâm ở gốc tọa độ; tường sau ở z = -3,5, tường trái ở x = -3,5. Đặt nhân vật trong vùng x từ -2 đến 2, z từ -1 đến 1,5 để camera mặc định thấy rõ. Đồ vật cố định của từng phòng (tránh đặt nhân vật đè lên):
  - `nha`: sofa quanh (-1,6; -2,6), chậu cây (2,8; -2,8), xô nước (2,0; 1,2) có `room.water` để tạo gợn nước.
  - `phong-kham`: bàn khám (1,3; -1,6), ghế đôn (1,3; -0,9), giường (-2,2; -2,7), tủ thuốc (2,6; -3,15).
  - `cua-khau`: quầy kiểm tra (0,9; -2,2), cột dây chắn ở z = 0,6 tại x = -2,4; -1,2; 0 (người xếp hàng đứng ở z khoảng 1,2), bảng chỉ dẫn trên tường sau (chữ trên bảng đặt bằng lớp chữ HTML).
- **Hướng nhìn khán giả** với camera mặc định là góc khoảng 0,4 đến 0,5. Góc theo hướng (dx, dz) là `Math.atan2(dx, dz)`; có sẵn `S.angleTo`.
- **Mỗi nhân vật một lần gọi `S.walk`**. Hàm đặt vị trí ở mọi thời điểm `t` (trước `t0` nhân vật đứng ở `from`), nên gọi hai lần cho cùng một nhân vật thì lần sau ghi đè lần trước: nhân vật đứng sẵn ở điểm xuất phát của đoạn sau ngay từ giây 0 và quay lưng về khán giả. Đi nhiều chặng thì truyền mảng, `from` của chặng sau trùng `to` của chặng trước:
  ```js
  S.walk(doc, [{ from: [3.0, 0.9], to: [0.4, 0.9], t0: 0, t1: 1.4, endAngle: 0.45 },
               { from: [0.4, 0.9], to: [1.6, 0.2], t0: T.s03, t1: T.s03 + 1.2, endAngle: 0.45 }], t);
  S.animate(doc, [["Walk", 0, 1.4], ["Idle", 1.4, T.s03], ["Walk", T.s03, T.s03 + 1.2], ["Idle", T.s03 + 1.2, DUR]], t);
  ```
- **Chờ quay người xong**: sau khi `walk` kết thúc ở `t1`, nhân vật mất `S.TURN` (0,6 giây) để quay; động tác hướng về khán giả bắt đầu từ `t1 + S.TURN`, nếu không nhân vật vẫy tay khi đang quay lưng.
- **Cử chỉ vừa phải**: biên độ trong thư viện đã chỉnh qua thử; tăng thêm thì tay vung quá đà.
- **Lệch pha `Idle`** giữa các nhân vật (`t + 1.3`, `t + 0.6`) để cảnh tự nhiên.
- Khổ dọc: lớp chữ nằm ở phần trên, phụ đề ở dưới; giữ nhân vật ở giữa khung. Khổ ngang: lớp chữ ở góc trên trái, đặt nhân vật lệch phải.
- Lớp chữ `.scene` của template 3D trong suốt, không che toàn cảnh; `.title` là thẻ nền sáng, `.body` là dòng phụ.

## Kiểm tra

`hyperframes check` phải qua. Lỗi hay gặp:
- `gsap_timeline_not_registered`: phải giữ nguyên đoạn cuối template (tạo `tl` và đăng ký trong module, sau khi nhân vật đã nạp).
- `multiple_root_compositions`: có file HTML thừa trong thư mục build; chuyển ra ngoài.
- Nhân vật không hiện: sai tên file trong `loadChar` (phải có `.gltf`) hoặc chưa chạy `get_characters.py`.

Xem nhanh tư thế trước khi render cả video: `cd build/<khổ> && hyperframes snapshot --at 1.5,4,7 --no-end -o snaps` rồi xem `snaps/contact-sheet.jpg`.
