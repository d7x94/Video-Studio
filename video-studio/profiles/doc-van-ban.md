# Hồ sơ: Đọc văn bản (truyện, tài liệu) thành âm thanh

**Dùng khi**: người dùng gửi một văn bản (PDF, .docx, .txt, .md hoặc dán) và nhờ đọc thành tiếng. Trước mắt dùng để đọc truyện cho chính người dùng nghe, không đăng tải. Không viết nội dung mới, không dựng hình. Quy trình chi tiết: `references/che-do-doc.md`.

## Mặc định

| Mục | Giá trị |
|---|---|
| Giọng | Hải Đăng (quyết định 2026-11-14); người dùng chọn giọng khác thì ghi `voice` vào brief. Giọng kể chuyện và đọc truyện xem `references/giong-doc.md` |
| Tốc độ | 1.0 (0.85 đến 1.15) |
| Đầu ra | MP3 mỗi chương một file (`ra/NNNN-ten-chuong.mp3`), danh sách phát `ra/danh-sach.m3u`. Phụ đề `.srt` và video chỉ khi người dùng yêu cầu |
| Kiểm chứng | Không có bảng kiểm chứng: studio không viết nội dung. Quy tắc thay thế: đọc nguyên văn, không thêm, không bớt, không tóm tắt |
| Nhạc nền | Không |

## Hỏi một lần ở bước 0

1. File văn bản (hoặc dán nội dung).
2. Chương nào đọc (một khoảng như `1-3`, hoặc cả quyển; quyển dài thì nên làm theo đợt).
3. Giọng (không nói thì Hải Đăng) và tốc độ.
4. Cần phụ đề `.srt` hoặc video không (mặc định không).

## Cổng duyệt (nhẹ, không chặn)

Mặc định không dừng. Studio tách chương, làm sạch, đọc thử một đoạn ngắn đầu chương đầu tiên, rồi đọc cả khoảng chương. Cuối job báo `cach-doc.md` (đã bỏ gì, chỗ chưa chắc cách đọc) để người dùng sửa bằng `cach-doc.txt`. Chỉ dừng hỏi khi bảng chỗ chưa chắc có hơn 10 mục khác nhau ở khoảng chương cần đọc, hoặc khi văn bản có nhiều nhân vật thoại và người dùng đã nói muốn nhiều giọng.

## Cần tránh

Đổi lời văn khi chuẩn hóa; bỏ đoạn mà không ghi vào `cach-doc.md`; đọc cả quyển nghìn chương trong một lần chạy; ghi nguồn hay tải truyện từ web (workspace không tải được, người dùng gửi file).

## Metadata

Không cần. Truyện là văn bản người dùng cung cấp để nghe riêng; studio không đăng tải. Credits ghi công cụ (VieNeu).
