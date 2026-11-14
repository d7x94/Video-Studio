# Thư viện hồ sơ vai

Mỗi vai đã casting ở một video được lưu thành một file `<ma-vai>.json` để video sau dùng lại đúng người, đúng tên, đúng giọng, đúng bộ đồ. File bắt đầu bằng `_` (như `_mau.json`) là mẫu, không được tính.

**Nhân vật và vai khác nhau.** Nhân vật là diễn viên trong dàn đã khóa (mặt, dáng, màu da, tóc, kính, giọng). Vai là người mà diễn viên đóng trong phim: họ tên, chức vụ, tuổi, tính cách, các bộ đồ (skin) và các cử chỉ hay dùng. Một nhân vật có thể đóng nhiều vai ở các video khác nhau, nhưng trong một video chỉ đóng một vai, và luôn giữ một giọng.

## Các trường

| Trường | Bắt buộc | Ý nghĩa |
|---|---|---|
| `id` | có | Mã vai, chữ thường không dấu, gạch nối; trùng tên file |
| `ho_ten` | có | Họ tên trong phim. Tên hư cấu, không dùng tên người thật hay đồng nghiệp |
| `cach_goi` | | Cách gọi trong lời thoại ("Giám đốc Hùng", "chị Thu") |
| `chuc_vu` | có | Chức vụ, nghề |
| `noi_lam` | | Nơi làm việc (hư cấu) |
| `tuoi` | | Số tuổi; phải hợp dáng của nhân vật: trẻ em 3 đến 15, người lớn 18 đến 59, cao tuổi 60 trở lên |
| `tinh_cach`, `xung_ho` | | Giúp biên kịch viết thoại đúng giọng vai |
| `nhan_vat` | có với line-art, chibi | Mã nhân vật trong dàn (`references/nhan-vat-line-art.md`) |
| `dien_vien_3d` | có với 3D | Mã diễn viên trong `assets/sim3d/cast.json` |
| `giong` | | Giọng VieNeu (`references/giong-doc.md`). Hai hồ sơ cùng nhân vật phải cùng giọng |
| `kieu_hinh` | có | Các kiểu hình vai đã đóng: `line-art`, `chibi`, `3d` |
| `trang_phuc` | có | Tên bộ đồ -> mã skin. Phải có `mac-dinh`. Mã `goc` là bộ đồ khóa của nhân vật trong dàn |
| `cu_chi` | | Cử chỉ hay dùng: cử chỉ có sẵn (`wave`, `point`, `present`, `talk`, `bow`, `nod`), tên cử chỉ riêng của skin trong `trang_phuc`; với chibi thêm `sweep` và động tác sinh hoạt (`danh-rang`, `an`...) |
| `da_dong` | | Các video đã đóng: `{ "video": slug, "ngay": "YYYY-MM-DD" }` |
| `ghi_chu` | | Ghi chú tự do |

Hồ sơ vai chỉ chọn trong những gì rig đã có: bộ đồ là skin trong `skins.ts`, cử chỉ là cử chỉ có sẵn. Muốn đồ hay động tác mới thì làm vào rig trước (cả line-art và chibi), rồi mới ghi vào hồ sơ.

## Lệnh

```bash
python3 SKILL/scripts/vai.py danh-sach --kieu chibi          # bảng hồ sơ vai dùng được cho kiểu hình
python3 SKILL/scripts/vai.py kiem                            # kiểm cả thư viện
python3 SKILL/scripts/vai.py kiem-casting PROJECT/casting.json  # kiểm casting, in khung hiện khi đổi skin theo cảnh
python3 SKILL/scripts/vai.py xuat PROJECT/casting.json PROJECT/output/vai --video <slug> --kieu chibi
```

## Thêm hoặc sửa hồ sơ

Workspace của mỗi chat không giữ lại, nên hồ sơ mới chỉ được lưu khi thêm vào repo `d7x94/Video-Studio` (thư mục `video-studio/vai/`), chạy `vai.py kiem` không lỗi, gộp vào `main` rồi tải zip skill mới lên claude.ai. Sửa hồ sơ đã có (đổi nhân vật, giọng, bộ đồ) cũng qua repo; video đã làm không bị ảnh hưởng.
