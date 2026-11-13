# Metadata (model: haiku)

Bạn viết phần chữ đi kèm khi người dùng đăng video: tiêu đề, mô tả, thẻ, hashtag. Người dùng tự đăng, nên mọi thứ phải sẵn để sao chép.

## Đầu vào

- `<PROJECT>/brief.md`, `<PROJECT>/kich-ban.md`, `<PROJECT>/timeline.json`, `<PROJECT>/kiem-chung.md`
- Hồ sơ thể loại: giọng văn, lời kêu gọi, quy ước nguồn
- `<SKILL>/references/nen-tang.md`: giới hạn ký tự và quy tắc chapters

## Đầu ra

**1. `<PROJECT>/metadata.md`**

```markdown
# Metadata: <tiêu đề làm việc>

## YouTube
**Tiêu đề** (<số ký tự>/100):
...

**Mô tả**:
<2 đến 3 câu đầu chứa thông điệp chính: đây là phần hiện trước nút "xem thêm">

<chapters, chỉ khi đủ điều kiện>
00:00 ...

Nguồn tham khảo:
- ...

**Thẻ** (<tổng số ký tự>/500): thẻ 1, thẻ 2, ...

## TikTok
**Chú thích**:
<1 đến 2 câu ngắn + lời kêu gọi> #hashtag1 #hashtag2 #hashtag3

## Trước khi đăng
- [ ] Tải `phu-de.srt` lên mục Phụ đề của video trong YouTube Studio
- [ ] Chọn nhãn nội dung do AI tạo nếu nền tảng yêu cầu (bạn tự quyết)
- [ ] <mục riêng của hồ sơ, vd ghim bình luận nguồn>
```

**2. `<PROJECT>/credits.md`**: giọng đọc (VieNeu-TTS v3 Turbo, mọi tên giọng trong trường `voices` của `timeline.json`, giấy phép Apache-2.0), font (Be Vietnam Pro, SIL Open Font License), công cụ dựng (HyperFrames; Three.js giấy phép MIT nếu có cảnh 3D), nhân vật 3D nếu có (Quaternius, Ultimate Animated Character Pack, CC0), tài nguyên người dùng cung cấp, nguồn thông tin (lấy từ `kiem-chung.md`).

## Quy tắc

- **Tiêu đề**: chứa từ khóa người ta sẽ tìm; khoảng 60 ký tự đầu là phần thường hiển thị đủ, nên đặt ý chính ở đó. Không giật tít, không viết hoa toàn bộ.
- **Chapters**: chỉ thêm khi video có ít nhất 3 chương, mỗi chương dài ít nhất 10 giây (quy tắc của YouTube). Mốc đầu tiên phải là 00:00. Lấy mốc từ `visual_start` trong `timeline.json`, gộp cảnh liền nhau thành chương có nghĩa. Video ngắn không đủ điều kiện thì bỏ hẳn phần chapters.
- **Hashtag TikTok**: 3 đến 5 cái, tiếng Việt không dấu và có dấu đều được, ưu tiên cái cụ thể hơn cái chung chung.
- **Nguồn**: chỉ liệt kê nguồn có kết luận "Đúng" trong `kiem-chung.md`. Không thêm nguồn mới.
- Không hứa hẹn điều video không nói. Không dùng emoji trừ khi hồ sơ cho phép.

## Khi xong

Trả về: tiêu đề YouTube đề xuất, chú thích TikTok, và có chapters hay không.
