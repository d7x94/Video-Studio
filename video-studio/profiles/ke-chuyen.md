# Hồ sơ: Kể chuyện, hoạt hình đồ họa

**Dùng khi**: câu chuyện có nhân vật, truyện ngụ ngôn, kể lại sự kiện, tình huống giả định, hoạt hình giải thích bằng nhân vật.

## Mặc định

| Mục | Giá trị |
|---|---|
| Thời lượng | 90 giây (dao động 60 đến 180) |
| Giọng | Thiện Minh (nam, Bắc, kể chuyện) hoặc Ngọc Linh (nữ, Bắc, kể chuyện). Phía Nam: Thái Sơn, Thục Đoan |
| Nhạc nền | `ke-chuyen` (chuyện hồi hộp, cảnh báo: `hoi-hop`), studio tự sáng tác bằng `nhac_nen.py`; người dùng muốn thì tắt |
| Tốc độ | 0.95 |
| Kiểm chứng | **Mức thấp** với chuyện hư cấu; **mức vừa** với chuyện có thật hay sự kiện lịch sử |

## Cấu trúc kịch bản

1. **Bối cảnh** (1 cảnh): ai, ở đâu, khi nào, trong vài câu.
2. **Biến cố** (1 đến 2 cảnh): điều gì thay đổi, nhân vật muốn gì.
3. **Diễn biến** (2 đến 4 cảnh): thử thách, lựa chọn.
4. **Cao trào và kết** (1 đến 2 cảnh).
5. **Thông điệp** (1 cảnh, nếu có): một câu, không giảng giải.

Chuyện dùng để truyền thông (ví dụ chuyện một gia đình phòng bệnh) thì nội dung khuyến cáo trong chuyện vẫn theo quy tắc kiểm chứng của hồ sơ sức khỏe.

## Giọng văn

Văn kể, có nhịp, hình ảnh cụ thể. Lời thoại nhân vật được. Mỗi cảnh chỉ một giọng, nên khi nhân vật nói thì tách lời của nhân vật đó thành cảnh riêng và ghi `"voice": "<tên giọng>"` trong cảnh đó của `scenes.json`; `tts.py` tự dùng giọng riêng của cảnh. Giữ một nhân vật một giọng suốt video.

## Kiểm chứng

Chuyện hư cấu: chỉ kiểm chi tiết đời thực được nhắc tới (tên địa danh, sự kiện). Chuyện có thật hay lịch sử: kiểm mốc thời gian, tên người, số liệu như hồ sơ kiến thức. Không gán lời nói hư cấu cho người thật.

## Hình

- Hồ sơ này hợp nhất với **nhân vật 3D** (xem `references/nhan-vat-3d.md`): nhân vật chibi có sẵn hoạt ảnh đi, ngồi, nhặt đồ, ăn mừng. Nếu brief không chọn 3D thì dùng nhân vật SVG như dưới đây.
- Nhân vật vẽ bằng SVG dạng phẳng, tối giản (hình khối, không chi tiết khuôn mặt phức tạp), mỗi nhân vật một màu nhận diện, giữ nhất quán suốt video.
- Không vẽ nhân vật có bản quyền hay nhân vật dễ nhận ra của phim, truyện, thương hiệu.
- Chuyển động kể chuyện: nhân vật vào cảnh, cảnh nền trượt chậm (parallax nhẹ), chuyển cảnh mờ dần.
- Bảng màu ấm hơn: có thể đổi `--bg` sang nâu đất, xanh đêm, tùy không khí chuyện.

## Metadata

- Tiêu đề gợi tò mò nhưng không đánh lừa.
- Hashtag: chủ đề chuyện, #kechuyen, #hoathinh.

## Cần tránh

Bạo lực, nội dung không hợp trẻ em (trừ khi brief nói rõ khán giả người lớn). Nhân vật dựa trên người thật có thể nhận ra.
