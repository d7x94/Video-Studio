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
1. Cảnh quay (video và ảnh), đã làm mờ hoặc chọn đoạn không lộ thông tin cá nhân (địa chỉ, tên, số điện thoại, mã vận đơn). Xin danh sách đoạn thùng giao hàng không có nhãn, hoặc làm mờ vùng phiếu bằng `scripts/lam_mo_vung_trang.py` (chế độ video có sẵn trong `SKILL.md`).
2. Giọng đọc và xưng hô.
3. Số liệu hoặc điều không được nói (ví dụ tổng số lượng).
4. Chi tiết sản phẩm khó hiểu cần người dùng xác nhận (cơ cấu, công dụng của bộ phận lạ). Ghi vào `brief.md` và `kiem-chung.md`, nếu không QA sẽ coi là khẳng định không nguồn.
5. Hàng nào là hàng mua, hàng nào là quà tặng kèm.
6. Có tài trợ hay không. Mặc định là không; không đọc câu "không tài trợ" trong video.

## Giọng

Người mua đang mở hộp và nhìn tận tay, không phải nhân viên cửa hàng đọc thông số. Dùng "mình thấy", "mình chưa rõ", "mình chưa thử". Không khuyên mua, không dùng từ khen tuyệt đối. Người dùng có thể yêu cầu giảm đại từ xưng hô: viết câu không chủ ngữ ("Hàng đã về rồi", "Mở nắp, đầu thỏi là..."), chỉ giữ "mình" khi thật cần. Mở đầu mẫu: "Hàng về rồi. Vỏ thùng chỉ nhăn nhẹ ở góc, không bị móp méo." Mô tả tình trạng thùng, vật chèn, hộp, dây là quan sát từ khung hình, không phải kiểm bằng tay: ghi rõ trong `kiem-chung.md` để người quay xác nhận. Mỗi cảnh có số liệu nên có một quan sát hoặc cảm nhận đi kèm.

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

## Ảnh tĩnh cuối video

Đoạn ảnh chụp sản phẩm, mặt sau, mặt bên, đáy: mỗi ảnh một ý ngắn về thương hiệu, công dụng theo nhãn, cách dùng theo nhãn, nơi sản xuất. Thông tin thương hiệu lấy từ bài báo hoặc trang chính thức đã mở đọc, ghi vào `kiem-chung.md`; trang chính thức có thể đã bán phiên bản mới khác sản phẩm trong video, không lấy thông số từ đó. Tìm trang sản phẩm theo đúng mã SKU in trên tem phụ (ví dụ AV10175bt2MBKV2), vì cùng hãng có nhiều mã gần giống (khác chất liệu, chuẩn, độ dài); trang bán của mã khác không dùng làm căn cứ. Tin về chủ sở hữu, năm thành lập của hãng là nguồn hạng 2 nếu chưa mở được trang giới thiệu chính thức: ghi rõ và để người dùng quyết. Nhãn chứng nhận có mã QR (ví dụ Ultra High Speed HDMI) kiểm được bằng ứng dụng của tổ chức cấp nhãn; chỉ nói được là "quét để kiểm tra", không nói cáp đã đạt khi chưa quét. Nhãn tiếng Hàn đọc từ khung hình gốc và ghi là "theo nhãn".

## Chữ ghi trên video

Dòng nguồn trên hình ở cảnh dùng thông tin ngoài là bắt buộc (xem phần phân loại thông tin). Làm bằng `scripts/chu_may_chu.py` (chữ hiện từng chữ như máy đánh chữ, dòng nguồn nhỏ bên dưới); chữ chính chỉ là từ khóa ngắn của ý đang đọc, không chép cả câu. Chữ quan sát (thùng, vật chèn, hộp, dây) không cần nguồn; chữ lấy từ tem hoặc hình trên hộp ghi "Theo tem phụ trên hộp" hay "Theo hình trên hộp".

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
- Làm mờ phiếu giao hàng: xem lại khung mỗi 0,1 giây cả đoạn có phiếu (kể cả lúc bóc phiếu và mảnh giấy rách trong tay); chỉ báo OK của script chưa đủ.
- Video có nhạc nền: mức -13 dB cho video lời thưa, chạy lại nhạc nền sau mỗi lần ghép lại (xem `scripts/dung_lai_video_co_san.sh`).
- Duyệt từng cảnh bằng render nháp trước khi render toàn bộ.

## Metadata

- Mô tả: trải nghiệm cá nhân, tách rõ "lời nhà sản xuất ghi" và "điều mình quan sát", nêu điều chưa thử. Dòng không tài trợ đặt ở mô tả, không đọc trong video.
- Nguồn tham khảo kèm ngày kiểm. Không ghi số liệu cấm. Không khẳng định công dụng chưa kiểm chứng.
- Hashtag: #mohop, loại sản phẩm, tên sản phẩm (không dấu).

## Cần tránh

Quảng cáo, kêu gọi mua; khẳng định công dụng hay chứng nhận chỉ có trên bao bì; lộ thông tin cá nhân; số liệu người dùng cấm; dùng chung nhân vật, nhạc, logo của người khác.
