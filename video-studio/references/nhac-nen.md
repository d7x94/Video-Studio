# Nhạc nền do studio tự sáng tác

`scripts/nhac_nen.py` sáng tác một bản nhạc nền dài đúng bằng video rồi ghép vào video, tự giảm âm khi có lời đọc. Mọi âm thanh tổng hợp bằng code (sóng sin, hòa âm, arpeggio, giai điệu chuông, bass, trống nhẹ, vang), không dùng file nhạc, mẫu âm thanh hay thư viện nhạc bên ngoài. Vì vậy quy tắc "không dùng nhạc của người khác" vẫn giữ nguyên: studio không nhận file nhạc người dùng gửi, không tìm nhạc trên mạng.

Kiểm chứng ngày 2026-11-13: sáng tác đủ 5 kiểu, ghép vào video chibi mẫu hai khổ, `check_output.py` ĐẠT; chạy lại nhiều lần ra cùng một file tiếng (không chồng nhạc).

## Kiểu nhạc

| Kiểu | Thang, nhịp | Lớp nhạc | Hồ sơ mặc định |
|---|---|---|---|
| `vui` | trưởng, 112 bpm | hòa âm, arpeggio móc dây, bass, trống nhẹ, lắc, chuông | kiến thức, review |
| `nhe-nhang` | trưởng, 84 bpm, hợp âm bảy | hòa âm dày, arpeggio chậm, chuông | sức khỏe |
| `nghiem-tuc` | thứ, 92 bpm | hòa âm, arpeggio nhanh nhỏ, bass móc, trống phách đầu | thủ tục |
| `hoi-hop` | thứ, 72 bpm | hòa âm trầm, tiếng tích tắc, chuông thưa | kể chuyện cảnh báo |
| `ke-chuyen` | trưởng, 76 bpm | hộp nhạc (chuông) rõ, hòa âm, arpeggio | kể chuyện |

Mỗi bản có ô nhịp đầu chỉ hòa âm (vào nhẹ), giai điệu lặp kiểu A A' B A, ô nhịp cuối về hợp âm chủ, vào dần 1,5 giây và tắt dần 2,5 giây cuối. Giọng (khóa) và vòng hòa âm chọn theo `seed`; mặc định `seed` lấy từ tên thư mục dự án, nên mỗi video một bản khác nhau nhưng chạy lại vẫn ra đúng bản đó. Muốn bản khác cùng kiểu: thêm `--seed <số>`.

## Lệnh

```bash
python3 SKILL/scripts/nhac_nen.py <PROJECT> --kieu nhe-nhang --chi-tao        # chỉ sáng tác: audio/nhac-nen.wav và .mp3 để nghe thử
python3 SKILL/scripts/nhac_nen.py <PROJECT> --kieu nhe-nhang renders/preview_portrait.mp4   # ghép vào bản nháp
python3 SKILL/scripts/nhac_nen.py <PROJECT> --kieu nhe-nhang                  # ghép vào mọi renders/final_*.mp4
python3 SKILL/scripts/nhac_nen.py <PROJECT> --bo                              # gỡ nhạc, trả lại bản không nhạc
```

- Bản không nhạc được giữ ở `renders/<tên>.khong-nhac.mp4`; lệnh luôn ghép từ bản này, nên chạy lại bao nhiêu lần cũng không chồng nhạc. `package.py` chỉ lấy `final_*.mp4`, không lấy bản không nhạc.
- Render lại một khổ thì chạy lại lệnh ghép cho khổ đó (bản render mới chưa có nhạc).
- Mức nhạc: `--muc` (mặc định -10 dB). Đo trên video mẫu với giọng Mai Anh (giọng khoảng -20 dB): nhạc khoảng -26 dB ở khoảng lặng giữa hai cảnh, khoảng -36 dB khi đang đọc. Người dùng thấy nhạc to quá thì giảm `--muc` (ví dụ -14).
- Thời gian: sáng tác 24 giây nhạc mất khoảng 2 giây; ghép không render lại hình (chép nguyên luồng hình).

## Quy trình

- Bước 0: ghi vào `brief.md` mục "Nhạc nền: <kiểu> theo hồ sơ" hoặc "không" nếu người dùng không muốn.
- Bước 6: sau khi render bản nháp, ghép nhạc vào bản nháp rồi mới `check_output.py` và gửi người dùng; hỏi thêm về nhạc (giữ, đổi kiểu, nhỏ hơn, bỏ).
- Bước 7: sau khi render bản cuối mỗi khổ, ghép nhạc rồi mới `check_output.py`.
- `credits.md`: "Nhạc nền: do studio tự sáng tác bằng code (tổng hợp âm thanh), không dùng nhạc hay mẫu âm thanh bên ngoài".
