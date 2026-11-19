# Chế độ "tiền bay" (video chi tiêu theo hóa đơn)

Dùng cùng hồ sơ `profiles/chi-tieu.md`. Không có lời đọc nên bỏ bước 2 đến 5 của `SKILL.md` (kịch bản, kiểm chứng câu chữ, lồng tiếng, HyperFrames); giữ cổng duyệt bản xem trước (bước 6), hoàn thiện (bước 7) và giao gói (bước 8). `scripts/may_tinh_tien.py` làm cả hình và tiếng hiệu ứng.

## Cách người dùng khai báo

Người dùng không phải học lệnh. Mẫu dán vào đầu tin nhắn, kèm file:

```
/video-studio kiểu "tiền bay đi chợ", TikTok 9:16
- Video hình: <file quay dọc, gửi bằng Tệp>
- Âm thanh: bỏ tiếng gốc, chỉ nhạc nền và tiếng máy tính tiền
- Hóa đơn: ảnh chụp màn hình app, <số tấm> tấm (có tấm tổng đơn thì gửi kèm)
- Ngày hiện ở mở đầu: <dd/mm/yyyy>
- Mỗi món: 2 giây cảnh mở bao bì, rồi ảnh sản phẩm và thẻ giá ghi số lượng
- Món đắt nhất đặt cuối làm cao trào
- Kết: biên lai in ra, chia nhóm (vd đồ ăn, đồ dùng)
- Không hook, không câu hỏi trên hình (câu kéo bình luận để ở caption)
```

Điều phối viên đọc mẫu này, điền `brief.md` và `tien-bay.json`. Dòng nào người dùng bỏ trống thì dùng mặc định của `profiles/chi-tieu.md` và nói rõ đã chọn gì.

## Quy trình

1. **Nhận việc**: chuẩn hóa brief; hóa đơn nhiều tấm thì ghép các dòng, loại dòng trùng ở chỗ nối, báo người dùng danh sách món và tổng đã cộng để xác nhận đủ món (không có tấm tổng đơn thì nói rõ tổng chưa đối chiếu được). Ghi `kiem-chung.md`: mỗi món một dòng gồm tên, số lượng, thành tiền và tấm ảnh hóa đơn chứa dòng đó; dòng cuối ghi tổng đã cộng và đã khớp `tong_hoa_don` hay chưa đối chiếu được. Bỏ bước 2 nhưng không bỏ việc kiểm chứng: số tiền là số liệu duy nhất trên hình nên phải có nguồn.
2. **Xem video gốc**: xuất bảng khung mỗi giây để tìm đoạn mở bao bì của từng món và đoạn ảnh sản phẩm sạch (sản phẩm đứng yên giữa khung, không có tay). Gợi ý lệnh: `ffmpeg -i video -vf "fps=1,scale=200:-1,drawtext=...:text='%{eif\:t\:d}',tile=10x14" -frames:v 1 qa/bang.jpg`. Ghi mốc `tu` và `dai` vào `tien-bay.json`.
3. **`may_tinh_tien.py PROJECT kiem`** rồi **`khung`**: kiểm cấu hình, xem `qa/tien-bay/khung_*.png` (lớp phủ đặt trên một khung tạm, chỉ để xem bố cục; cảnh thật ở bước 5).
4. **`may_tinh_tien.py PROJECT dung`**: tạo `timeline.json`, `audio/hieu-ung.wav` và `renders/final_portrait.mp4`.
5. **Ghép nhạc và chuẩn âm**: `nhac_nen.py PROJECT --kieu vui --muc -16` (tự trộn `audio/hieu-ung.wav` không giảm theo lời đọc), `chuan_am.sh renders/final_portrait.mp4`, `check_output.py timeline.json renders/final_portrait.mp4 --frames qa/final --chuan-am`.
6. **Xem bảng khung** `qa/final/contact_sheet.png` và xem ít nhất hai khung ở cuối video: chữ trên biên lai có tràn không, con số trên ô tiền khớp tổng không.
7. **Gửi bản xem trước**, chờ duyệt. Sửa một chữ hay mốc thì chạy lại `dung`, rồi nhạc nền, chuẩn âm, kiểm.
8. **Giao gói**: `package.py PROJECT --thumb-at <giây>`. Ảnh bìa: chọn giây sau khi mọi hiệu ứng đã dừng (biên lai in xong, thanh chia nhóm đầy), vì lấy giữa lúc hiệu ứng chạy sẽ ra số dang dở; nên mở ảnh bìa và đối chiếu số trên đó với tổng. `metadata.md` và `credits.md` viết theo hồ sơ. Video không có lời nên không có `phu-de.srt`.

## `tien-bay.json`

```json
{
 "video": "src/v1.mov",
 "ngay": "19/11/2026",
 "tong_hoa_don": 1106800,
 "mo_dau": {"tu": 138.9, "dai": 3.0},
 "ket": {"nen_tu": 140.6, "dai": 9.5, "tieu_de": "HÓA ĐƠN ĐI CHỢ"},
 "mon": [
  {"ten": "Bánh bao Thọ Phát", "so_luong": 2, "gia": 125800, "nhom": "Đồ ăn",
   "mo": {"tu": 16.5, "dai": 1.9}, "anh": {"tu": 148.0, "dai": 3.2}},
  {"ten": "Táo Rockit ống 4 trái", "so_luong": 2, "gia": 296000, "nhom": "Đồ ăn",
   "chia": {"so": 8, "don_vi": "trái"}, "mo": {"tu": 7.0, "dai": 1.9}, "anh": {"tu": 142.0, "dai": 4.0}}
 ]
}
```

| Khóa | Ý nghĩa |
|---|---|
| `video` | video gốc, đường dẫn trong dự án (bắt buộc) |
| `ngay` | nhãn ngày ở mở đầu; bỏ thì không hiện (tùy chọn) |
| `tong_hoa_don` | tổng ghi trên hóa đơn thật; có thì cộng các dòng phải khớp, lệch thì dừng (nên có) |
| `mo_dau`, `ket.nen_tu` | đoạn cảnh mở đầu; giây lấy khung làm nền mờ cho phần kết, phải nằm trong video gốc (bắt buộc) |
| `ket.dai` | tối thiểu 8 giây để biên lai in hết; `ket.tieu_de` đổi tiêu đề biên lai |
| `mon[].gia` | thành tiền của dòng (số nguyên, đồng), không phải đơn giá |
| `mon[].nhom` | nhóm cho thanh phần trăm ở cuối; tối đa 4 nhóm; chỉ một nhóm thì không vẽ thanh |
| `mon[].mo` | đoạn tay mở bao bì (tùy chọn) |
| `mon[].anh` | đoạn ảnh sản phẩm, `dai` tối thiểu 3,0 giây (thẻ giá bay vào ô tiền ở giây 1,9 rồi số nhảy) |
| `mon[].chia` | `{"so": tổng đơn vị, "don_vi": "trái"}`: hiện "≈ giá mỗi đơn vị" ở món đắt nhất; `anh.dai` nên từ 3,4 giây |
| `mon[].ten_bien_lai` | tên rút gọn cho dòng biên lai khi tên dài |
| `dat_nhat_cuoi` | mặc định `true`: món đắt nhất tự chuyển xuống cuối; `false` giữ thứ tự khai báo |
| `mon_dat_nhat` | mặc định `true`: đánh dấu món đắt nhất; `false` tắt nhãn, rung và tiếng trầm |
| `font` | họ font tìm bằng `fc-match` (mặc định Inter, không có thì DejaVu Sans); phải có chữ Việt có dấu |

Tối đa 16 món (biên lai tràn khung). Chữ Việt trong file được chuẩn hóa NFC khi đọc. Mọi `dai` được làm tròn về bội số 1/30 giây (một khung) để hình nền và lớp phủ không lệch nhau; ghi mốc theo bước 0,1 giây thì không bị đổi.

## Số đo và giới hạn

- Render trên workspace 2 nhân: 94 giây cho video 69,8 giây (11 món) và 107 giây cho video 59,7 giây (lần dựng đầu), tức khoảng 1,3 đến 1,8 giây máy cho 1 giây video. Hai số đo, cùng một job, không phải mọi video.
- Đã chạy trọn chuỗi `may_tinh_tien.py dung`, `nhac_nen.py`, `chuan_am.sh`, `check_output.py` trên một job mua sắm khổ dọc 720x1280 (nguồn 3 phút 43 giây, 11 món, 2 nhóm): ĐẠT, -14,8 LUFS, đỉnh -1,0 dBTP, không hình đen hay đứng yên.
- Video nguồn nhỏ hơn 1080x1920 được phóng to khi ghép (phóng nhẹ 5% mỗi cảnh), nên độ nét kém hơn khung gốc. Nguồn 720x1280 vẫn xem được trên điện thoại; chưa thử nguồn thấp hơn.
- Chưa hỗ trợ: tiếng gốc của video (luôn bỏ), khổ 16:9, lời đọc, nhiều ảnh sản phẩm cho một món, tự tìm mốc cảnh trong video gốc (mốc ghi tay ở bước 2).
- Cắt nhiều đoạn từ một file dài: dùng mỗi đoạn một đầu vào `-ss ... -t ... -i` riêng (script đã làm vậy). Thử cắt nhiều đoạn bằng `trim` từ một đầu vào duy nhất làm ffmpeg dừng giữa chừng (`BrokenPipeError`).
- Không có công cụ kiểm tự động chữ trên biên lai có tràn không: xem bằng mắt ở bước 6.
