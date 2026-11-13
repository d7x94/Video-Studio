# Viết tween GSAP cho HyperFrames

Quy tắc cho agent dựng cảnh khi viết khối `// ANIMATION` (và tween trong `SETUP`, `DIRECTION` nếu có). Rút từ bộ skill chính thức [greensock/gsap-skills](https://github.com/greensock/gsap-skills) (MIT, giấy phép ở `LICENSE-gsap-skills.txt`, commit `aed9cfd`, các skill `gsap-core`, `gsap-timeline`, `gsap-performance`, `gsap-utils`, `gsap-plugins`), chỉ giữ phần hợp với cách HyperFrames render, đối chiếu tài liệu đi kèm `hyperframes` 0.9.38 (`references/runtimes.md`, `references/motion.md`). Các điểm ghi "đã thử" được chạy lại trên gsap 3.15.0 ngày 2026-11-13.

Khác biệt gốc: gsap-skills viết cho trang web chạy theo thời gian thực. HyperFrames thì **tua timeline tới từng khung hình rồi chụp**, có khi nhảy cóc, có khi lùi lại. Mọi thứ nhìn thấy phải là hàm của thời gian timeline, không phụ thuộc khung trước.

## 1. Bắt buộc (sai thì hình sai hoặc mỗi lần render khác nhau)

- **Mọi tween gắn vào `tl`, đặt bằng vị trí tuyệt đối** `T.<id> + giây` (tham số thứ ba). Không gọi `gsap.to(...)` đứng riêng, không xếp nhịp bằng `delay`, không dùng vị trí tương đối `"+=0.5"`, `"<"`, `">"`: khi lời đọc đổi thời lượng và `inject.py` điền lại `T`, vị trí tương đối kéo lệch cả chuỗi phía sau.
- **Trạng thái đầu đặt trong tween, không đặt trong CSS.** Dùng `fromTo` khi điểm đầu quan trọng. CSS chỉ giữ trạng thái nghỉ (sau khi hiện xong).
- **Hai `from`/`fromTo` trên cùng thuộc tính của cùng phần tử**: tween thứ hai trở đi phải có `immediateRender: false`. Đã thử: `tl.from(o,{x:100},0).from(o,{x:200},2)` để mặc định thì phần tử kết thúc ở `x = 100` thay vì `0`, vì tween thứ hai đọc nhầm điểm cuối. Cách gọn hơn: vào bằng `fromTo`/`from`, ra bằng `to`.
- **Không ngẫu nhiên.** Không `stagger: { from: "random" }`, không `gsap.utils.random(...)`, không giá trị chuỗi `"random(-20, 20)"`: cả ba gọi `Math.random()` bên trong (đã kiểm trong mã gsap 3.15.0). Cần lệch nhịp hay lệch vị trí trông tự nhiên thì dùng hàm theo chỉ số `(i) => [0, 14, -8, 20][i % 4]`, hoặc bộ sinh số có hạt cố định (mulberry32) viết ngay trong khối `ANIMATION`.
- **Lặp hữu hạn.** Không `repeat: -1`. Lặp trong một cảnh: `repeat: Math.max(0, Math.floor(thoiLuong / chuKy) - 1)`, `yoyo: true` nếu cần đi về.
- **Không dùng callback để đổi hình.** `onStart`, `onComplete`, `tl.call(...)` không dùng để thêm lớp, đổi chữ, hiện phần tử. Đã thử: `tl.seek()` mặc định bỏ qua callback, nên tua qua mốc là mất thay đổi. Đổi chữ hay đổi trạng thái thì dùng hai phần tử và tween `opacity` chéo nhau. Ngoại lệ là `onUpdate` có sẵn trong template (tween `state.t` gọi `render(state.t)` để vẽ nhân vật theo thời gian): vẫn đúng vì chỉ phụ thuộc thời gian, không sửa.
- **Không tween `visibility` hay `autoAlpha` trên chính `<section class="clip scene">`**: HyperFrames tự bật tắt cảnh theo `data-start`, `data-duration`; đụng vào thì cảnh trắng. `autoAlpha` dùng cho phần tử con bên trong thì được.
- **Một thuộc tính của một phần tử chỉ có một tween chạy tại một thời điểm.** Hai tween chồng thời gian lên cùng `y` của cùng phần tử cho kết quả phụ thuộc thứ tự tua. Nối tiếp nhau thì được.
- **`<span>` muốn dịch, xoay, phóng phải có `display: inline-block`** (hoặc `block`); transform không áp lên phần tử inline.

## 2. Hiệu năng

Render dùng đường chụp màn hình và GPU giả lập phần mềm (`moi-truong.md`), nên chi phí vẽ mỗi khung lớn hơn trên máy thật.

- Di chuyển bằng `x`, `y`, `xPercent`, `yPercent`, `scale`, `rotation`, `opacity`. Không tween `width`, `height`, `top`, `left`, `margin`, `padding`, `font-size` để tạo chuyển động.
- Thanh tiến độ, thanh biểu đồ lớn dần: `scaleX` (hoặc `scaleY`) với `transformOrigin: "left center"` thay vì tween `width`.
- Cùng một chuyển động cho nhiều phần tử: một tween có `stagger`, không viết nhiều tween lệch giờ bằng tay.
- Không thêm `filter`, `blur`, `backdrop-filter`, `box-shadow` đổi theo thời gian; không đặt `will-change` hàng loạt.

## 3. Nhịp và ease

- Template tạo sẵn `tl` không có `defaults` và không được sửa dòng đó. Muốn dùng chung thời lượng và ease, khai báo hằng ở đầu khối `ANIMATION`, ví dụ `const VAO = { duration: 0.6, ease: "power3.out" };` rồi `tl.from(el, { ...VAO, y: 40, opacity: 0 }, T.s01 + 0.2)`.
- Ease theo vai trò (theo `motion.md` của HyperFrames):
  - Xuất hiện: đuôi dài, `power3.out`, `power4.out`, `expo.out`.
  - Di chuyển hai đầu, đổi khung: `power2.inOut`.
  - Rời đi: tăng tốc, `power2.in`, `power3.in`; dài bằng khoảng 50 đến 60% lúc vào.
  - Nảy nhẹ: `back.out(1.4)`, `elastic.out(1, 0.5)`; chỉ cho vị trí, cỡ. `opacity` và màu không bao giờ nảy.
  - `"none"` (tuyến tính) chỉ cho xoay đều, thanh tiến độ, chuyển động đều có chủ ý.
- Đừng dùng một `power2.out` 0,5 giây cho mọi thứ: nhìn đều đều, giống máy làm.
- Chỉ dùng tên ease có sẵn: `none`, `power1` đến `power4`, `back`, `bounce`, `circ`, `elastic`, `expo`, `sine`, mỗi loại có `.in`, `.out`, `.inOut`. Không tự đặt tên ease.
- Chồng nhịp: phần tử sau bắt đầu khi phần tử trước đi được 30 đến 50%. Nối tiếp hẳn trông cứng, cùng lúc hết trông rẻ.
- Khoảng `stagger`: từng chữ cái cách nhau khoảng một khung hình, từng từ 0,06 đến 0,12 giây, từng mục danh sách 0,04 đến 0,08 giây. Danh sách cần thời gian đọc thì hiện theo lời đọc, không dồn bằng stagger.

## 4. Mẹo cú pháp hay dùng

- Thuộc tính viết camelCase: `backgroundColor`, `transformOrigin`, `strokeDashoffset`.
- Dùng bí danh transform (`x`, `y`, `scale`, `rotation`) thay cho chuỗi `transform`.
- Xoay theo đường ngắn: `rotation: "-170_short"`; ép chiều: `"_cw"`, `"_ccw"`.
- Nhiều phần tử SVG xoay, phóng quanh cùng một điểm: `svgOrigin: "250 100"` (tọa độ của SVG). Không dùng chung với `transformOrigin` trên cùng phần tử.
- Vẽ nét SVG không cần plugin: đặt `stroke-dasharray` bằng độ dài nét rồi tween `strokeDashoffset` từ độ dài về 0. Đo độ dài một lần (`el.getTotalLength()`) trước khi tạo tween, không đo trong `onUpdate`. Kiểu `ve-net` đã có thư viện riêng, dùng `venet.js`.
- Giá trị theo chỉ số: `x: (i) => i * 120` cùng `stagger`.

## 5. Không dùng trong studio

| Phần của gsap-skills | Lý do |
|---|---|
| ScrollTrigger, ScrollSmoother, ScrollTo, Observer, Draggable, Inertia, `quickTo` | Video không cuộn, không chuột, không tương tác |
| `gsap.matchMedia()`, `prefers-reduced-motion` | Khổ hình do template quyết; video đã render không đổi theo thiết bị người xem |
| `gsap-react`, `gsap-frameworks`, `useGSAP` | Studio không dùng React hay framework |
| Plugin `SplitText`, `DrawSVG`, `MorphSVG`, `MotionPath`, `CustomEase` | Có sẵn và miễn phí trong gói `gsap` 3.15.0, nhưng template chỉ nạp `gsap.min.js`. Muốn dùng phải sửa `setup.sh`, `new_project.sh` và template, rồi chạy thử trọn một video (`CLAUDE.md` của repo) trước khi cho agent dùng |
| `gsap.utils.random`, `stagger` ngẫu nhiên | Mỗi lần render ra hình khác (mục 1) |

## 6. Tự kiểm trước khi trả việc

- `grep -nE "repeat: *-1|Math\.random|\"random|from: *\"random\"|delay:" build/<khổ>/index.html` không ra dòng nào trong khối `ANIMATION`.
- `hyperframes check` 0 lỗi (xem `agents/dung-canh.md`).
- Contact sheet bản nháp: xem từng cảnh ở giữa và cuối, phần tử nào sai chỗ thì kiểm lại `immediateRender` và tween chồng nhau.
