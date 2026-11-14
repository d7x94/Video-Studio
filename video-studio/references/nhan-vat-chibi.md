# Cảnh có nhân vật chibi

Nhân vật hoạt hình đầu to nhìn chính diện: viền nâu đậm, màu phẳng có một lớp bóng, má hồng, viền trắng kiểu sticker, nền mờ phía sau, phụ đề chữ trắng viền đen. Dựng bằng SVG trong HyperFrames theo kiểu cut-out (các mảnh vẽ một lần, chỉ đổi tư thế và nét mặt), có nhép miệng theo lời đọc. Kiểm chứng chạy trọn quy trình ngày 2026-11-13 cho cả kiểu tay ống và tay chân que (lồng tiếng 2 giọng, `inject.py`, `hyperframes check` 0 lỗi, render hai khổ, `check_output.py` ĐẠT).

## Khi nào dùng

Khi brief ghi "kiểu hình: chibi", hoặc người dùng muốn kiểu hoạt hình dễ thương, đầu to, có biểu cảm và nhép miệng (clip hội thoại ngắn kiểu TikTok). So với các kiểu khác:

| Loại | Render đo được (workspace 2 nhân) |
|---|---|
| 2D chữ và biểu tượng | khoảng 1,3 giây cho mỗi giây video |
| Line-art, 2 nhân vật | khoảng 3,5 giây cho mỗi giây video |
| Chibi, 2 nhân vật | khoảng 4,5 giây cho mỗi giây video (video 10,3 giây: 46 giây mỗi khổ, 1080p) |
| Chibi tay chân que, không viền sticker (khổ ngang, 3 nhân vật, đèn pin) | khoảng 3,3 giây cho mỗi giây video (video 9,6 giây: 32 giây) |
| Chibi tay chân que, có viền sticker và `C.shade` (khổ dọc, 2 nhân vật, đèn pin) | khoảng 4,9 giây cho mỗi giây video (video 9,6 giây: 47 giây) |
| 3D, 2 đến 3 nhân vật | khoảng 13 đến 15 giây cho mỗi giây video |

Không cần tải gì từ mạng. Video 60 giây hai khổ, mỗi khổ 1 bản nháp và 1 bản cuối: khoảng 18 phút render; bản dài hơn khoảng 2 phút một khổ thì chạy nền.

Có hai kiểu tay chân, chọn khi `C.add`:
- `limbs: "chibi"` (mặc định): tay áo ống tròn, chân ngắn, viền sticker trắng. Hợp clip hội thoại đứng.
- `limbs: "que"`: tay chân là một nét que cong, đầu mút chấm tròn, chân dài hơn (kiểu rubber hose). Uốn tư thế tự nhiên hơn, ngồi và chạy trông đẹp hơn, cầm được đèn pin. Hợp cảnh có hành động, cảnh tối, kể chuyện. Thường tắt viền sticker (`sticker: 0`) cho giống hoạt hình kể chuyện.

Giới hạn hiện có (đừng viết kịch bản đòi những thứ này):
- Chỉ nhìn chính diện, hơi nghiêng về một phía; quay trái hoặc phải bằng cách lật gương nhanh (đồ cầm tay đổi bên theo).
- Đi, chạy theo chiều ngang; ngồi trên ghế nhìn chính diện (kiểu `chibi` ngồi trông như ngồi xổm, nên dùng `que` cho cảnh ngồi). Không nằm, không cúi nhặt đồ, không leo trèo.
- Đồ cầm thêm ngoài dàn chỉ có đèn pin (kiểu `que`). Không tự đổi trang phục, màu, đạo cụ giữa video. Muốn nhân vật mặc đồ theo vai thì chọn skin ở casting; muốn đổi đồ theo cảnh thì chốt `skin_theo_canh` ở casting (xem mục Skin theo vai cuối tài liệu).
- Động tác sinh hoạt (đánh răng, ăn, uống, nghe điện thoại, khóc, sợ, lạnh, reo mừng, nhảy) chỉ có ở kiểu `que`, qua 10 clip chuyển động thật ở mục Động tác mocap. Tay không cầm đồ vật: bàn chải, cốc, điện thoại là ngầm hiểu.

## Dàn nhân vật

Dùng chung dàn 12 nhân vật đã khóa với line-art (`references/nhan-vat-line-art.md`): cùng mã, tên, trang phục, màu, đạo cụ. Bản chibi chỉ thêm màu da và màu tóc (bảng `LOOKS` trong `assets/chibi/src/rig.ts`). Một người có thể xuất hiện ở cả hai kiểu hình mà vẫn nhận ra. Thêm hay sửa nhân vật thì sửa `assets/lineart/src/cast/roster.ts` (đã khóa, chỉ sửa khi người dùng yêu cầu), thêm màu da vào `LOOKS`, rồi build lại cả hai thư viện (`tools/build_lineart.sh`, `tools/build_chibi.sh`). Trang phục mới chưa có trong rig thì thư viện báo lỗi "chua ve ban chibi", không vẽ sai.

Đồ cầm tay luôn ở tay sau (bên trái hình khi `dir` 1): Chị Thu ôm bìa hồ sơ, Cô Hoa ôm sách, Anh Khoa kéo vali, Anh Đức xách cặp, Bà Sáu xách giỏ, Ông Bảy chống gậy, Chị Năm gánh đòn gánh trên vai, Bé An đeo ba lô. Cử chỉ làm bằng tay trước.

## Thư viện `chibi.js`

Template chibi đã nạp sẵn. Agent dựng cảnh viết khối `SETUP` (nằm trong `C.setup(...)`), lớp chữ `SCENES` và tween `ANIMATION`; khối `DIRECTION` thường để trống.

Ví dụ kiểu `que` trong cảnh tối (đã chạy thử, khổ ngang):

```js
C.shade(0.4);
const tuan = C.add("anh-tuan", { x: -260, y: 1010, scale: 2.6, dir: 1, limbs: "que" });
const thu = C.add("can-bo-thu", { x: 2200, y: 1010, scale: 2.6, dir: -1, limbs: "que" });
tuan.hold("den-pin");
C.at(0, () => tuan.walkTo(720));
C.at(T.s01 + 3.3, () => tuan.act("sweep", 2.6));
C.at(T.s02 - 0.4, () => thu.walkTo(1300));
C.at(T.s02, () => { tuan.say(2.5); tuan.expr("surprised", 2.4); });
```

Ví dụ kiểu `chibi` (clip hội thoại):

```js
// SETUP: chạy lại từ đầu mỗi khi tua lùi, nên chỉ được dựng cảnh và hẹn giờ ở đây
const thu = C.add("can-bo-thu", { x: 300, y: 1900, scale: 3.3, dir: 1 });     // dir 1: hướng sang phải
const khoa = C.add("anh-khoa", { x: 1400, y: 1900, scale: 3.3, dir: -1 });  // bắt đầu ngoài khung
C.at(0, () => khoa.walkTo(790));                                            // đi vào rồi tự dừng
C.at(T.s01, () => { thu.say(3.23); thu.expr("wink", 1.6); khoa.expr("deadpan", 3.2); });
C.at(T.s01 + 1.4, () => thu.act("present", 1.6));
C.at(T.s02, () => { khoa.say(2.67); khoa.expr("surprised", 1.2); thu.expr("neutral"); });
```

- `C.add(mã, { x, y, scale, dir, limbs })`: `y` là mặt đất dưới chân; `scale` 1 tương ứng người lớn cao khoảng 300 px (đầu khoảng 160 px), trẻ em khoảng 230 px; kiểu `que` cao hơn khoảng 46 px. Kiểu `que` toàn thân trong khổ ngang: `scale` 2,4 đến 2,8, `y` 980 đến 1030. Gợi ý bố cục kiểu clip hội thoại: khổ dọc `scale` 3 đến 3,4, `y` 1850 đến 1950 (đầu ở giữa khung, phụ đề đè lên thân), hai người cách nhau khoảng 490 px; khổ ngang `scale` 3,2 đến 3,6, `y` 1300 đến 1400 (cắt ngang hông), hai người cách nhau khoảng 680 px. Nửa trên khổ dọc để trống cho lớp chữ.
- `c.say(giây)`: nhép miệng trong khoảng này theo âm lượng lời đọc (`speech.js` do `inject.py` sinh từ `voiceover.wav`). Gọi ở `T.<id>` với giây bằng `visual_duration` của cảnh trong `timeline.json`; lúc im lặng miệng tự khép. Chỉ người đang nói trong cảnh được gọi `say`. Nhân vật đeo khẩu trang thì khẩu trang co giãn theo lời.
- `c.expr(tên, giây?)`: `neutral`, `happy` (mắt cười, miệng mở), `wink` (nháy mắt), `deadpan` (mắt dẹt, chán), `surprised` (mắt tròn), `worried` (lo). Không ghi giây thì giữ đến khi đổi. Mắt tự chớp khi `neutral`, `surprised`, `worried`.
- `c.act(tên, giây)`: `wave` vẫy tay, `point` chỉ về hướng đang nhìn, `present` mời hoặc giới thiệu, `talk` tay đưa trước ngực theo nhịp nói, `bow` cúi chào, `nod` gật đầu. Cử chỉ chỉ chạy khi đứng yên.
- `c.walkTo(x)`: đi tới hoành độ `x` rồi dừng, tự quay theo hướng đi. Tốc độ: người lớn khoảng 120 × scale px/giây, trẻ em khoảng 105 × scale, người già khoảng 70 × scale. Muốn đến đúng lúc thì tính giờ xuất phát.
- `c.runTo(x)`: chạy tới `x` (nhanh khoảng 2,3 lần đi bộ, nhún và vung tay mạnh hơn).
- `c.sit(true | false)`: ngồi xuống hoặc đứng lên trong 0,35 giây, tại chỗ. Vẽ ghế dưới người ngồi bằng `C.bench(x, y, scale, rộng, chiều cao mặt ghế)`: chiều cao mặt ghế theo đơn vị hình là 60 cho `que`, 30 cho `chibi`; trẻ em nhân 0,7. Gọi `walkTo` khi đang ngồi thì tự đứng lên rồi mới đi.
- `c.hold("den-pin" | null)` (chỉ kiểu `que`): cầm đèn pin bằng tay trước, có luồng sáng hình nón theo hướng cẳng tay; tay nghỉ là rọi xuống đất phía trước. `c.act("sweep", giây)` rọi quét qua lại.
- `c.play(mã, giây?)` (chỉ kiểu `que`): diễn một clip chuyển động thật, xem mục Động tác mocap.
- `c.face(1 | -1)`: quay sang phải hoặc trái (lật gương trong 0,16 giây).
- `C.at(t, fn)`: hẹn một việc ở giây `t` (dùng `T.<id> + ...`, không viết số giây tuyệt đối).
- `C.shade(độ tối, màu)`: làm tối cảnh (đêm, phòng tắt đèn), mặc định 0,4: phủ lớp tối và viền tối lên nền, nằm sau nhân vật nên nhân vật vẫn rõ. Gọi ở đầu `SETUP`, trước `C.bench` nếu muốn ghế sáng như nhân vật.
- Tắt viền sticker cho cả cảnh: `CB.createChibiStage(..., { width, height, sticker: 0 })` (sửa dòng tạo `C` trong template).
- Vẽ thêm vào `C.back` (sau nhân vật) hoặc `C.front` (trước) bằng `CB.fill(lớp, d, màu)`, `CB.line(lớp, d, độ dày)`; viền dùng màu `CB.OUT` cho hợp nét nhân vật.

## Động tác mocap (chỉ kiểu `que`)

Tay chân que diễn theo chuyển động ghi từ người thật (CMU Motion Capture Database), đã chiếu sang góc nhìn chính diện và chỉnh cho đầu to của chibi: tay đưa lên miệng hay tai thì chạm đúng mặt chibi. Agent chỉ chọn mã clip và thời điểm, không chỉnh tay chân bằng số.

| Mã | Động tác | Dài (giây) | Gợi ý dùng |
|---|---|---|---|
| `danh-rang` | đánh răng, tay trước đưa lên miệng | 6,5 | vệ sinh răng miệng |
| `an` | ăn bằng tay, đưa lên miệng | 5,7 | ăn uống, an toàn thực phẩm |
| `uong-nuoc` | cầm cốc uống | 3,7 | uống đủ nước, uống thuốc |
| `nghe-dien-thoai` | áp điện thoại lên tai | 3,7 | gọi tổng đài, báo y tế |
| `vui-mung` | dang tay reo vui | 5,3 | kết thúc có hậu, khỏi bệnh |
| `khoc` | hai tay ôm mặt khóc | 7,3 | tình huống xấu, hối hận (thêm `expr("worried")`) |
| `so-hai` | co người, tay đưa lên miệng | 5,7 | hoảng sợ, giật mình (thêm `expr("surprised")`) |
| `lanh-run` | ôm người run | 8,5 | rét, sốt rét run |
| `nhay` | nhún rồi nhảy lên tại chỗ | 2,9 | mừng rỡ, bất ngờ |
| `nhay-dang-tay` | nhảy dang tay chân | 2,7 | tập thể dục |

```js
C.at(T.s01 + 0.1, () => minh.play("danh-rang", 3.0));   // cắt còn 3 giây cho vừa cảnh
C.at(T.s02 + 0.1, () => thu.play("uong-nuoc", 2.0));
C.at(T.s02 + 2.2, () => thu.play("vui-mung", 1.5));      // clip sau trộn chéo từ clip trước
```

- `play(mã, giây?)` trả về số giây sẽ diễn. Không ghi giây thì diễn hết clip; ghi ngắn hơn thì cắt, và 0,3 giây cuối trộn về tư thế nghỉ. Clip giữ khung cuối nếu `giây` dài hơn clip.
- Tự trộn vào 0,3 giây đầu. Gọi clip mới khi clip cũ chưa xong thì trộn chéo, không giật.
- Đang `walkTo`, `runTo` thì clip tạm dừng (như `act`); cho nhân vật đứng yên rồi mới `play`. Đang `hold("den-pin")` thì đèn đi theo bàn tay trước.
- Kiểu `chibi` (tay ống) gọi `play` thì không có tác dụng và in cảnh báo ra console.
- Mã không có trong bảng thì thư viện báo lỗi. Muốn thêm động tác: thêm dòng vào `tools/mocap/catalog.json` (mã file CMU, đoạn giây, kích thước, sha256) rồi chạy `python3 tools/mocap/bvh2que.py` và `bash tools/build_chibi.sh` trong repo skill. Đã thử và bỏ vì nhìn chính diện, không đạo cụ thì không ra động tác: quét nhà, bế em bé, cười, buồn, đập muỗi.

Render video có clip mocap đo được khoảng 4,8 giây cho mỗi giây video (khổ dọc, 2 nhân vật có viền sticker, video 7,1 giây: 34 giây), như chibi thường.

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

Video có dùng `play` (động tác mocap) ghi thêm: "Chuyển động: dữ liệu từ CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), cơ sở dữ liệu được tài trợ bởi NSF EIA-0196217."

## Skin theo vai

Mỗi vai có ba lớp: **nhân vật** (khuôn mặt, dáng, màu da, tóc, kính, giọng; khóa cứng), **skin** (trang phục, màu, mũ, đồ đeo, đạo cụ) và **tính cách** (cách diễn: lời thoại, nhịp đọc, biểu cảm, cử chỉ theo tình huống; xem mục Tính cách bên dưới). Không ghi `skin` thì nhân vật mặc bộ đồ khóa trong roster như trước. Nguồn skin: `assets/lineart/src/cast/skins.ts` (dùng chung line-art và chibi).

```js
const sep = C.add("bac-si-minh", { x: 405, y: 1100, scale: 1, skin: "sep", tinhCach: "nghiem-khac" });
C.at(T.s04, () => { sep.noi(3.4); sep.act("ra-lenh", 3.4); });   // "ra-lenh" -> point theo tính cách nghiem-khac
```

| Skin | Đồ |
|---|---|
| `sep` | áo vest tối, cà vạt, quần tối |
| `luat-su` | áo vest xám, quần tối, cầm hồ sơ (đạo cụ `books`) |
| `nhan-vien-van-phong` | sơ mi, cà vạt, cặp da |
| `bac-si` | áo blouse, ống nghe |
| `dieu-duong` | đồng phục xanh ngọc, mũ, khẩu trang |
| `can-bo-kiem-dich` | áo xanh nhạt, mũ kê-pi, thẻ đeo, bìa hồ sơ |
| `cong-nhan` | mũ bảo hộ, áo phản quang |
| `hanh-khach` | áo khoác, mũ lưỡi trai, khẩu trang, vali |

Quy tắc:
- Kính thuộc về nhân vật, không thuộc skin: ai đeo kính vẫn đeo kính khi đổi skin, ai không đeo thì không có.
- Skin chốt ở cổng casting (`casting.json` mỗi vai ghi `character` và `skin`) rồi khóa như nhân vật. Vai cần đổi đồ theo cảnh thì ghi `skin_theo_canh` (mã cảnh -> mã skin, `goc` là bộ đồ khóa) ở casting; chỉ đổi ở ranh giới hai cảnh, không đổi giữa một cảnh, và không thêm bộ đồ nào chưa chốt.
- Cách dựng khi đổi skin theo cảnh: thêm cùng nhân vật nhiều lần, mỗi bản một skin, với khung hiện `from`/`until` (giây) nối tiếp nhau ở đầu cảnh đổi đồ. `python3 SKILL/scripts/vai.py kiem-casting casting.json` in sẵn các dòng này. Hai bản của cùng nhân vật trùng khung hiện thì thư viện báo lỗi.

```js
const hung = C.add("anh-duc", { x: 540, y: 1700, scale: 1.4, skin: "sep", until: T.s03 });   // s01-s02: đi làm
const hungNha = C.add("anh-duc", { x: 540, y: 1700, scale: 1.4, from: T.s03 });               // s03 trở đi: bộ đồ gốc
C.at(T.s03 + 0.2, () => hungNha.say(2));   // hẹn giờ cho đúng bản đang hiện
```
- Skin chỉ dùng được mẫu đồ đã có trong rig (xem `SUPPORTED` trong `assets/chibi/src/rig.ts`). Muốn đồ mới (vest dài, đồng phục cảnh sát...) phải vẽ vào cả hai rig rồi mới thêm skin; thư viện báo lỗi "chua ve ban chibi" nếu thiếu.
- Skin chỉ là đồ mặc; cử chỉ riêng theo vai (`ra-lenh`, `kham`...) nằm ở tính cách. Thêm skin: viết vào `LIST` trong `skins.ts`, build lại (xem `assets/lineart/src/BUILD.md`).
- Cặp nhân vật và skin không bị giới hạn theo giới, nhưng đồ mặc kiểu `aodai`, `baba`, `dress` chưa có skin nên chỉ có trong bộ đồ khóa của nhân vật.

## Tính cách (cách diễn)

Tính cách là cách một vai diễn, tách khỏi người đóng và đồ mặc: một giám đốc hiền và một giám đốc khó tính có thể cùng nhân vật, cùng skin `sep`. Thư viện ở `SKILL/tinh-cach/` (xem `tinh-cach/README.md`; `python3 SKILL/scripts/vai.py tinh-cach` in bảng). Tính cách chốt ở casting cho cả video, không đổi theo cảnh; cảm xúc từng cảnh do kịch bản quyết, tính cách quyết vai đó thể hiện cảm xúc ra sao.

```js
const hung = C.add("anh-duc", { x: 540, y: 1700, scale: 1.4, skin: "sep", tinhCach: "nghiem-khac" });
C.at(T.s02, () => { hung.noi(2.3); hung.act("ra-lenh", 2.3); });
C.at(T.s03, () => hung.nghe(2));
```

- `cu_chi`: tên tình huống -> cử chỉ có sẵn (`wave`, `point`, `present`, `talk`, `bow`, `nod`). Gọi `nv.act("ra-lenh", 2)` thì ra cử chỉ mà tính cách gán cho "ra-lenh"; tên không có trong tính cách thì chuyển thẳng cho thư viện. `khi-noi`, `khi-nghe` dùng cho `noi()`, `nghe()`.
- `bieu_cam`: tên tình huống -> nét mặt có sẵn (`neutral`, `happy`, `wink`, `deadpan`, `surprised`, `worried`). `binh-thuong` là nét mặt mặc định (sau mỗi biểu cảm có giờ hết thì trở về nét này), `nghe` dùng cho `nghe()`. Gọi `nv.expr("vui", 2)` thì ra nét mặt mà tính cách gán cho "vui".
- `nv.noi(giây)`: nhép miệng theo lời đọc, kèm cử chỉ `khi-noi` nếu tính cách có. Dùng thay `say()` cho vai có tính cách.
- `nv.nghe(giây)`: nét mặt `nghe` và cử chỉ `khi-nghe` (thường là gật đầu) nếu tính cách có.
- Lời thoại và nhịp đọc (`loi_thoai`, `giong`) dành cho biên kịch và `vai.py ap-giong`, không ảnh hưởng hình.
- `tinh-cach.js` do `inject.py` sinh từ thư viện và `PROJECT/tinh-cach/`; ghi `tinhCach` sai mã thì thư viện báo lỗi ngay khi dựng.
