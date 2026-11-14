# Thư viện tính cách (cách diễn)

Mỗi vai có ba lớp: **nhân vật** (diễn viên trong dàn đã khóa: mặt, dáng, giọng), **skin** (trang phục) và **tính cách** (cách diễn). Tính cách dùng lại được cho nhiều vai, nhiều nhân vật: "nghiêm khắc" dùng được cho giám đốc, trưởng phòng hay ông bố.

Mỗi tính cách một file `<ma>.json`. Tính cách mới của một video để ở `PROJECT/tinh-cach/<ma>.json`, không trùng mã với thư viện; ở bước 8 được xuất cùng hồ sơ vai để thêm vào repo. File bắt đầu bằng `_` không được tính.

## Các trường

| Trường | Bắt buộc | Ý nghĩa |
|---|---|---|
| `id` | có | Mã, chữ thường không dấu, gạch nối; trùng tên file |
| `ten`, `mo_ta` | `ten` có | Tên và mô tả ngắn, để chọn ở casting |
| `loi_thoai` | | Cho biên kịch: `xung_ho`, `cau` (câu dài hay ngắn, kiểu câu), `giong_dieu`, `cau_cua_mieng` (danh sách) |
| `giong` | | Nhịp đọc: `speed` (0,85 đến 1,15), `pause_before` (0 đến 1,5). `vai.py ap-giong` đặt vào các cảnh của vai chưa có giá trị riêng. Giọng (người đọc) thuộc về nhân vật, không thuộc tính cách |
| `cu_chi` | có | Tên tình huống -> cử chỉ có sẵn (`wave`, `point`, `present`, `talk`, `bow`, `nod`). Khóa đặc biệt: `khi-noi`, `khi-nghe` |
| `bieu_cam` | | Tên tình huống -> nét mặt có sẵn (`neutral`, `happy`, `wink`, `deadpan`, `surprised`, `worried`). Chỉ chibi. Khóa đặc biệt: `binh-thuong` (nét mặt mặc định), `nghe` |
| `dong_tac` | | Động tác sinh hoạt hay làm (clip chibi tay chân que: `danh-rang`, `nghe-dien-thoai`...); gợi ý cho biên kịch và dựng cảnh |

Tính cách chỉ chọn trong cử chỉ và nét mặt rig đã có. Muốn động tác hay nét mặt mới thì làm vào rig trước (cả line-art và chibi nếu cần), rồi mới ghi vào tính cách.

## Có sẵn

| Mã | Dùng cho |
|---|---|
| `nghiem-khac` | Người có chức vụ, nói ngắn, ít cười (`ra-lenh`, `thuyet-phuc`, `tra-loi`) |
| `than-thien` | Cởi mở, hay cười, lắng nghe |
| `soi-noi` | Năng động, nói nhanh, hay vẫy tay |
| `tan-tam` | Bác sĩ, điều dưỡng, cán bộ: điềm tĩnh, hướng dẫn từng bước (`kham`, `giai-thich`, `huong-dan`, `kiem-tra`) |
| `chuyen-nghiep` | Luật sư, văn phòng: rành mạch (`trinh-ho-so`, `phan-tich`, `chi-dieu-khoan`) |
| `hien-hau` | Người cao tuổi: chậm rãi, ân cần |
| `hon-nhien` | Trẻ em: vui, tò mò |
| `lo-lang` | Người dân, hành khách đang lo, yên tâm dần khi được hướng dẫn |

## Lệnh

```bash
python3 SKILL/scripts/vai.py tinh-cach [PROJECT]     # bảng tính cách (thư viện + của dự án)
python3 SKILL/scripts/vai.py kiem                    # kiểm thư viện hồ sơ vai và tính cách
python3 SKILL/scripts/vai.py ap-giong PROJECT/casting.json PROJECT/scenes.json
```
