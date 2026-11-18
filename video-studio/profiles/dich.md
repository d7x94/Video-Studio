# Hồ sơ: Dịch video (phụ đề, thuyết minh)

**Dùng khi**: người dùng gửi video nói tiếng nước ngoài (trước mắt tiếng Anh, tiếng Trung) và nhờ dịch sang tiếng Việt. Không dựng hình mới. Quy trình chi tiết: `references/che-do-dich.md`.

## Mặc định

| Mục | Giá trị |
|---|---|
| Khổ hình | Giữ nguyên video gốc |
| Đầu ra | Phụ đề cứng tiếng Việt và `phu-de-vi.srt` (thuyết minh chưa có script ở bản này) |
| Ngôn ngữ gốc | Tự nhận dạng; người dùng biết trước thì ghi rõ |
| Mô hình chép lời | Whisper `medium`, bật VAD |
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

## Cổng duyệt

1. Bản chép lời gốc (ngôn ngữ, cờ nghi ngờ, khoảng không có lời).
2. Bản dịch (bảng gốc và dịch).
3. Bảng khung kiểm phụ đề trước khi giao.

## Metadata

Tiêu đề và mô tả tiếng Việt. Không ghi nguồn video gốc khi người dùng đã nói tự chịu trách nhiệm về quyền sử dụng; nhắc người dùng điều này một lần ở bước 0. Nhãn nội dung AI do người dùng quyết.

## Cần tránh

Dịch khi bản chép gốc tin cậy thấp mà chưa báo người dùng; sửa lời gốc theo ý mình mà không hỏi; giữ câu Whisper bịa; phụ đề đè lên chữ sẵn có của video.
