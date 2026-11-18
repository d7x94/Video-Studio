# Nhật ký thay đổi

Quy ước số phiên bản `MAJOR.MINOR.PATCH`, ghi ở `video-studio/VERSION` và dòng "Phiên bản skill" trong `video-studio/SKILL.md` (hai nơi phải khớp, CI kiểm tra khi đóng gói). Thêm kiểu hình hoặc tính năng thì tăng MINOR; sửa lỗi thì tăng PATCH; đổi lớn làm hỏng cách dùng cũ thì tăng MAJOR. Mỗi lần gộp PR thay đổi skill: tăng số, sửa hai nơi trên và thêm mục mới ở đầu file này.

## [1.9.0] - 2026-11-18

Vân tay tiếng đọc và khóa kịch bản sau cổng duyệt 1 (ý tưởng từ quy trình phim người que của OpenCreator, xem README mục Ghi công; mã tự viết).

- `scripts/tts.py`: ghi `audio/van-tay.json` (sha256 của lời đọc, giọng, tốc độ, tag bản mô hình, số phiên bản vân tay của từng cảnh). Chạy không có `--only` và không có `--retime` thì chỉ đọc lại cảnh chưa có file, chưa có vân tay hoặc vân tay đã đổi; trước đây luôn đọc lại cả video. Thêm `--lam-lai` (đọc lại tất cả, như hành vi cũ) và `--kiem` (không nạp mô hình, không ghi gì, thoát mã 1 nếu có cảnh thiếu file hoặc lệch vân tay). Với `--only` và `--retime`, cảnh không đọc lại mà vân tay đã lệch được báo `[LECH]`. Mô hình chỉ nạp khi có cảnh cần đọc. Không tính vào vân tay: `pause_before` (chỉ đổi mốc, dùng `--retime`) và độ chính xác int8 hay fp32 (tùy CPU). Dự án làm bằng bản cũ chưa có `van-tay.json` thì lần chạy đầu đọc lại hết.
- Thêm `scripts/khoa_kich_ban.py` (`khoa`, `kiem`, `cap-nhat`, `xem`): ghi `khoa-kich-ban.json` gồm băm `narration`, `subtitle`, `on_screen` (cả dòng nguồn), `claims` từng cảnh lúc người dùng duyệt; `kiem` thoát mã 1 và liệt kê cảnh ĐỔI, THÊM, BỚT; `cap-nhat` nhận cảnh đã đổi vào bản khóa kèm `--ly-do` bắt buộc và lịch sử, và từ chối cảnh có số hoặc `claims` nếu thiếu `--da-kiem-chung`. Không băm `visual`, `pause_before`, `speed`, `voice`, `sfx`. Script chỉ so băm, không đánh giá đúng sai.
- `SKILL.md`: bước 3 (khóa kịch bản), bước 4 (chạy `kiem` trước lồng tiếng, mô tả vân tay), bước 6 và 7 (`khoa_kich_ban.py kiem` và `tts.py --kiem` trước render), phần chạy không giám sát (vẫn khóa, báo kịch bản chưa người duyệt). `agents/qa.md` đọc `lich_su` của file khóa.
- Đã chạy thử: `setup.sh` đầy đủ; `tts.py` với VieNeu thật, giọng Mai Anh, 3 cảnh: lần đầu đọc 3 cảnh (3,8 giây), lần hai không đọc cảnh nào (0,3 giây), `--kiem` khớp (mã 0); đổi lời một cảnh thì `--kiem` thoát mã 1 và chạy lại chỉ đọc đúng cảnh đó, `--kiem` khớp lại; `timeline.json` và `voiceover.wav` đúng như trước. Thử thêm với `synth` giả cho các nhánh `--only` (báo `[LECH]`), `--retime`, `--lam-lai`, đổi `pause_before` (chỉ đổi mốc), xóa `van-tay.json` (đọc lại hết). `khoa_kich_ban.py`: đủ các nhánh khoa, kiem, cap-nhat (kể cả từ chối thiếu `--da-kiem-chung`), thêm và bớt cảnh, khóa trùng, xem. `new_project.sh` khổ dọc 2D, `inject.py`, `hyperframes check` (0 lỗi), `render.sh preview` chạy được trên template chưa có cảnh. Chưa chạy: dựng cảnh thật, `render.sh final`, `check_output.py` ĐẠT trên video có nội dung, nghe thử bằng tai (các phần này không đổi trong bản này).

## [1.8.0] - 2026-11-18

Phụ đề từng từ, tiếng động tự tổng hợp, kiểm bố cục bằng số đo và quy tắc nhịp hình (ý tưởng từ một skill làm phim ngắn hoạt hình bên ngoài; mã và tài liệu tự viết, xem README mục Ghi công).

- Thêm `scripts/moc_tu.py`: ước lượng mốc từng tiếng của lời đọc từ file tiếng từng cảnh (khoảng lặng, chỗ ngắt cụm, chia theo độ dài chữ, dịch ranh giới về chỗ âm lượng thấp nhất), ghi `moc-tu.json`; `--tim "<cụm từ>"` in giây bắt đầu của cụm từ. Không dùng mô hình nhận dạng giọng nói, không tải gì. Phụ đề `subtitle` khác `narration` được ghép theo cụm.
- `scripts/inject.py`: thêm `--tung-tu`. Mốc dòng phụ đề lấy theo tiếng thật thay vì chia theo ký tự, từ đang đọc đổi màu (biến CSS `--cap-hi`, mặc định `#ffd166`) bằng `tl.set` ngay trước dòng đăng ký timeline; chạy lại không có cờ thì gỡ khối đó. Không có `--tung-tu` thì kết quả giống hệt 1.7.0 (đã so từng dòng `index.html` và `phu-de.srt`, chỉ khác ở khối `TUNG-TU` do lần chạy có cờ trước để lại, nay được gỡ).
- Thêm `scripts/tieng_dong.py`: 15 loại tiếng động tổng hợp bằng numpy (vụt, bóp, chạm, đinh, đúng, sai, chuông, ting, gõ cửa, giấy, bước chân, vỗ tay, nước chảy, tim đập, đồng hồ), đặt theo trường `sfx` của cảnh trong `scenes.json` (`luc` theo mốc cảnh hoặc `tu` theo một cụm từ trong lời đọc), ghi `audio/tieng-dong.wav`; `--danh-sach`, `--nghe-thu`.
- `scripts/nhac_nen.py`: trộn cả `audio/hieu-ung.wav` (tiếng bút) và `audio/tieng-dong.wav` khi có; `--chi-hieu-ung` nhận một trong hai file. Không có `tieng-dong.wav` thì hành vi như cũ.
- Thêm `scripts/kiem_bo_cuc.py`: mở composition trong Chrome không giao diện, tua tới 3 mốc mỗi cảnh và giữa mỗi dòng phụ đề, đo chữ tràn khung, chữ đè phụ đề, chữ chồng chữ, chữ ở vùng giao diện TikTok che, đầu và thân nhân vật bị mép khung cắt, phụ đề hoặc chữ che mặt. Thoát mã 1 khi có LỖI.
- Thư viện nhân vật line-art và chibi: gắn thuộc tính `data-nhan-vat` (mã nhân vật) lên nhóm gốc và `data-dau` lên nhóm đầu để `kiem_bo_cuc.py` đo được. Chỉ thêm thuộc tính, không đổi hình; sửa nguồn trong `src/` rồi build lại bằng `tools/build_lineart.sh`, `tools/build_chibi.sh` (cả hai `--check` khớp nguồn trước khi sửa).
- Thêm `references/phu-de-tieng-dong-bo-cuc.md` (cách dùng ba công cụ và mục Nhịp hình: một hành động rơi vào một từ, ít cú cắt, một lần đứng hình có chủ ý, khổ dọc hẹp, không bật tắt trong một khung, đi bộ bằng `walkTo`). `SKILL.md` (bước 4, 5, 6, 7, quy tắc bản quyền, tham khảo), `agents/bien-kich.md` (trường `sfx`, nhịp hình), `agents/dung-canh.md` (`--tung-tu`, `kiem_bo_cuc.py`, nhịp hình), `agents/qa.md` (đọc báo cáo bố cục) trỏ tới tài liệu mới.
- Đã chạy thử: `setup.sh` đầy đủ; video mẫu 3 cảnh 14,2 giây (giọng Mai Anh, có `subtitle` chứa số): `tts.py`, `moc_tu.py`, `new_project.sh` khổ dọc chibi, khổ ngang 2D và khổ dọc line-art, `inject.py --tung-tu` (khổ ngang thêm `--no-burn`), `hyperframes check` 0 lỗi cả ba, `kiem_bo_cuc.py` (0 LỖI; thử thêm một bản cố ý sai: bắt đúng chữ đè phụ đề, chữ tràn khung, mũ và đầu bị mép trên cắt), `render.sh final` khổ dọc chibi 63 giây và khổ ngang 2D 16 giây (khớp số đo cũ), bản nháp line-art 37 giây, `tieng_dong.py` 7 tiếng (có tiếng đặt theo từ), `nhac_nen.py --kieu nhe-nhang` trộn nhạc và tiếng động, `chuan_am.sh`, `check_output.py --chuan-am` ĐẠT cả hai khổ. Xem khung hình: từ đang đọc đổi màu đúng, phụ đề không vỡ viền.
- Đo mốc từng tiếng: so với mốc từ của Whisper small (chỉ dùng để đo, không đưa vào skill) trên 30 tiếng của 2 cảnh đếm từ khớp: lệch trung bình 0,08 giây, trung vị 0,065 giây, lớn nhất 0,33 giây. Mốc của Whisper cũng là ước lượng.
- Chưa kiểm: tiếng động chưa được nghe thử bằng tai (chỉ đo phổ, mức và có mặt trong bản trộn), cần nghe và chỉnh `muc` trên video thật; mốc từng tiếng chưa đo với giọng khác Mai Anh và với câu dài trên 25 tiếng không dấu câu; `kiem_bo_cuc.py` chưa đo được nhân vật 3D (vẽ lên canvas) và chưa thử với kiểu `ve-tay`, `ve-net`; ngưỡng vùng giao diện TikTok (300 px đáy, 120 px phải) lấy theo lề sẵn có của template, chưa đối chiếu lại trên điện thoại.

## [1.7.0] - 2026-11-17

Chuẩn hóa phần cơ học của chế độ lồng tiếng cho video có sẵn (đã lặp lại nhiều lần trong ngày với video khui hàng; lỗi nằm ở cùng mấy chỗ: làm mờ, mốc ảnh tĩnh, câu không chắc). Phần phán đoán (viết lời, chọn nguồn thương hiệu, chọn vùng che) vẫn do người duyệt.

- Thêm `scripts/kiem_khung_lam_mo.py`: bảng khung kiểm làm mờ mỗi 0,1 giây (ảnh gốc, ảnh đã mờ, vùng bị mờ), cảnh báo khi vùng mờ chạm tem đỏ (`DO`), da (`DA`), mờ quá rộng (`MO-LAN`), hoặc vùng trắng còn sắc nét (`CON-TRANG`, cần `--vung-trang`). Chỉ báo điểm nghi ngờ, không thay mắt người.
- Thêm `scripts/so_khang_dinh.py`: sổ khẳng định `khang-dinh.json` (mỗi câu thuộc `nhan`, `quan-sat`, `nguon-ngoai` hoặc `khong-khang-dinh`), chặn câu `quan-sat` chưa xác nhận hoặc thiếu mốc giây, câu nhạy cảm chưa xác nhận, nguồn ngoài thiếu đơn vị, link thẳng, ngày hoặc nằm trên tên miền không cho phép; ghi `kiem-chung.md` từ sổ.
- Thêm `scripts/phan_tich_dau_vao.py`: một lệnh ra thông số, tiếng gốc, bảng ảnh tĩnh (`freezedetect`), mốc đổi cảnh, bảng khung mỗi giây, khung độ phân giải gốc cho đọc chữ, và `job.json` mẫu.
- Thêm `scripts/job.py` (`kiem`, `lam-mo`, `sinh`, `dung`): `job.json` gom giọng, tốc độ, các bước làm mờ, mốc ảnh tĩnh, cue, chữ ghi trên hình, kiểu nhạc; `job.py` sinh `ghep.json`, `dong.json` và gọi các script sẵn có.
- Thêm `scripts/kiem_loi_doc.py`: báo lời chồng (lỗi chặn), khoảng cách dưới 0,2 giây, gạch nối kiểu đánh vần, đại từ xưng hô (đếm theo cảnh, ngưỡng do người dùng đặt), từ khen tuyệt đối, tên riêng viết nguyên dạng trong `narration`, lời dài hơn đoạn ảnh tĩnh; in tiếng mỗi giây từng cảnh.
- Tách mục "Chế độ lồng tiếng cho video có sẵn" ra `references/che-do-video-co-san.md` (kèm mục Job và thứ tự chạy); `SKILL.md` chỉ giữ phần tóm tắt và trỏ sang.
- `scripts/setup.sh`: cài `opencv-python-headless==5.0.0.93` (ghim; chấp nhận bản opencv-python đã có đúng pin), vì các script làm mờ và kiểm khung cần gói này.
- `scripts/dung_lai_video_co_san.sh`: khi `chuan_am.sh` chỉ báo âm lượng lệch mục tiêu (đã ghi file chuẩn hóa) thì vẫn chép ra `output/` và in lại cảnh báo ở cuối; lỗi thật của `chuan_am.sh` (dòng `[LOI]`) vẫn dừng chuỗi. Trước đây `set -e` dừng cả chuỗi và không chép ra gói. Đây là chỗ duy nhất đổi hành vi của script cũ.
- `profiles/unbox.md`: trỏ tới bảng khung kiểm làm mờ và sổ khẳng định. `lam_mo_phieu_chat.py`, `lam_mo_vung_trang.py`: đổi tham chiếu sang `references/che-do-video-co-san.md` (chỉ đổi chữ).
- Đã chạy thử: năm script mới trên video tổng hợp (mờ đúng, mờ thiếu, mờ lấn sang tem đỏ và da; sổ khẳng định đủ ca chặn và ca đạt; lời chồng, xưng hô, viết tắt) và chuỗi `job.py kiem`, `lam-mo`, `dung` với giọng đọc thật của `tts.py` (Hải Đăng), có kéo dài ảnh tĩnh và ghi chữ. Chạy `setup.sh` đầy đủ, rồi một video mẫu 2D khổ dọc trọn quy trình (`tts.py`, `new_project.sh`, `inject.py`, `hyperframes check` đạt, `render.sh final` 14 giây cho 6,4 giây video, `chuan_am.sh`, `check_output.py` ĐẠT).
- Chưa kiểm: các script mới chưa chạy trên video khui hàng thật (chỉ video tổng hợp), nên ngưỡng `DO`, `DA`, `CON-TRANG` chưa được hiệu chỉnh trên phiếu và tem thật; danh sách từ khen tuyệt đối, cụm câu nhạy cảm và tên miền cấm là danh sách đề xuất, cần bổ sung khi gặp ca mới; chưa nghe lại bằng tai cách đọc "A-đáp", "ô bê giê e", "ét pê ép"; `kiem_loi_doc.py` không có ngưỡng tiếng mỗi giây vì chưa có số đo đủ.

## [1.6.0] - 2026-11-17

Bài học từ một job khui hàng kem nền OBgE (720x1280, 88 giây, người dùng chê làm mờ quá lố và yêu cầu bỏ thông tin không chắc).

- Thêm `scripts/lam_mo_phieu_chat.py`: làm mờ phiếu giao hàng chặt hơn `lam_mo_vung_trang.py`. Chỉ nhận vùng trắng trong `--vung X0,X1,Y0,Y1`, bỏ thành phần nằm trong tem đỏ (chữ trắng "hàng dễ vỡ" bị bắt nhầm), nở bao lồi 7 px thay vì 17, giữ nguyên hình cho mảnh nhỏ (mép phiếu lộ ra ở cạnh thùng sau khi úp, phóng to thấy vạch mã vạch). Chạy hai lượt (dải clip, rồi vùng hẹp quanh thùng). Đã chạy thử trên job đó: kết quả hai lượt giống từng điểm ảnh (PSNR vô cực) với bản đã giao cho người dùng sau khi sửa; người dùng chưa xem lại. Cần `opencv-python` như các script làm mờ khác.
- `SKILL.md` (chế độ video có sẵn): hướng dẫn dùng script mới, lời cho đoạn ảnh tĩnh chạy theo chuỗi ý và rút cho vừa 2,5 đến 3,4 giây mỗi ảnh, quy tắc "không chắc thì bỏ" (cọ tích hợp khác cọ tháo rời; thông cáo của hãng không đủ làm căn cứ cho đúng mẫu), tìm nguồn thương hiệu (bỏ trang bán lẻ, trang chính thức có thể bán bản PRO khác hộp), `tts.py --only` phân cách bằng dấu phẩy, `--retime` sau khi xóa cảnh, đổi video đã làm mờ trong `ghep.json`.
- `profiles/unbox.md`: mục soát trước khi gọi QA thêm che chặt và bỏ câu quan sát không chắc. `scripts/lam_mo_vung_trang.py`: ghi thêm giới hạn đã biết (chỉ đổi chữ).
- Chưa chạy thử `setup.sh`, `new_project.sh`, `inject.py`, `render.sh` vì không bị ảnh hưởng (chỉ thêm script cho chế độ video có sẵn và sửa tài liệu). Chưa kiểm tra bằng tai cách đọc "A-đáp", "ô bê giê e", "ét pê ép".

## [1.5.0] - 2026-11-17

- Thêm `scripts/chu_may_chu.py`: tạo chữ ghi trên video hiện từng chữ như máy đánh chữ kèm dòng nguồn nhỏ (file `.ass`), và ghi vào video bằng bộ lọc `ass` của ffmpeg (mã hóa lại hình crf 16, giữ tiếng). Đã chạy thử trên job đó: `.ass` giống từng dòng và video giống từng điểm ảnh (PSNR vô cực) với bản đã giao cho người dùng; người dùng đã xem khung hình, chưa báo lỗi. Font mặc định Inter (có sẵn trên máy chạy thử, hỗ trợ tiếng Việt); chưa thử font Be Vietnam Pro. `SKILL.md` thêm bước 5b, `profiles/unbox.md` thêm mục "Chữ ghi trên video".

## [1.4.0] - 2026-11-17

Bài học từ một job lồng tiếng thật cho video khui hàng cáp HDMI (720x1280, 90 giây, 20 câu, gồm phần quay thật và 17 ảnh tĩnh).

- Thêm `scripts/lam_mo_tay.py`: làm mờ bằng khung đặt tay theo mốc giây, cho phiếu giao hàng bị bóc nghiêng, tay che hoặc rách thành mảnh nhỏ mà `lam_mo_vung_trang.py` bỏ sót (trên job thật, phiếu lộ ra ở giây 2,5 đến 3,1 dù script báo OK). Đã chạy thử lại trên job đó: kết quả giống bản dựng tay (PSNR 50 dB, cùng 25 khung bị mờ).
- Thêm `scripts/dung_lai_video_co_san.sh`: một lệnh chạy lại ghép lời, cập nhật `total` trong `timeline.json`, nhạc nền, chuẩn âm, chép ra gói sau mỗi lần sửa lời hoặc làm mờ. Đã chạy thử trên job đó: ra video dài bằng bản dựng tay (91,57 giây); file không giống từng byte vì mã hóa lại.
- `SKILL.md` (chế độ video có sẵn): lập bảng mốc/ảnh/lời bằng `freezedetect`, lời cách nhau tối thiểu 0,2 giây, kiểm khung mỗi 0,1 giây khi làm mờ, trỏ tới script mới, cách viết chữ viết tắt, mức nhạc nền cho video lời thưa.
- `references/giong-doc.md`: bảng cách viết liền cho viết tắt (HDMI, HDR); viết có gạch nối bị đọc rời và ngắt quãng. Cách đọc chưa được người dùng xác nhận lại bằng tai.
- `profiles/unbox.md`: câu mở đầu mẫu không đại từ, tìm trang hãng theo đúng SKU, nhãn QR chỉ nói "quét để kiểm tra", soát làm mờ và nhạc nền.
- `scripts/lam_mo_vung_trang.py`: ghi thêm giới hạn đã biết trong phần mô tả đầu file (chỉ đổi chữ).
- Chưa chạy thử `setup.sh`, `new_project.sh`, `inject.py`, `render.sh` vì không bị ảnh hưởng (chỉ thêm script cho chế độ video có sẵn và sửa tài liệu). `lam_mo_tay.py` và `dung_lai_video_co_san.sh` cần `opencv-python` và `soundfile` như hai script của 1.3.0.

## [1.3.0] - 2026-11-17

- `SKILL.md`: thêm mục "Chế độ lồng tiếng cho video có sẵn" (phân tích video, viết lời theo mốc, làm mờ vùng nhạy cảm, ghép lời, giao); sửa mô tả để việc viết lời, lồng tiếng và làm mờ cho video có sẵn không còn bị loại.
- Thêm `scripts/lam_mo_vung_trang.py` (làm mờ phiếu giao hàng hoặc vùng trắng trong một khoảng thời gian) và `scripts/ghep_loi_video_co_san.py` (đặt lời của `tts.py` đúng giây của video có sẵn, kéo dài ảnh tĩnh bằng giữ khung hình, ghi `phu-de.srt`).
- `profiles/unbox.md`: giảm đại từ xưng hô, mục ảnh tĩnh cuối video, dùng script làm mờ.
- `references/giong-doc.md`: tốc độ đọc Hải Đăng đo được (khoảng 4,2 tiếng mỗi giây) và cách ghi tên riêng, chỉ số; `agents/bien-kich.md` trỏ tới đó.
- `scripts/chuan_am.sh`: sửa lời cảnh báo khi không có nhạc nền (chỉ đổi chữ, không đổi ngưỡng).
- Đã chạy thử hai script mới trên một job thật (video 720x1280, 88 giây, 14 cảnh): mốc giữ khung hình trùng bản dựng tay trước đó, độ giống khung hình 3 giây đầu SSIM 0,994, lời không chồng nhau; làm mờ khoảng 2 phút cho video này trên máy chạy thử. Chưa chạy lại `setup.sh`, `new_project.sh`, `inject.py`, `render.sh` vì không bị ảnh hưởng; chưa kiểm tra bằng tai cách đọc tên thương hiệu.
- Hai script mới cần `opencv-python` và `soundfile`; `setup.sh` chưa ghim hay cài `opencv-python`, nên chưa thêm vào đó (chưa có bản ghim đã kiểm). Workspace chạy thử đã có sẵn.

## [1.2.0] - 2026-11-15

- Thêm hồ sơ thể loại `unbox.md` (mở hộp từ góc nhìn người tiêu dùng, trên cảnh quay thật của người dùng): giọng người mua, phân loại thông tin (lời ghi trên bao bì, quan sát, thông tin ngoài có nguồn), cấu trúc cảnh, câu hỏi gom ở bước 0, danh sách soát trước QA, metadata.
- `agents/qa.md`: thêm mục đối chiếu yêu cầu riêng của brief và các lỗi hay gặp (từ tuyệt đối chưa đo, nhãn dịch lệch, lời lệch hình, phụ đề không khớp).
- `SKILL.md`: ghi cách chạy render nền bằng `setsid nohup` và gom sửa chữ trước khi render bản cuối.
- Chưa thêm script dựng clip theo cảnh và render nháp theo cảnh: bản dùng ở job mẫu gắn cứng tên dự án, cần tổng quát hóa và chạy thử trước. Chưa chạy thử đầu cuối bằng `setup.sh` và `new_project.sh` cho thay đổi này (chỉ thay đổi tài liệu).

## [1.1.0] - 2026-11-14

- Kiểu `ve-net`: bàn tay cầm bút đổi từ SVG vẽ bằng code sang ảnh PNG (`assets/venet/hand.png`, `hand-shadow.png`), do người dùng tạo bằng Grok; `new_project.sh` chép ảnh vào `build/<khổ>/assets/`.
- Bàn tay cử động tự nhiên hơn: cổ tay xoay theo vị trí, nhấc bút theo đường cong khi chuyển nét, bóng đổ lùi xa khi nhấc, rung nhẹ tất định.
- Thêm `tools/tach_ban_tay.py` để tách nền ảnh bàn tay mới.
- Ghi công ảnh bàn tay trong README và `references/ve-net.md`.
- Đã chạy thử trọn video mẫu 124 giây (Mac mini M6, 11 cảnh): lồng tiếng, `inject.py`, `hyperframes check` 0 lỗi, `render.sh` bản xem trước khổ dọc khoảng 340 giây (2,7 giây cho mỗi giây video), `check_output.py` ĐẠT. Chưa thử khổ ngang.

## [1.0.0] - 2026-11-14

Mốc phiên bản đầu tiên, tính từ trạng thái `main` tại commit `fcf0306`. Gần nhất trước mốc này:

- Thêm lớp tính cách (cách diễn) cho vai.
- Thêm thư viện hồ sơ vai và đổi skin theo cảnh.
- Sửa `chuan_am.sh` làm hỏng bản gốc không nhạc, `setup.sh` cài lại khi đổi pin, kiểm `venet-chu.js` trong CI.
