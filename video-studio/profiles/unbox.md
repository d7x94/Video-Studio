# Hồ sơ: Unbox (mở hộp từ góc nhìn người tiêu dùng)

**Dùng khi**: người dùng quay cảnh mở hộp sản phẩm họ tự mua và muốn một video khách quan, không quảng cáo. Nếu là đánh giá sau thời gian dùng thì dùng `review.md`.

## Mặc định

| Mục | Giá trị |
|---|---|
| Khổ hình | 9:16 (hỏi thêm nếu cần 16:9) |
| Thời lượng | 180 đến 240 giây, theo độ dài cảnh quay của người dùng |
| Giọng | Chọn ở cổng duyệt 1 theo xưng hô: "mình" hợp giọng miền Bắc (Hải Đăng, Trúc Ly); "tui" cần giọng miền Nam |
| Nhạc nền | `nhe-nhang`, mức -16 dB; người dùng muốn thì tắt |
| Tốc độ | 1.0 |
| Kiểu hình | 2D trên cảnh quay thật của người dùng (clip cắt theo cảnh) |
| Kiểm chứng | **Mức vừa**: thông tin ngoài phải có nguồn khách quan; chữ trên bao bì lấy từ cảnh quay của người dùng |

## Đầu vào cần có

Hỏi một lần ở bước 0, gom thành một tin:
1. Cảnh quay (video và ảnh), đã làm mờ hoặc chọn đoạn không lộ thông tin cá nhân (địa chỉ, tên, số điện thoại, mã vận đơn). Xin danh sách đoạn thùng giao hàng không có nhãn.
2. Giọng đọc và xưng hô.
3. Số liệu hoặc điều không được nói (ví dụ tổng số lượng).
4. Chi tiết sản phẩm khó hiểu cần người dùng xác nhận (cơ cấu, công dụng của bộ phận lạ). Ghi vào `brief.md` và `kiem-chung.md`, nếu không QA sẽ coi là khẳng định không nguồn.
5. Hàng nào là hàng mua, hàng nào là quà tặng kèm.
6. Có tài trợ hay không. Mặc định là không; không đọc câu "không tài trợ" trong video.

## Giọng

Người mua đang mở hộp và nhìn tận tay, không phải nhân viên cửa hàng đọc thông số. Dùng "mình thấy", "mình chưa rõ", "mình chưa thử". Không khuyên mua, không dùng từ khen tuyệt đối. Mỗi cảnh có số liệu nên có một quan sát hoặc cảm nhận đi kèm.

## Phân loại thông tin (bắt buộc)

Mỗi câu thuộc đúng một loại, và lời đọc nói rõ loại đó:
- **Lời ghi trên bao bì**: "Hộp ghi...", "đây là lời ghi trên bao bì, mình không biết thật hư ra sao". Mọi tuyên bố như an toàn thực phẩm, kháng khuẩn, FDA, bền, chịu nhiệt thuộc loại này, trừ khi có nguồn ngoài.
- **Điều mình quan sát**: kích thước đo bằng mắt, cảm giác, tình trạng hộp. Không dùng từ chưa đo như "to nhất", "dày nhất"; dùng điều đã biết ("cỡ túi lớn nhất").
- **Thông tin ngoài có nguồn**: chỉ từ cơ quan quản lý, tiêu chuẩn, tài liệu kỹ thuật. Có dòng nguồn trên hình ở cảnh dùng nó; quy chuẩn trích dẫn phải kiểm còn hiệu lực ở trang chính thống, nếu chỉ suy ra từ văn bản khác thì ghi rõ.

Dịch nhãn đúng nghĩa (ví dụ "Translucent" là trong mờ, không phải trong suốt).

## Cấu trúc kịch bản

1. **Thùng giao hàng**: chỉ đoạn sạch nhãn vận đơn; nói ngắn hoặc không nói.
2. **Mở thùng, bên trong**: có chống sốc hay không, hộp có hư hại không.
3. **Lấy hết ra**: đếm hộp, phân loại, hàng tặng kèm. Không nói tổng số nếu người dùng cấm.
4. **Từng loại hộp**: mặt trước (cỡ, kích thước), mặt sau (công năng, hướng dẫn), nhà sản xuất, hạn dùng, chất liệu, cảnh báo.
5. **Phụ kiện, quà tặng**: mở, cho thấy bên trong, thông số.
6. **Điểm cần lưu ý**: chữ nhỏ, ngôn ngữ nhãn, lời trên bao bì.
7. **Điều chưa thử và tóm tắt bộ hàng**. Nói rõ chưa thử độ bền, độ kín, chịu nhiệt; không có cảnh quay thì nói thẳng, không dựng giả.

## Hình

- Mọi cảnh dùng cảnh quay thật. Quay ngang: nền mờ, khung giữa; quay dọc: cắt phủ. Zoom 0,22 khi mô tả hình có "ZOOM", mặc định 0,08. Tốc độ phát 0,5 đến 1,5, thiếu thì giữ khung hình cuối.
- Chữ nhỏ hoặc biểu tượng nhỏ trên bao bì (như dấu FDA): cắt ảnh tĩnh phóng to từ khung rõ nhất.
- Nền chữ: dải gradient đặt ở nền phần tử cảnh (không dùng z-index âm), bóng chữ nhẹ.
- Khung hình lộ thông tin cá nhân: không dùng, hoặc làm mờ.
- Không dùng logo, nhạc, hình của bên thứ ba ngoài chính sản phẩm.

## Soát trước khi gọi QA

- Từ tuyệt đối chưa đo; nhãn dịch lệch; lời nói lệch hình đang chiếu.
- Phụ đề khớp từng câu lời đọc; phụ đề dài không đè chữ trên bao bì hay dòng nguồn.
- Số liệu cấm không còn ở `scenes.json`, `phu-de.srt`, `kich-ban.md`, `kiem-chung.md`, `loi-doc-*.json`, metadata (gói giao kèm các file này).
- Gom mọi sửa chữ trước khi render toàn bộ để chỉ render một lần.
- Duyệt từng cảnh bằng render nháp trước khi render toàn bộ.

## Metadata

- Mô tả: trải nghiệm cá nhân, tách rõ "lời nhà sản xuất ghi" và "điều mình quan sát", nêu điều chưa thử. Dòng không tài trợ đặt ở mô tả, không đọc trong video.
- Nguồn tham khảo kèm ngày kiểm. Không ghi số liệu cấm. Không khẳng định công dụng chưa kiểm chứng.
- Hashtag: #mohop, loại sản phẩm, tên sản phẩm (không dấu).

## Cần tránh

Quảng cáo, kêu gọi mua; khẳng định công dụng hay chứng nhận chỉ có trên bao bì; lộ thông tin cá nhân; số liệu người dùng cấm; dùng chung nhân vật, nhạc, logo của người khác.
