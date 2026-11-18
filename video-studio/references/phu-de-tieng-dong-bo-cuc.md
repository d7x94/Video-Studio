# Phụ đề từng từ, tiếng động, kiểm bố cục, nhịp hình

Ba công cụ thêm ở 1.8.0 và các quy tắc nhịp hình đi kèm. Tất cả chạy trên workspace, không tải gì từ mạng.

## Phụ đề từng từ

Phụ đề hiện cả dòng như cũ, nhưng từ nào đang được đọc thì đổi màu đúng lúc tiếng đó bắt đầu (kiểu TikTok/Shorts). Mốc mỗi dòng phụ đề cũng lấy theo tiếng thật thay vì chia theo số ký tự, nên file `.srt` khớp lời hơn.

```bash
python3 SKILL/scripts/inject.py timeline.json build/portrait/index.html --tung-tu
python3 SKILL/scripts/inject.py timeline.json build/landscape/index.html --no-burn --tung-tu   # chỉ để .srt khớp tiếng
```

- Mặc định bật cho khổ dọc (TikTok, Shorts). Khổ ngang đốt phụ đề vào hình thì bật nếu brief muốn; khổ ngang `--no-burn` vẫn nên thêm `--tung-tu` để `.srt` khớp tiếng hơn.
- Màu từ đang đọc: biến CSS `--cap-hi` (mặc định `#ffd166`, vàng). Đổi trong `:root` của composition khi bảng màu hồ sơ cần màu khác; giữ tương phản với viền chữ phụ đề.
- `inject.py` tự gọi `moc_tu.py` và tự tính lại khi `timeline.json` mới hơn `moc-tu.json` (sau khi đọc lại một cảnh). Xem mốc từng tiếng: `python3 SKILL/scripts/moc_tu.py <PROJECT>`.
- Cách ước lượng: tìm các khoảng lặng trong file tiếng từng cảnh, ghép chỗ ngắt cụm (dấu phẩy, dấu chấm) với khoảng lặng, rồi chia thời gian có tiếng trong cụm cho từng tiếng theo độ dài chữ và dịch ranh giới về chỗ âm lượng thấp nhất. Không dùng mô hình nhận dạng giọng nói.
- Đo trên video mẫu 3 cảnh (giọng Mai Anh, 30 tiếng so được): lệch so với mốc từ của Whisper small trung bình 0,08 giây, trung vị 0,065 giây, lớn nhất 0,33 giây. Mốc của Whisper cũng là ước lượng, nên con số này chỉ cho biết độ lớn sai số.
- `subtitle` khác `narration` (số, tên riêng viết phiên âm): số cụm hai bên bằng nhau thì mỗi cụm phụ đề nhận đúng khoảng thời gian của cụm lời đọc tương ứng; khác nhau thì chia đều cả cảnh. Vì vậy khi viết `subtitle`, giữ nguyên dấu phẩy và dấu chấm như `narration`.
- Mốc không khớp (số từ phụ đề khác số mốc) thì `inject.py` in `[CANH BAO]` và cảnh đó quay về cách chia theo ký tự, không đổi màu từng từ.

## Tiếng động

`scripts/tieng_dong.py` tổng hợp 15 loại tiếng bằng numpy (không dùng mẫu âm thanh) và đặt theo mốc cảnh hoặc theo một từ trong lời đọc. Danh sách: `python3 SKILL/scripts/tieng_dong.py --danh-sach`. Nghe thử tất cả: `--nghe-thu /tmp/nghe.wav`.

| Loại | Dùng khi |
|---|---|
| `vut` | chuyển cảnh, vật bay vào |
| `bop` | chữ, biểu tượng hiện ra |
| `cham` | bấm nút, dấu tích |
| `ding` | nhấn một ý |
| `dung` / `sai` | việc nên làm / cần tránh |
| `chuong` | thông báo, nhắc lịch |
| `ting` | sạch sẽ, sáng bóng |
| `go-cua`, `giay` | gõ cửa; lật hồ sơ, giấy tờ |
| `buoc-chan`, `vo-tay`, `nuoc`, `tim-dap`, `dong-ho` | tiếng kéo dài, ghi thêm `dai` (giây) |

Biên kịch hoặc điều phối ghi vào trường `sfx` của cảnh trong `scenes.json`:

```json
"sfx": [
  {"loai": "vut", "luc": -0.2},
  {"loai": "nuoc", "tu": "làm ướt", "dai": 1.2, "muc": -3},
  {"loai": "ting", "tu": "xà phòng"}
]
```

- `luc`: giây tính từ đầu hình cảnh (cùng mốc `T.<id>` của tween). `tu`: tiếng vang đúng lúc cụm từ đó được đọc trong cảnh (không phân biệt dấu, hoa thường). Có cả hai thì lấy mốc của từ rồi cộng `luc`.
- `muc` (dB cộng thêm), `pan` (-1 trái, 1 phải) tùy chọn.
- Chạy sau `tts.py` và trước `nhac_nen.py`: `python3 SKILL/scripts/tieng_dong.py .` ghi `audio/tieng-dong.wav`; `nhac_nen.py` tự trộn file này (không giảm theo lời đọc, như tiếng bút). Brief không nhạc: `nhac_nen.py . --chi-hieu-ung`.
- Mặc định đỉnh -16 dBFS (`--muc`). Ít thôi: 1 đến 2 tiếng mỗi cảnh, đặt vào hành động chính, không rải mọi chuyển động. Video sức khỏe, thủ tục giữ tiếng nhẹ (`bop`, `cham`, `ding`, `dung`); `sai` chỉ cho việc cần tránh.
- Tiếng mới tổng hợp, chưa được nghe thử bằng tai trên video thật: nghe bản nháp, chỉnh `muc` từng tiếng trước khi giao. Ghi `credits.md`: tiếng động do studio tự tổng hợp bằng code.

## Kiểm bố cục

```bash
python3 SKILL/scripts/kiem_bo_cuc.py build/portrait --json qa/bo-cuc-portrait.json
```

Mở composition trong Chrome không giao diện, tua tới 3 mốc mỗi cảnh và giữa mỗi dòng phụ đề, đo bằng số (không nhìn ảnh). Chạy sau `inject.py`, mất vài giây.

| Mã | Mức | Nghĩa |
|---|---|---|
| `CHU-RA-NGOAI` | LỖI | chữ cảnh tràn ra ngoài khung |
| `CHU-DE-PHU-DE` | LỖI | chữ cảnh đè lên phụ đề |
| `DAU-BI-CAT` | LỖI | mép trên hoặc dưới khung cắt đầu nhân vật |
| `DAU-BI-CAT-MEP`, `NGUOI-BI-CAT-MEP` | cảnh báo | mép trái, phải cắt đầu hoặc thân; lúc đi vào, đi ra thì bỏ qua, đứng yên mà bị cắt thì sửa |
| `CHU-CHONG-CHU` | cảnh báo | hai khối chữ chồng nhau |
| `CHU-VUNG-NUT` | cảnh báo | khổ dọc: chữ nằm ở 300 px đáy hoặc cột nút bên phải, nơi giao diện TikTok che |
| `PHU-DE-CHE-MAT`, `CHU-CHE-MAT` | cảnh báo | phụ đề hoặc chữ che hơn 25% đầu nhân vật |

Đo được nhân vật line-art và chibi (thư viện có gắn `data-nhan-vat`, `data-dau` từ 1.8.0). Nhân vật 3D vẽ lên canvas nên chưa đo được nhân vật, chỉ đo chữ và phụ đề. Thoát mã 1 khi có LỖI.

## Nhịp hình (rút từ kinh nghiệm làm phim ngắn hoạt hình)

Áp cho biên kịch khi viết `visual` và cho dựng cảnh khi viết tween:

- **Một hành động, một từ**: mỗi cảnh có một hành động chính, rơi đúng vào một từ được đọc. Ghi từ đó trong `visual` (ví dụ: "khi đọc *xà phòng*: bọt nở ra"). Dựng cảnh lấy mốc bằng `python3 SKILL/scripts/moc_tu.py <PROJECT> --tim "xà phòng"` rồi viết `T.s02 + (mốc - visual_start)`; tiếng động cùng hành động thì ghi `"tu": "xà phòng"` trong `sfx`.
- **Ít cảnh cắt**: khoảng 3 đến 4 lần đổi khung hình lớn mỗi 30 giây; trong một cảnh cho vật chuyển động, đừng cắt liên tục. Cắt quá dày nhìn giật.
- **Một lần đứng hình có chủ ý**: video 30 đến 60 giây nên có một khoảnh khắc dừng (0,6 đến 1 giây) trước ý chính hoặc câu kết, khớp với `pause_before` dài của cảnh đó. Ghi `data-hold` cho phần tử đứng yên để `hyperframes check` không báo `dead_stretch`.
- **Khổ dọc hẹp**: khổ 9:16 chỉ rộng khoảng một nửa khổ ngang, nên xếp nhân vật và vật theo chiều sâu hoặc chiều dọc, đừng dàn hàng ngang như khổ 16:9.
- **Không bật tắt trong một khung**: đèn, vầng sáng, lớp tối, biểu tượng hiện ra mờ dần trong 0,3 đến 0,5 giây (10 đến 15 khung), không đổi đột ngột trong một khung hình (trừ cú cắt cảnh).
- **Đi bộ không trượt**: nhân vật line-art, chibi đi bằng `walkTo` (bước chân tự khớp quãng đường); đừng tween `x` của cả nhân vật, sẽ trông như trượt trên sàn.
