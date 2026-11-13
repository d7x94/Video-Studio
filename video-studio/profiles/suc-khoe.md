# Hồ sơ: Truyền thông giáo dục sức khỏe

**Dùng khi**: khuyến cáo phòng bệnh, nhận biết dấu hiệu bệnh, hướng dẫn hành vi sức khỏe, tiêm chủng, vệ sinh, dinh dưỡng phổ thông.

## Mặc định

| Mục | Giá trị |
|---|---|
| Thời lượng | 60 giây (dao động 45 đến 90) |
| Giọng | Mai Anh (nữ, Bắc, tin tức). Khán giả phía Nam: Thùy Dung |
| Nhạc nền | `nhe-nhang`, studio tự sáng tác bằng `nhac_nen.py`; người dùng muốn thì tắt |
| Tốc độ | 1.0 |
| Kiểm chứng | **Bắt buộc, mức cao** |

## Cấu trúc kịch bản

1. **Mở** (1 cảnh, dưới 5 giây): một câu hỏi, một tình huống quen thuộc, hoặc một con số gây chú ý. Không mở bằng lời chào.
2. **Vấn đề** (1 đến 2 cảnh): bệnh là gì, lây thế nào, ai có nguy cơ. Chỉ những gì cần để hiểu hành động phía sau.
3. **Hành động** (2 đến 4 cảnh): việc cụ thể người xem làm được ngay, mỗi cảnh một việc, động từ ở đầu câu ("Úp ngược...", "Rửa tay...").
4. **Khi nào cần đi khám** (1 cảnh, nếu liên quan): dấu hiệu cảnh báo, viết rõ ràng, không gây hoảng sợ.
5. **Kết** (1 cảnh): nhắc lại thông điệp chính trong một câu, kèm dòng nguồn trên hình.

## Giọng văn

Gần gũi, rõ ràng, tôn trọng. Nói "bạn", "gia đình bạn". Câu ngắn. Khẳng định tích cực ("Hãy đậy kín lu") hơn là cấm đoán. Không dọa nạt, không dùng hình ảnh hay từ ngữ gây sợ hãi để thuyết phục.

## Kiểm chứng

Mọi khuyến cáo, triệu chứng, số liệu phải đối chiếu. Nguồn ưu tiên theo thứ tự:
1. Văn bản, hướng dẫn chuyên môn của Bộ Y tế và các cục chuyên môn trực thuộc
2. Hướng dẫn của Tổ chức Y tế Thế giới (WHO)
3. Viện Pasteur, Viện Vệ sinh dịch tễ, Trung tâm Kiểm soát bệnh tật tỉnh/thành
4. Tài liệu người dùng cung cấp (ghi rõ)

Khi nguồn trong nước và quốc tế khác nhau, theo hướng dẫn của Bộ Y tế và ghi chú khác biệt cho người duyệt. Số liệu dịch tễ phải ghi thời điểm ("năm 2025", "tính đến tháng 10").

Không đưa lời khuyên dùng thuốc cụ thể (tên thuốc, liều) trừ khi người dùng yêu cầu và có hướng dẫn chính thức đi kèm. Luôn có thông điệp "đến cơ sở y tế" khi nói về triệu chứng.

## Hình

- Bảng màu mặc định của template (xanh đậm, chữ trắng, nhấn vàng) hợp chủ đề này. Màu đỏ (`--danger`) chỉ cho dấu hiệu cảnh báo.
- Biểu tượng SVG đơn giản, nét đều: giọt nước, muỗi, bàn tay, nhiệt kế, ngôi nhà.
- Chuyển động điềm tĩnh: hiện dần, trượt nhẹ 40 đến 60px, 0,5 đến 0,7 giây. Không rung, không nhấp nháy.
- Dòng nguồn ở cảnh cuối dùng lớp `.source`, ví dụ "Nguồn: Bộ Y tế".
- **Nhân vật 3D** (khi brief yêu cầu): cán bộ y tế dùng `Doctor_*`, người dân dùng `Casual_*` hoặc `OldClassy_*`; phòng `nha` cho chủ đề hộ gia đình, `phong-kham` cho khám chữa bệnh, `cua-khau` cho kiểm dịch. Cho nhân vật làm mẫu bằng hoạt ảnh có sẵn khi hợp (`PickUp` nhặt đồ, `Walk_Carry` bê đồ) thay vì chỉ đứng nói; thao tác thư viện không có (úp xô, đậy nắp) thì thể hiện bằng chữ và biểu tượng ở lớp chữ.

## Metadata

- Lời kêu gọi: chia sẻ cho người thân, hoặc hành động cụ thể ("Kiểm tra nhà bạn ngay hôm nay").
- Mô tả YouTube liệt kê nguồn có link.
- Hashtag gợi ý: tên bệnh, #phongbenh, #suckhoe.
- Trước khi đăng: nhắc người dùng xem lại nếu video đăng dưới danh nghĩa cơ quan thì cần quy trình duyệt nội bộ của cơ quan.

## Cần tránh

Hình ảnh máu, kim tiêm cận cảnh, người bệnh đau đớn. Kỳ thị nhóm người hay địa phương. Khẳng định tuyệt đối ("chắc chắn không mắc bệnh").
