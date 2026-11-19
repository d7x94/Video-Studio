# Hồ sơ: Chi tiêu, "tiền bay" (đi chợ, mua sắm theo hóa đơn)

**Dùng khi**: người dùng có cảnh quay hàng vừa mua (mở túi, ảnh từng món) và hóa đơn thật, muốn video cho thấy tiền "bay" dần vào máy tính tiền và tổng cuối cùng. Không có lời đọc. Mở hộp một sản phẩm có lời đọc thì dùng `unbox.md`.

Công cụ riêng: `scripts/may_tinh_tien.py`, quy trình ở `references/che-do-tien-bay.md`. Không đi qua bước 2 đến 4 và bước 5 của `SKILL.md` (không kịch bản, không lồng tiếng, không HyperFrames); vẫn giữ cổng duyệt bản xem trước và các quy tắc chung.

## Mặc định

| Mục | Giá trị |
|---|---|
| Khổ hình | 9:16 (TikTok) |
| Thời lượng | khoảng 5 giây mỗi món (2 giây mở bao bì, 3 giây ảnh sản phẩm) cộng 3 giây mở đầu và 9,5 giây kết; 11 món ra khoảng 70 giây |
| Lời đọc | Không có |
| Nhạc nền | `vui`, mức -16 dB; kèm tiếng máy tính tiền, máy in biên lai do studio tự tổng hợp |
| Tiếng gốc của video | Bỏ (video ghép dùng luồng tiếng im, chỉ nghe nhạc và tiếng hiệu ứng) |
| Kiểm chứng | **Mức thấp, nhưng số tiền phải khớp hóa đơn thật** (xem dưới) |

## Đầu vào cần có

- Video quay hàng (khổ dọc, gửi bằng "Tệp", không gửi bằng "Ảnh" để không bị nén).
- Hóa đơn: ảnh chụp màn hình app hoặc phiếu giấy. Hóa đơn dài thì chụp nhiều tấm cuộn nối nhau, mỗi tấm trùng ít nhất một dòng với tấm kế tiếp để chắc không thiếu món. Có tấm hiện tổng đơn thì chụp thêm: đó là cách duy nhất đối chiếu được tổng.
- Ngày nhận hàng muốn hiện ở mở đầu (tùy chọn).
- Món nào đóng gói nhiều đơn vị (ống 4 trái, hộp 10 quả) mà muốn hiện giá mỗi đơn vị thì cho số đơn vị tổng (vd 2 ống x 4 trái = 8).

## Cấu trúc video

1. **Mở đầu** (khoảng 3 giây): cảnh tổng quát túi hàng, ô tiền hiện 0đ; có ngày thì hiện nhãn ngày. Không hook bằng câu hỏi hay lời kêu gọi trên hình.
2. **Mỗi món** (khoảng 5 giây): cảnh tay lấy món ra khỏi túi (khoảng 2 giây), rồi ảnh sản phẩm; thẻ giá (tên, số lượng, thành tiền) bật lên, bay vào ô tiền, số nhảy kèm tiếng máy tính tiền.
3. **Món đắt nhất đặt cuối** để thành cao trào: thẻ viền đỏ có nhãn, ô tiền rung kèm tiếng trầm; có `chia` thì hiện giá mỗi đơn vị (tính bằng code, làm tròn 100đ, kèm dấu "≈").
4. **Kết**: biên lai in ra từng dòng, dòng tổng cộng, thanh chia nhóm theo phần trăm.

## Kiểm chứng (bắt buộc)

- Giá từng dòng chép từ hóa đơn của người dùng; `kiem-chung.md` ghi mỗi dòng lấy từ tấm ảnh nào.
- Tổng do code cộng, không gõ tay. Có `tong_hoa_don` trong `tien-bay.json` thì `may_tinh_tien.py kiem` chặn khi lệch. Không có thì báo cảnh báo và nói rõ với người dùng rằng tổng chưa đối chiếu được với app.
- Số suy ra (giá mỗi đơn vị, phần trăm theo nhóm) là phép tính từ số của hóa đơn; không thêm số liệu từ nguồn khác (không so sánh với giá siêu thị khác, không nêu mức "đắt" hay "rẻ").
- Hóa đơn thiếu dòng (ảnh bắt đầu giữa danh sách, tấm cuộn không trùng dòng) thì hỏi lại trước khi dựng.

## Hình

- Cảnh quay của người dùng là hình chính; thẻ giá, ô tiền, biên lai là đồ họa tự vẽ bằng code.
- Mã đơn hay thông tin cá nhân lộ trên hình (số ghi tay trên túi, nhãn giao hàng, tên người nhận) thì hỏi người dùng có làm mờ không. Logo siêu thị lộ ngẫu nhiên trên túi: hỏi giữ hay làm mờ.
- Không dùng logo, nhạc, hình của bên thứ ba ngoài chính sản phẩm.

## Metadata

- Chú thích TikTok: một câu nêu số món và tổng tiền, câu hỏi kéo bình luận đặt ở đây (không đặt trên hình), 3 đến 5 hashtag.
- Không ghi tên siêu thị, không khen hay chê thương hiệu.
- `credits.md`: cảnh quay của chủ video; đồ họa, nhạc nền, tiếng hiệu ứng do studio tự tạo bằng code; font hệ thống (Inter, SIL OFL 1.1 và Apache 2.0, theo gói `fonts-inter` của Debian; không đóng gói trong skill); nguồn giá là hóa đơn của chủ video, ghi ngày.

## Cần tránh

Giá không có trong hóa đơn. Nhận xét "đắt", "rẻ", "tiết kiệm" trên hình. Khuyên mua hay quảng cáo. Lộ mã đơn, địa chỉ, số điện thoại. Dùng nhạc hay tiếng của người khác.
