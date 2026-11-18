# Cổng casting: chốt nhân vật (bước 3b)

Chi tiết bước 3b của `SKILL.md`, chỉ dùng khi video có nhân vật line-art, chibi hoặc 3D. Đọc hết file này trước khi bắt đầu casting.

Như casting diễn viên trước khi quay: chốt ai đóng vai nào, trông thế nào, giọng gì, mặc gì ở từng cảnh, rồi mới lồng tiếng và dựng hình. Đổi nhân vật sau bước này nghĩa là lồng tiếng và dựng lại, nên dừng ở đây. Video kiểu `2d` thì bỏ qua bước này.

**Hồ sơ vai có sẵn** (thư mục `SKILL/vai/`, xem `vai/README.md`): vai có `vai_id` trong "Danh sách vai" thì dùng đúng nhân vật, giọng, bộ đồ và tính cách trong hồ sơ, không chọn ứng viên khác; bảng casting ghi "dùng lại hồ sơ <vai_id>" để người dùng xác nhận. Người dùng muốn đổi người hay giọng của vai đã có hồ sơ thì làm vai mới (mã khác) hoặc sửa hồ sơ qua repo, không đổi lén trong video.

**Đổi skin theo cảnh** (line-art, chibi): nhân vật không bao giờ đổi, nhưng một vai được mặc nhiều bộ đồ khác nhau ở các cảnh khác nhau nếu kịch bản có lý do (sáng đi làm, tối về nhà). Mọi bộ đồ phải chốt ở cổng này, ghi trong `casting.json` bằng `skin_theo_canh` (mã cảnh -> mã skin, ghi đủ mọi cảnh của vai; `goc` là bộ đồ khóa của nhân vật). Chỉ đổi ở ranh giới hai cảnh, không đổi giữa một cảnh. Ảnh thử vai đặt mỗi bộ đồ của vai một người đứng cạnh nhau. Nhân vật 3D chưa đổi skin theo cảnh được.

**Tính cách** (line-art, chibi): mỗi vai chốt một tính cách cho cả video (không đổi theo cảnh), cùng lúc với nhân vật và skin. Bảng casting có thêm cột tính cách; tính cách mới thiết kế cho video này thì gửi kèm bảng `cu_chi`, `bieu_cam` để người dùng duyệt. Ảnh thử vai chibi đặt mỗi người nét mặt `binh-thuong` của tính cách. Tính cách dùng với 3D chỉ có tác dụng ở lời thoại và nhịp đọc.

**Line-art** (dàn nhân vật đã khóa trong `references/nhan-vat-line-art.md`, không tải gì):
1. Mỗi vai trong "Danh sách vai" chọn 1 đến 2 nhân vật trong dàn hợp tuổi, giới, nghề, và một skin hợp vai (sếp, luật sư, bác sĩ...; xem mục "Skin theo vai" cuối `references/nhan-vat-line-art.md`; ghi `skin` trong `casting.json`); vai có thoại chọn giọng VieNeu như mục 2 bên dưới. Không có nhân vật hợp vai thì dùng người gần nhất và báo người dùng.
2. Thử vai bằng ảnh: `bash SKILL/scripts/new_project.sh ~/studio/<slug>/casting portrait lineart`, viết khối `SETUP` đặt các ứng viên đứng thành hàng (cách nhau khoảng 260 px ở `scale` 3,5, cùng quay phải), lớp chữ ghi mã vai dưới chân từng người, rồi `hyperframes snapshot --at 1 --no-end -o snaps`. Nghe thử giọng như mục 4 bên dưới.
3. Gửi bảng casting (vai, nhân vật, giọng), ảnh và giọng thử. Dừng lại chờ. Chốt: `casting.json` mỗi vai ghi `role`, `character` (mã trong dàn), `voice`, `scenes`, `skin` hoặc `skin_theo_canh`, `tinh_cach` (mã tính cách), `vai_id` nếu dùng lại hồ sơ, và `ho_so` (họ tên, chức vụ, tuổi, tính cách, xưng hô, cử chỉ hay dùng, theo các trường của `vai/README.md`) cho vai mới; và `casting.md`. Chạy `python3 SKILL/scripts/vai.py kiem-casting ~/studio/<slug>/casting.json` đến khi không còn lỗi. Từ đây không đổi nhân vật, giọng, tính cách hay bộ đồ của từng cảnh.

**Chibi** (cùng dàn nhân vật đã khóa, xem `references/nhan-vat-chibi.md`, không tải gì): làm như line-art ở trên, chỉ khác lệnh thử vai: `bash SKILL/scripts/new_project.sh ~/studio/<slug>/casting portrait chibi`, đặt các ứng viên đứng thành hàng (cách nhau khoảng 300 px ở `scale` 1,4, cùng quay phải, nhiều hơn 3 người thì xếp nhiều hàng), cho mỗi người một biểu cảm (`expr`) để người dùng thấy nét mặt. Chốt `casting.json` và `casting.md` như line-art.

**3D** (các mục 1 đến 6 dưới đây):

1. **Danh sách vai**: lấy từ mục "Danh sách vai" của `kich-ban.md` đã duyệt. Người dẫn chuyện không cần casting hình, chỉ cần giọng (mặc định theo brief).
2. **Chọn ứng viên**, 1 đến 2 phương án mỗi vai. Ưu tiên dàn diễn viên người Việt đã khóa (xem `python3 SKILL/scripts/get_characters.py --cast`, bảng ở `references/nhan-vat-3d.md`): dùng nguyên cấu hình của diễn viên, không tự đổi. Chỉ khi không diễn viên nào hợp vai mới chọn từ danh mục gốc (`get_characters.py --list`) và tự định cấu hình, rồi báo người dùng. Dàn chỉ có người lớn; vai trẻ em dùng người lớn thu nhỏ (`height` 1,1 đến 1,2, tỉ lệ đầu thân vẫn là người lớn nên chỉ hợp vai phụ). Mỗi ứng viên ghi đủ: model (`.gltf`), `height`, `skin` (`S.SKIN.sang`, `vua`, `ngam`, `nau`), `colors` trang phục (theo tên vật liệu trong `ch.materials`), và giọng VieNeu nếu vai có thoại (theo `references/giong-doc.md`). Ràng buộc: các vai trong cùng video phải phân biệt được bằng mắt (khác model hoặc khác hẳn màu áo); một nhân vật một giọng suốt video; hai vai có thoại không dùng chung giọng, và không trùng giọng người dẫn chuyện.
3. **Thử vai bằng ảnh, không render video**:
   ```bash
   bash SKILL/scripts/new_project.sh ~/studio/<slug>/casting portrait 3d
   python3 SKILL/scripts/get_characters.py ~/studio/<slug>/casting/build/portrait --cast <mã diễn viên ứng viên>
   # hoặc, với model ngoài dàn: ... get_characters.py <thư mục> <các model ứng viên>
   ```
   Tự viết khối `SETUP` đặt các ứng viên đứng thành hàng giữa phòng của brief, cách nhau khoảng 1 mét, quay về khán giả (góc khoảng 0,45), mỗi người đúng cấu hình đã định; khối `DIRECTION` chỉ cho `Idle`; lớp chữ ghi mã vai và mã ứng viên dưới chân từng người. Rồi chụp: `cd ~/studio/<slug>/casting/build/portrait && hyperframes snapshot --at 1,2 --no-end -o snaps`. Nhiều hơn 4 ứng viên thì chia nhiều ảnh. Xem ảnh trước khi gửi: nhân vật bị che, sai màu da, hai vai trông giống nhau thì sửa luôn.
4. **Nghe thử giọng**: với các vai có thoại, viết `casting/scenes.json` mỗi vai một cảnh, lời là một câu thoại thật của vai trong kịch bản, `voice` là giọng ứng viên; chạy `python3 SKILL/scripts/tts.py casting/scenes.json casting`.
5. **Gửi người dùng**: bảng casting (vai, ứng viên, model, màu da, trang phục, giọng), ảnh thử vai và file giọng thử. Dừng lại chờ. Người dùng chọn, đổi hoặc yêu cầu phương án khác bao nhiêu vòng cũng được.
6. **Chốt**: ghi `casting.json` (mỗi vai: `role`, `model`, `height`, `skin`, `colors`, `voice`, `scenes`) và `casting.md` (bảng dễ đọc kèm đường dẫn ảnh thử vai). Từ đây dàn nhân vật bị khóa: các bước sau dùng đúng cấu hình trong `casting.json`, không tự ý đổi model, màu hay giọng. Cảnh có thoại của một vai trong `scenes.json` phải mang `voice` của vai đó theo `casting.json`. Người dùng muốn đổi vai sau khi chốt thì quay lại bước này và báo trước những gì phải làm lại (lồng tiếng các cảnh của vai đó, dựng lại cảnh có vai đó).
