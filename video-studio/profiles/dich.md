# Hồ sơ: Dịch video (phụ đề, thuyết minh)

**Dùng khi**: người dùng gửi video nói tiếng nước ngoài (trước mắt tiếng Anh, tiếng Trung) và nhờ dịch sang tiếng Việt. Không dựng hình mới. Quy trình chi tiết: `references/che-do-dich.md`.

## Mặc định

| Mục | Giá trị |
|---|---|
| Khổ hình | Giữ nguyên video gốc |
| Đầu ra | Phụ đề cứng tiếng Việt và `phu-de-vi.srt` (thuyết minh chưa có script ở bản này) |
| Ngôn ngữ gốc | Tự nhận dạng; người dùng biết trước thì ghi rõ |
| Mô hình chép lời | Whisper `medium`, bật VAD; kiểm chéo bằng FireRedASR2 với tiếng Trung, tiếng Anh (`chep_loi_firered.py`); đọc chữ trên hình (`chu_tren_hinh.py`) |
| Tiếng gốc | Giữ nguyên khi chỉ làm phụ đề |
| Nhạc nền | Không thêm |
| Kiểm chứng | **Mức theo nội dung**: mặc định kiểm dịch trung thực với lời gốc, ghi "theo lời người nói" khi có số liệu; nội dung sức khỏe, thủ tục thì số liệu, khuyến cáo vẫn kiểm chứng nguồn ngoài như `suc-khoe.md`, `thu-tuc.md` |

## Hỏi một lần ở bước 0

1. File video (không nhận link: workspace không tải được YouTube).
2. Chỉ phụ đề, hay cần thuyết minh. Thuyết minh thì tiếng gốc giữ nhỏ lại, thay hẳn hay tắt.
3. Phụ đề một ngôn ngữ hay song ngữ.
4. Ngôn ngữ gốc nếu đã biết; video có mấy người nói.
5. Video có phụ đề cứng sẵn không (nếu có thì làm mờ dải đáy hoặc đặt phụ đề dịch lên trên).

## Giọng văn bản dịch

Dịch ý cho người Việt đọc tự nhiên, không dịch từng chữ. Giữ giọng người nói (vlog thân mật, bài giảng trang trọng). Xưng hô theo quan hệ người nói. Không thêm ý, không bình luận, không làm mềm lời gốc. Câu chưa chắc nghĩa thì đánh dấu và hỏi ở cổng duyệt, không đoán.

## Phân vai

Agent chép lời (haiku) chỉ chạy script và báo lại; dịch (sonnet); kiểm dịch độc lập (sonnet, opus khi nội dung sức khỏe, thủ tục); trọng tài chỉ cho câu người dịch và người kiểm dịch không thống nhất. Chi tiết: `references/che-do-dich.md`, mục "Phân vai".

## Cổng duyệt

1. Bản chép lời gốc: một bảng `dich/duyet-chep.md` (`phu_de_dich.py duyet-chep`) gộp cờ Whisper, chỗ `KHÁC` của FireRed, chỗ khác chữ trên hình, lời trong khoảng trống; hỏi người nói. Áp lựa chọn bằng `sua`, `them`, `nguoi`, rồi gộp mảnh câu (`goi-y-gop`, `gop`) trước khi dịch.
2. Bản dịch: bảng `dich/ban-dich.md` (`phu_de_dich.py bang`) kèm tóm tắt lượt kiểm dịch `dich/kiem-dich.md`.
3. Bảng khung kiểm phụ đề trước khi giao.

## Metadata

Tiêu đề và mô tả tiếng Việt. Không ghi nguồn video gốc khi người dùng đã nói tự chịu trách nhiệm về quyền sử dụng; nhắc người dùng điều này một lần ở bước 0. Nhãn nội dung AI do người dùng quyết.

## Cần tránh

Dịch khi bản chép gốc tin cậy thấp mà chưa báo người dùng; sửa lời gốc theo ý mình mà không hỏi; giữ câu Whisper bịa; phụ đề đè lên chữ sẵn có của video.
