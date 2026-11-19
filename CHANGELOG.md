# Nhật ký thay đổi

Quy ước số phiên bản `MAJOR.MINOR.PATCH`, ghi ở `video-studio/VERSION` và dòng "Phiên bản skill" trong `video-studio/SKILL.md` (hai nơi phải khớp, CI kiểm tra khi đóng gói). Thêm kiểu hình hoặc tính năng thì tăng MINOR; sửa lỗi thì tăng PATCH; đổi lớn làm hỏng cách dùng cũ thì tăng MAJOR. Mỗi lần gộp PR thay đổi skill: tăng số, sửa hai nơi trên và thêm mục mới ở đầu file này.

## [1.16.0] - 2026-11-19

Chế độ lồng tiếng cho video có sẵn: rút kinh nghiệm từ một job khui hàng khổ dọc 720x1280 (81,3 giây, 10 cảnh lời, ảnh tĩnh cuối video chỉ có nhạc, phiếu giao hàng xoay nhanh trong tay). Không đổi quy tắc kiểm chứng, bản quyền, khóa nhân vật.

- `scripts/kiem_loi_doc.py`: khóa `anh_tinh_khong_loi` trong `job.json`. Bật thì cảnh nào có lời chạm vào đoạn `anh_tinh` (kể cả lời bắt đầu trước đoạn rồi tràn vào) bị `[CANH BAO]`. Kiểm hiện có chỉ bắt lời bắt đầu bên trong đoạn ảnh tĩnh, nên lời tràn từ ngoài vào không bị báo (trong job trên, cảnh cuối dài 4,28 giây trong cửa sổ khoảng 3 giây, phải tự phát hiện khi xem mốc). Lời tính trên video ghép còn `anh_tinh` tính trên video gốc, nên chỉ dùng khi không có `giu_hinh` đứng trước đoạn đó (ghi trong tài liệu). `scripts/job.py` ghi thêm khóa này trong phần mô tả `job.json`.
- `scripts/check_output.py --co-san`: video có sẵn không phóng to, độ phân giải khác 1080x1920 hay 1920x1080 chỉ là `[CANH BAO]`, không còn là `[LOI]` (mặc định không đổi). Đã thử trên video 720x1280 của job trên: không cờ báo 1 LỖI, có cờ báo CẢNH BÁO và KẾT QUẢ ĐẠT.
- `references/che-do-video-co-san.md`: thêm mục 4b (phiếu xoay nhanh: nối nhiều bước `lam_mo` `phieu_chat` rồi `tay`, đặt mốc cách 0,2 giây, nới khung, xem lại từng khung cách 0,1 giây; ghi rõ chưa có bước tự nhận biết phiếu), 4c (đoạn ảnh tĩnh chỉ có nhạc, nhạc chạy xuyên video), 4d (`--co-san`).
- `profiles/unbox.md`: hỏi thêm ở bước 0 người dùng đã dùng thử chưa hoặc người nhà nhận xét gì (đọc rõ ai nhận xét, không viết như kết luận khách quan; đổi sau khi lồng tiếng thì cập nhật khóa kịch bản), và nhạc nền chạy xuyên video hay chỉ ở ảnh tĩnh.
- `references/giong-doc.md`: thêm hai dòng "QR" và "XL" vào bảng cách đọc viết tắt, ghi rõ đã dùng và chưa nghe kiểm bằng tai.
- `tools/smoke_test.sh`: thêm ca `anh_tinh_khong_loi` (lời tràn vào đoạn ảnh tĩnh bị báo; không bật thì không báo; lời kết thúc trước đoạn ảnh tĩnh không báo nhầm) và kiểm có `--co-san`. Đã xác nhận ca đầu thất bại trên mã 1.15.1.
- Đã chạy thử: `smoke_test.sh` đạt; `ruff F,E9` sạch; `check_output.py` thật với ffprobe và ffmpeg trên video đã giao của job trên. Chưa chạy: `setup.sh`, `tts.py`, `new_project.sh`, `inject.py`, `hyperframes check`, `render.sh`, `job.py dung` trọn chuỗi (thay đổi không chạm các bước này).
- Chưa làm (đề xuất, cần thiết kế và thử riêng): tự nhận biết và theo dõi phiếu giao hàng (hộp trắng có mã vạch hoặc QR) để đặt khung làm mờ; kiểm tự động video đã làm mờ bằng đọc mã vạch hoặc QR và báo đích danh khung còn đọc được; nhạc nền chỉ ở đoạn ảnh tĩnh; lệnh đồng bộ `khang-dinh.json` khi sửa lời mà giữ loại cũ cho câu trùng; đóng gói riêng cho video có sẵn (`package.py` hiện chỉ chép `renders/final_*.mp4` và tạo thumbnail); `phan_tich_dau_vao.py` nhận diện đoạn ảnh tĩnh tốt hơn khi có chuyển mờ và đoạn quay đứng yên.

## [1.15.1] - 2026-11-19

Sửa hai lỗi ở bước ghép lời vào video có sẵn (tìm ra khi rà soát repo sau 1.15.0); không đổi quy tắc kiểm chứng, bản quyền, khóa nhân vật.

- `scripts/ghep_loi_video_co_san.py`: mốc `cue` là giây trên video gốc, nhưng trước đây không được cộng phần kéo dài của các lần `giu_hinh` nằm trước nó, nên lời của cảnh `cue` đứng sau một cảnh giữ hình phát sớm hơn hình, `phu-de.srt` và `timeline_ghep.json` ghi mốc sai và script báo chồng lời giả. Nay mốc ghép = `cue` + tổng phần kéo dài của các lần giữ hình có `dong_bang` không lớn hơn `cue` (tính theo khung hình đã làm tròn như bước nhân khung). Thử: video 5 giây, `s01` giữ hình ở 1,0 giây (kéo thêm 2,0 giây), `s02` cue 2,0 giây: trước đây lời `s02` ở giây 2,0, nay ở giây 4,0 (video ghép 7,0 giây).
- Cùng file: lời đọc kết thúc sau cuối video ghép (cảnh cuối có lời dài hơn phần hình còn lại) trước đây làm script dừng giữa chừng với `ValueError: operands could not be broadcast` (đã ghi xong `video_giu_hinh.mp4`, chưa có thành phẩm). Nay script chặn sớm theo thời lượng video và kiểm lại chính xác sau khi đếm khung hình, in `[LOI]` ghi cảnh và số giây vượt, không tự cắt lời.
- `scripts/kiem_loi_doc.py`: khi chưa có `timeline_ghep.json`, cue cũng được cộng phần kéo dài giữ hình (hết báo chồng lời giả); báo `[LOI]` khi lời kết thúc sau cuối video (cuối video lấy từ `tong_giay` của `timeline_ghep.json`, hoặc video gốc cộng phần kéo dài khi chưa ghép).
- `scripts/job.py kiem`: in `[CANH BAO]` cho cảnh `cue` có lời vượt cuối video ghép, trước khi chạy `dung`.
- `tools/smoke_test.sh`: thêm ca cue sau giữ hình và ca lời vượt cuối video (đã xác nhận ca thứ nhất thất bại trên mã 1.15.0).
- Đã chạy thử: `smoke_test.sh` đạt; `ruff F,E9` sạch; `job.py kiem` và `ghep_loi_video_co_san.py` với ffmpeg thật trên video mẫu 5 giây (ca lời vượt báo lỗi thoát mã 1; ca hợp lệ ghép 7,0 giây, `phu-de.srt` khối 2 ở 4,0 giây). Chưa chạy: `setup.sh`, `tts.py`, `new_project.sh`, `inject.py`, `hyperframes check`, `render.sh` (không chạm các bước này), `job.py dung` trọn chuỗi (cần `tts.py` và mô hình giọng).
- Chưa sửa: hai mốc `dong_bang` làm tròn ra cùng một khung hình thì một lần giữ hình bị mất.

## [1.15.0] - 2026-11-19

Chế độ lồng tiếng cho video có sẵn: phụ đề từng từ, áp lời sửa từ srt, kiểm lời bớt báo nhầm. Rút ra từ một job khui hàng khổ dọc 720x1280 (video quay 89,7 giây, 27 cảnh lời). Không đổi quy tắc kiểm chứng, bản quyền, khóa nhân vật.

- Thêm `scripts/phu_de_tung_tu.py PROJECT [--ghi VIDEO_VAO VIDEO_RA]`: phụ đề từng từ (từ đang đọc đổi màu) ghi cứng vào hình cho chế độ video có sẵn, từ `moc-tu.json`, `timeline.json`, `timeline_ghep.json` (mốc cảnh đổi sang mốc video đã ghép). Chọn font bằng `fc-list` (Be Vietnam Pro TTF/OTF, rồi Inter, rồi mặc định kèm cảnh báo); gói `@fontsource` mà `setup.sh` cài chỉ có woff/woff2 (đã kiểm: 54 woff và 54 woff2, không có ttf) nên libass không đọc được. Tự kiểm định dạng ASS (đủ 7 trường mỗi dòng `Dialogue`): bản viết tay đầu tiên ghi thừa trường nên chữ "0,0,," lọt lên hình.
- `scripts/dung_lai_video_co_san.sh --tung-tu` và `job.json` `"tung_tu": true` (cho `job.py dung`): thêm `output/<tên>-phu-de-tung-tu.mp4`, giữ `output/<tên>.mp4` không phụ đề cứng. Có cả `chu` thì `job.py dung` thêm `output/<tên>-chu-phu-de-tung-tu.mp4` đủ cả chữ ghi trên hình và phụ đề từng từ. `phu_de_tung_tu.py` cắt kết thúc sự kiện ở lúc sự kiện kế tiếp bắt đầu, để hai câu không hiện cùng lúc khi hai lời cách nhau dưới 0,3 giây; bước tự kiểm bắt dòng thừa trường qua trường Name và Effect, không báo nhầm phụ đề bắt đầu bằng số thập phân kiểu Việt ("2,5 mét").
- Thêm `scripts/ap_sua_srt.py PROJECT SUA.srt [--ap]`: áp các khối `phu-de.srt` người dùng đã sửa vào `scenes.json` (xem trước, rồi `--ap`; giữ bản sao `scenes.truoc-sua.json`, `khang-dinh.truoc-sua.json`) và đồng bộ `khang-dinh.json`: câu đổi chữ về `chua-phan-loai` bất kể loại cũ, kể cả `khong-khang-dinh` (câu mới có thể thêm số liệu), loại cũ ghi ở `loai_cu`; câu giữ nguyên chữ giữ mục cũ; cảnh đổi chưa có mục trong sổ thì thêm mục mới. Khối srt ghép với cảnh theo mốc trong `timeline_ghep.json` (`phu-de.srt` đánh số theo mốc bắt đầu, không theo thứ tự `scenes.json`). Cảnh có `subtitle` khác `narration` chỉ sửa `subtitle` và in `[CAN XEM]`. Khối srt lệch mốc cảnh quá 0,15 giây bị bỏ qua.
- `scripts/kiem_loi_doc.py`: báo `[CANH BAO]` khi `timeline_ghep.json` cũ hơn `job.json`, `scenes.json` hay một `audio/<id>.wav` (trước đây chạy trước `job.py dung` thì báo "lời chồng" giả vì đọc mốc cũ). Chưa có `timeline_ghep.json` thì tính mốc các cảnh `giu_hinh` bằng cùng công thức ghép (cảnh giữ hình đứng trước đẩy lùi các cảnh sau), nên hai cảnh giữ hình liên tiếp không còn bị báo chồng lời giả trước khi ghép (gặp khi chạy thử trên video thật: s05 và s06 báo chồng 0,5 giây, sau khi ghép thì không).
- `scripts/job.py kiem`: in `[THONG TIN]` ước tính tổng thời lượng sau khi giữ khung hình và các cảnh bị kéo dài nhiều nhất (cùng công thức `ghep_loi_video_co_san.py`; cần đã có `audio/*.wav`). Ước tính 107,2 giây khớp video ghép thật 107,2 giây.
- `scripts/kiem_khung_lam_mo.py --trang-min N` (mặc định 1200, không đổi hành vi cũ): hạ ngưỡng điểm trắng để soi mảnh phiếu nhỏ vừa bóc. Đo trên đoạn 2,0 đến 3,2 giây của job trên: mặc định báo 6/12 mốc, `--trang-min 300` báo 12/12 mốc (nhiều báo nhầm), nên tài liệu ghi chỉ dùng để soi đoạn đã nghi.
- `references/che-do-video-co-san.md`: thêm bước 5c phụ đề từng từ, mục áp lời sửa bằng srt, cảnh báo `timeline_ghep.json` cũ, ước tính thời lượng, nhắc xem lại mọi mốc có cảnh báo làm mờ ở độ phân giải đủ đọc.
- `tools/smoke_test.sh`: thử `phu_de_tung_tu.py` (đổi mốc sang mốc ghép, bắt dòng thừa trường), `ap_sua_srt.py` (xem trước không ghi, `--ap`, đồng bộ sổ khẳng định, srt lệch mốc), cảnh báo `timeline_ghep.json` cũ.
- Đã chạy thử: `smoke_test.sh` đạt; trọn chuỗi `job.py kiem`, `job.py dung` với `tung_tu` trên bản sao dự án thật (video 89,7 giây, 27 cảnh, giọng Hải Đăng đã đọc sẵn): ghép 107,2 giây, `phu_de_tung_tu.py` 260 sự kiện, xem khung hình có phụ đề; chuỗi sự kiện ASS trùng bản viết tay đã giao cho người dùng. `ap_sua_srt.py` thử trên bản sao dự án với 4 khối sửa. Chưa chạy: `setup.sh`, `tts.py` mới từ đầu, `new_project.sh`, `inject.py`, `hyperframes check`, `render.sh` (thay đổi không chạm các bước này); chưa thử trên video khổ ngang hay video có tiếng gốc.

## [1.14.1] - 2026-11-18

Sửa lỗi sau đợt rà soát chế độ dịch (1.14.0); không đổi quy tắc kiểm chứng, bản quyền, khóa nhân vật.

- `scripts/phu_de_dich.py`: `kiem` không còn chặn bản dịch viết số thập phân kiểu Việt (lời gốc "3.5", bản dịch "3,5"; "1,000" và "1.000" coi là một nghìn); vẫn bắt mất số (thử "3.5" so với "35", "10" biến mất). `--song-ngu`: dòng gốc dài trước đây tràn ra ngoài khung (`WrapStyle: 2` không tự ngắt; khổ 720x1280 mất hai đầu câu), nay ngắt dòng theo cỡ chữ 0,7 lần và dòng dịch đẩy lên theo số dòng gốc; sửa cả vị trí dòng dịch khi `--vi-tri tren`. Chữ `{...}` trong bản dịch (libass coi là lệnh định dạng, mất chữ) đổi thành `(...)`; dấu gạch ngược đổi thành `/` (trước đây `\N` gây xuống dòng thừa).
- `scripts/setup.sh --dich`: ghim thêm `ctranslate2==4.9.0` (bản đã đo ở 1.13.0) và `av==17.0.0`. Thử trong venv sạch ngày 2026-11-18: `faster-whisper` 1.2.1 với `av` 19.0.2 (bản pip chọn mặc định) tái hiện lỗi `open() got an unexpected keyword argument 'metadata_errors'` ở `decode_audio`; `av` 15.1.0, 16.1.0 và 17.0.0 chạy được; chọn 17.0.0 (mới nhất chạy được). Lỗi pip không còn bị giấu (in 15 dòng cuối). `--check` báo thêm trạng thái faster-whisper.
- `scripts/chep_loi_goc.py`: bỏ `import re` thừa; `--ngon-ngu` ngoài en, zh, vi in `[CANH BAO]` và ghi vào `chep-goc.md` (không dừng hỏi vì người dùng đã chọn).
- `tools/smoke_test.sh`: thêm phép thử số thập phân kiểu Việt, thoát ký tự libass và ngắt dòng gốc song ngữ (đã xác nhận phép thử thất bại trên mã 1.14.0).
- Đã chạy thử: `kiem` và `ghi` (khổ ngang 1280x720 và dọc 720x1280, `--song-ngu`, `--vi-tri tren`) trên video mẫu, xem ảnh khung hình; `smoke_test.sh` đạt; ruff F, E9 sạch trên hai script đã sửa. Chưa chạy lại trọn video mẫu (`setup.sh`, `tts.py`, `render.sh`...) vì thay đổi chỉ chạm script chế độ dịch và `setup.sh --dich`; chưa chạy `chep_loi_goc.py` với mô hình Whisper thật sau khi ghim `av` (đã thử `decode_audio` và VAD với `av` 17.0.0, chưa tải mô hình).

## [1.14.0] - 2026-11-18

Chế độ dịch video, phần phụ đề: chép lời gốc bằng Whisper (tự nhận dạng ngôn ngữ, cờ nghi ngờ), kiểm bản dịch, ghi phụ đề cứng tiếng Việt. Thuyết minh chưa có script. Không đổi quy tắc kiểm chứng, bản quyền, khóa nhân vật.

- Thêm `scripts/chep_loi_goc.py VIDEO PROJECT [--ngon-ngu auto|en|zh...] [--ban medium|small] [--khong-vad]`: đọc tiếng bằng ffmpeg ra mảng 16 kHz (tránh lỗi PyAV khi đưa đường dẫn file vào faster-whisper), nhận dạng ngôn ngữ theo khúc 30 giây có ít nhất 3 giây tiếng nói (VAD) trên mọi ngôn ngữ, in `[CAN HOI]` khi không chắc chắn hoặc ngôn ngữ ngoài en, zh, vi; chép bằng `medium` bật VAD; mốc đoạn lấy theo từ đầu và từ cuối cộng 0,4 giây (mốc đoạn gốc của Whisper trùm cả khoảng nhạc: 4,6 đến 40,2 giây cho một câu 2 giây); cờ `nghi-bia`, `tin-thap`, `ngan`; liệt kê khoảng không có lời trên 2 giây. Ra `dich/chep-goc.json` và `chep-goc.md`.
- Thêm `scripts/phu_de_dich.py khoi|kiem|srt|ghi`: `ban-dich.json` theo đoạn (gộp đoạn bằng `bo`); kiểm chặn thiếu dịch, chồng đoạn, vượt thời lượng, chữ số mất ở bản dịch, quá 2 dòng, chưa NFC; cảnh báo đọc nhanh hơn `--cps` (15), hiện dưới 1 giây, đoạn có cờ; tự kéo dài đoạn đọc nhanh vào khoảng trống phía sau tối đa `--keo-dai` (1,5 giây); ghi `output/phu-de-vi.srt`, phụ đề cứng `.ass` theo kích thước video (giữ độ phân giải, chép nguyên tiếng), `--song-ngu`, `--vi-tri tren`, `--che-day` (làm mờ dải đáy để che phụ đề cứng sẵn có); xuất bảng khung kiểm `dich/qa-phu-de.png`.
- Thêm `profiles/dich.md`, `references/che-do-dich.md`; `SKILL.md`: bảng thể loại, mục Chế độ dịch video, tham khảo.
- `scripts/setup.sh --dich`: cài thêm `faster-whisper==1.2.1` (ghim). Không cờ thì hành vi như cũ.
- `tools/smoke_test.sh`: thử `phu_de_dich.py khoi`, `kiem` (chặn thiếu dịch, mất số), `srt` (bỏ đoạn đánh dấu `bo`).
- Đã chạy thử: `setup.sh --dich` đầy đủ; trọn chế độ dịch trên vlog tiếng Anh 143 giây 1280x720 (`chep_loi_goc.py` tự nhận dạng `en` 0,972, 29 đoạn, khoảng 42 giây với `--ngon-ngu en` khi đã có mô hình; dịch, gộp đoạn, `kiem` 0 lỗi; `ghi` 34 giây, thêm `--che-day 0.2` 42 giây; xem bảng khung kiểm: phụ đề song ngữ Trung Anh sẵn có của video bị che, chữ dịch đọc rõ). Thử `kiem` với bản dịch cố ý sai: bắt đủ thiếu dịch, mất số `3.5`, chồng đoạn, chữ NFD, quá 2 dòng. Video mẫu thường 2 cảnh khổ dọc 2D: `tts.py`, `new_project.sh`, `inject.py`, `hyperframes check` đạt, `render.sh final` 17 giây cho 6,4 giây video, `check_output.py` ĐẠT. `smoke_test.sh` đạt.
- Chưa kiểm: thuyết minh; tiếng Trung dài có nhạc nền; video nhiều người nói (Whisper không tách người nói); ngưỡng cờ và ngưỡng chắc chắn mới lấy theo 3 clip; `--cps` 15 chưa đo riêng cho phụ đề tiếng Việt; `--song-ngu` với lời gốc dài hơn một dòng có thể chạm dòng dịch.

## [1.13.0] - 2026-11-18

Thêm mô hình nhận dạng giọng nói Whisper (small, medium) vào Release riêng và script tải; chưa nối vào quy trình nào (chưa có `asr_check`, chưa có chế độ dịch video). Việc đã làm: ghim, chép nguyên vẹn, kiểm sha256.

- Thêm `video-studio/assets/whisper-models.json`: danh mục 8 file (`config.json`, `model.bin`, `tokenizer.json`, `vocabulary.txt` của hai bản), kích thước, sha256, revision huggingface ghim bằng mã commit (small `536b0662`, medium `08e178d4`; `model.bin` của cả hai khớp sha256 trong API huggingface), tag release `whisper-faster-small-medium-536b066-08e178d`.
- Thêm `scripts/lay_whisper.py small|medium [--kiem]`: tải từ GitHub Release trước, huggingface dùng đúng revision ghim là dự phòng, mỗi file phải khớp kích thước và sha256; in đường dẫn thư mục mô hình ở dòng cuối. Mô hình để ở `$STUDIO_HOME/.tools/whisper/<bản>`, không vào git hay zip. `setup.sh` không tải Whisper (mỗi bản 484 MB và 1,5 GB), chỉ tải khi cần.
- Thêm `tools/publish_whisper_models.sh` và workflow `whisper-models.yml`: đăng bản chép lên Release riêng khi danh mục đổi trên `main`, cùng mẫu với `voice-models.yml`. Không xóa hay tạo lại release này.
- Thêm `references/LICENSE-whisper.txt` (MIT của openai/whisper) và mục Ghi công trong README.
- Số đo (2026-11-18, workspace 2 lõi CPU không GPU, faster-whisper 1.2.1, ctranslate2 4.9.0, `int8`, `language=vi`, `beam_size=5`): 10 câu lời đọc giọng Hải Đăng, 41,1 giây tiếng. WER so với `narration` (bỏ dấu câu, hạ chữ thường): small 0,281, medium 0,232 (bản `base` 0,432, không đưa vào). Cả ba nhận đủ 9/9 số cần có. Tốc độ giải mã (giây giải mã trên giây tiếng): small 0,55, medium 1,48. Kết quả đầy đủ ở tài liệu dự án `claude/do-thu-whisper-tieng-viet.md`.
- Chưa kiểm: chỉ 10 câu, một giọng, tiếng tổng hợp sạch; chưa đo với giọng thật, tiếng nói tiếng Anh hay tiếng Trung, tiếng có nhạc nền. `faster-whisper.transcribe(đường_dẫn_wav)` lỗi ở workspace đo (`av.open() got an unexpected keyword argument 'metadata_errors'`, gói PyAV không khớp); cách tránh đã dùng là tự nạp wav, đổi về 16 kHz rồi đưa mảng số vào. Chưa ghim phiên bản faster-whisper trong `setup.sh`.

## [1.12.1] - 2026-11-18

Sửa lỗi sau đợt rà soát repo; không đổi quy tắc kiểm chứng, bản quyền, khóa nhân vật.

- `SKILL.md`: rút gọn `description` từ 1016 xuống 819 ký tự (giới hạn của claude.ai là 1024; thêm `mo hop san pham`). `tools/package_skill.sh` kiểm độ dài này: quá 1024 thì dừng, trên 960 thì cảnh báo.
- `SKILL.md`: tách chi tiết cổng casting (bước 3b: hồ sơ vai, skin theo cảnh, tính cách, thử vai line-art, chibi, 3D, nghe thử giọng, trường `casting.json`) sang `references/casting.md`, chép nguyên văn. Bước 3b trong `SKILL.md` giữ tóm tắt các quy tắc bắt buộc (dùng đúng hồ sơ vai, dàn đã khóa, một nhân vật một giọng, dừng chờ người dùng, `vai.py kiem-casting`, khóa sau khi chốt) và lệnh đọc tài liệu. `SKILL.md` giảm từ 57,3 KB xuống khoảng 52 KB.
- `scripts/render.sh`: render ra file tạm `.dang-render-<tên>` rồi mới đổi tên thành file đích. Trước đây lệnh bị cắt giữa chừng (vd video 3D quá 10 phút) có thể để lại file đích dở dang mà lần chạy sau coi là đã xong và bỏ qua.
- `scripts/tts.py`: mô hình đã tải sẵn được kiểm sha256 một lần (ghi `<file>.sha256` cạnh file), sai thì tải lại. Trước đây chỉ kiểm kích thước.
- `scripts/setup.sh`: `.voice_done` ghi bản vieneu, onnxruntime và tag mô hình; khớp thì bỏ qua bước thử giọng nên chạy lại setup nhanh (đo: 3 giây). Lần chạy đầu sau khi cập nhật vẫn thử giọng một lần.
- `scripts/inject.py`: `--srt-only` mặc định ngắt dòng ở 48 ký tự (như khổ ngang) thay vì 42, nên `.srt` khớp phụ đề đốt chữ khổ ngang. `--tung-tu`: dòng phụ đề chỉ có dấu câu không còn làm script dừng vì `StopIteration`; dòng đó nối vào dòng trước.
- Bỏ mã thừa: biến `ti_le` trong `kiem_khung_lam_mo.py`, f-string không có biến trong `phan_tich_dau_vao.py`, `check_output.py`, `tools/mocap/bvh2que.py`.
- Thêm `tools/smoke_test.sh` và bước chạy nó trong workflow đóng gói (mỗi PR): `inject.py` khổ dọc, ngang, `--tung-tu`, `--srt-only`, dòng chỉ có dấu câu; `ma_khang_dinh.py`; `khoa_kich_ban.py`; `soat_canh.py`; `trang_thai.py`; `vai.py kiem`; cú pháp script shell. Không cần mô hình giọng, trình duyệt hay mạng; không thay bước chạy thử trọn một video mẫu.
- Đã chạy thử trọn một video mẫu 2 cảnh 2D, khổ dọc (`--tung-tu`) và ngang: `setup.sh` (lần hai bỏ qua thử giọng), `tts.py` với VieNeu thật (8,0 giây), `new_project.sh`, `inject.py`, `hyperframes check` 0 lỗi, `render.sh` preview và final cả hai khổ (11 đến 16 giây mỗi lần, như trước), chạy lại bỏ qua đúng, ngắt render giữa chừng bằng SIGINT không để lại file đích hay file tạm, `check_output.py --srt --frames` ĐẠT cả hai khổ, ảnh khung hình đúng dấu. `tools/smoke_test.sh` đạt; phép thử dòng chỉ có dấu câu báo `StopIteration` trên bản 1.12.0. Chưa thử: kiểu hình line-art, chibi, ve-tay, ve-net, 3D (thay đổi chỉ chạm script dùng chung); bước casting chưa chạy lại với `references/casting.md` mới.

## [1.12.0] - 2026-11-18

Biên kịch tự soát giọng văn máy trong lượt viết (ý tưởng từ blader/humanizer, MIT; xem README mục Ghi công). Không thêm agent, không thêm lượt gọi model.

- `agents/bien-kich.md`: thêm mục "Soát giọng văn máy" gồm 12 lối viết tiếng Việt. Năm mẫu mạnh (đối lập giả "không phải X mà là Y", câu chốt lặp ý, câu nghe sâu sắc, rào đón kiểu "Hãy cùng tìm hiểu", cãi với người không có mặt) sửa ngay khi gặp; bảy mẫu yếu (bộ ba gượng ép, mở câu lặp, từ sáo, thổi phồng, giọng quảng cáo, viện dẫn chung chung, giải thích lại) chỉ sửa khi dồn nhiều trong một hai cảnh. Sửa xong phải so lại với `claims`, không làm mất hay đổi thông tin; "nhiều người nghĩ" và "chuyên gia khuyên" phải thành khẳng định có nguồn hoặc bỏ. Không sửa trích dẫn, tên riêng, thoại theo tính cách, câu cố định của hồ sơ. Báo cáo cuối của biên kịch thêm một dòng số chỗ đã sửa.
- Thêm `references/LICENSE-humanizer.txt`.
- Chỉ đổi chỉ dẫn agent, không đổi script hay template nên không chạy thử trọn một video mẫu. Đã chạy `tools/package_skill.sh` và `unzip -l`. Chưa thử: chưa viết kịch bản thật với chỉ dẫn mới, nên chưa biết biên kịch có sửa quá tay hay bỏ sót không; nên xem mục này ở cổng duyệt kịch bản của vài video đầu.

## [1.11.1] - 2026-11-18

Dấu tiếng Việt về mặt kỹ thuật: chuẩn hóa NFC và soát chữ trước khi giao (ý tưởng kiểm NFC/NFD từ vietfont.vn; mã tự viết, không dùng tài nguyên của trang).

- `scripts/inject.py`: chuẩn hóa Unicode NFC (dấu dựng sẵn) cho phụ đề đốt chữ, chữ từng từ (`--tung-tu`), `phu-de.srt` và toàn bộ `index.html` trước khi ghi, nên chữ agent dựng cảnh gõ tay ở dạng dấu tổ hợp rời (NFD) cũng được sửa.
- `scripts/check_output.py`: soát `.srt` (nếu có `--srt`), `scenes.json` và `build/*/index.html` cạnh `timeline.json`. Dòng chưa NFC là LỖI kèm cách sửa; dòng có ký tự mã cũ TCVN3 (ABC) nằm giữa hai chữ cái là LỖI. Ký hiệu cạnh số (37°C, 5µg) không bị báo. Dừng sau 5 dòng lỗi mỗi file.
- `agents/qa.md`: hai lỗi trên là "Chặn"; soát trên ảnh khung hình dấu chồng hai tầng, chữ hoa có dấu và chữ cỡ nhỏ (dấu bị cắt mép trên, đè dòng trên, lệch khỏi chữ).
- Font không đổi: Be Vietnam Pro và Patrick Hand (SIL OFL 1.1) đã có đủ ký tự tiếng Việt và đã ghi trong credits.
- Đã chạy thử trọn một video mẫu 2 cảnh khổ dọc 2D, chữ trên hình cố ý gõ ở dạng NFD: `setup.sh`, `tts.py`, `new_project.sh portrait`, `inject.py` (index.html và `phu-de.srt` ra NFC), `hyperframes check` đạt, `render.sh final` (12 giây cho video 5,8 giây), `check_output.py --srt --frames` ĐẠT, ảnh khung hình hiện đúng dấu. Thử riêng bộ soát: bắt được `index.html` và `scenes.json` dạng NFD, chữ TCVN3 mẫu; không báo nhầm "37°C", "5µg". Chưa thử: các kiểu hình line-art, chibi, ve-tay, ve-net, 3D và khổ ngang (thay đổi chỉ chạm `inject.py` và bộ soát dùng chung); quy tắc TCVN3 chưa chạy trên chữ mã cũ thật từ người dùng.

## [1.11.0] - 2026-11-18

Bốn mục còn lại từ ghi chú học OpenCreator: kiểm hình đen và đứng yên, đếm tiếng lời đọc, file trạng thái dự án, câu lệnh tranh ve-tay có vai trò ảnh tham chiếu (xem README mục Ghi công; mã và tài liệu tự viết).

- `scripts/check_output.py`: một lần giải mã bằng `blackdetect` (độ sáng dưới 2%, dài từ 0,5 giây) và `freezedetect` (-60 dB). Đoạn đen là LỖI kèm mã cảnh giao với đoạn đó. Đoạn đứng yên từ `--dung-hinh` giây (mặc định 4) là CẢNH BÁO kèm mã cảnh, không phải lỗi, vì đứng hình có chủ ý và cảnh chỉ có chữ là hợp lệ. Đoạn đen không bị báo thêm là đứng yên.
- `scripts/soat_canh.py`: đếm tiếng của `narration`, ước thời lượng từng cảnh theo tốc độ đã đo của giọng (Mai Anh 3,5; Hải Đăng 4,2 tiếng mỗi giây, lấy từ `agents/bien-kich.md` và `references/giong-doc.md`; giọng khác dùng 3,5 và ghi chú) nhân `speed` của cảnh, cộng khoảng nghỉ giữ khớp `tts.py`. Cảnh dưới 2 hoặc trên 10 giây là GỢI Ý; thêm `--muc-tieu GIÂY`: tổng ước tính lệch quá 10% là NÊN SỬA. `--toc-do` ghi đè tốc độ. Ước tính chỉ là ước tính. Đối chiếu với `tts.py` thật trên 3 cảnh mẫu: 3,3 đến 3,7 tiếng mỗi giây (giọng Mai Anh), khớp 3,5.
- Thêm `scripts/trang_thai.py` (`ghi`, `xem`, `xem --json`): `trang-thai.json` trong dự án ghi trạng thái từng bước (dang-lam, xong, cho-nguoi-dung, loi, bo-qua), ghi chú và các tệp đầu ra; `xem` in bảng, báo tệp đã ghi mà mất và chỉ ra bước tiếp theo (0a, 3b, 3c là bước tùy chọn). Chỉ giúp trong một cuộc chat (workspace không sang chat khác). Chưa làm: dòng JSON cuối cho mọi script (`{ok, stage, outputs, error}` như OpenCreator); các script kiểm hiện đã trả mã thoát 0 hoặc 1 kèm văn bản và agent đọc văn bản được, nên chưa đủ lợi ích so với việc sửa nhiều script.
- `references/ve-tay.md`, `SKILL.md`: câu lệnh tranh thêm khối màu (từ chỉ màu trong cảnh là nghĩa, không phải lệnh thêm màu ngoài bảng màu), hai dòng `The picture must communicate` và `Required objects` từ trường tùy chọn `y_chinh`, `vat_bat_buoc` của cảnh, hai vai trò ảnh tham chiếu (nhân vật lặp lại giữ danh tính, không chép dáng và nền; tranh cảnh trước chỉ khi cảnh có `lien_mach`), và chỉ dẫn khổ dọc chừa một phần tư dưới cho phụ đề. `agents/qa.md` đọc cảnh báo hình đứng yên.
- Đã chạy thử: `check_output.py` trên video tổng hợp 7,5 giây có đoạn đứng yên, đoạn đen và đoạn có chuyển động (báo đúng đoạn và cảnh); `soat_canh.py` trên kịch bản mẫu (cảnh ngắn, cảnh dài, giọng Hải Đăng, `pause_before`, `--muc-tieu` lệch 32% và 3%); `trang_thai.py` đủ các nhánh (tệp thiếu, bước sai, tệp mất, `--json`). Chưa thử: phần ve-tay chỉ sửa tài liệu, chưa thử với công cụ tạo ảnh thật nên chưa biết công cụ có làm theo vai trò ảnh tham chiếu hay không; `check_output.py` chưa chạy trên video render thật có nội dung (ngưỡng đen và 4 giây là chọn ban đầu, có thể cần chỉnh sau vài video); không có chạy trọn một video mẫu.

## [1.10.0] - 2026-11-18

Mã khẳng định: mỗi claim có mã, mỗi mã đúng một dòng kiểm chứng, kiểm bằng script (ý tưởng chuỗi nguồn - khẳng định - cảnh bằng mã từ OpenCreator, xem README mục Ghi công; mã tự viết).

- Thêm `scripts/ma_khang_dinh.py` (`gan`, `liet-ke`, `kiem`): `gan` đổi `claims` dạng chuỗi thành `{"id": "k01", "text": "..."}` (chạy lại không đổi gì, mã đã có được giữ); `liet-ke` in bảng Mã, Cảnh, Thông tin cho agent kiểm chứng; `kiem` đối chiếu `scenes.json` với bảng trong `kiem-chung.md` (tìm cột theo tên) và thoát mã 1 khi: claim không có dòng (THIEU), dòng không có claim (MO-COI), dòng còn `Cần sửa`, `Không kiểm chứng được` hoặc mã `moi` (CHUA-XU-LY), dòng `Đã bỏ` mà claim còn (DA-BO), dòng `Đúng` mà câu claim đã bị sửa sau khi kiểm (LECH-CAU), dòng `Đúng` hoặc `Đã sửa` thiếu nguồn hoặc trích đoạn (THIEU-NGUON), kết luận ngoài năm giá trị (KHONG-HIEU). Cảnh báo, không chặn: trích đoạn dài hơn 25 chữ; cảnh có chữ số mà không có claim. Script không biết nguồn có thật hay trích đoạn có đúng không.
- `agents/kiem-chung.md`: bảng thêm cột đầu `Mã`; chép nguyên văn câu claim vào cột Thông tin; khẳng định tìm thêm ghi Mã `moi`. `SKILL.md` bước 2 (gán mã, `liet-ke`, đổi kết luận thành `Đã sửa` hoặc `Đã bỏ` khi áp sửa đổi, chạy `kiem` trước cổng 1) và bước 3; `agents/qa.md` nhận kết quả `kiem`. `kiem-chung.md` của dự án đã làm bằng bản cũ (không có cột Mã) cần thêm cột này trước khi chạy `kiem`.
- Chế độ video có sẵn (`so_khang_dinh.py`) không đổi.
- Đã chạy thử với dữ liệu mẫu: `gan` hai lần, `liet-ke`, `kiem` trước khi xử lý (bắt CHUA-XU-LY cho `Cần sửa`, `Không kiểm chứng được` và `moi`, MO-COI, cảnh báo cảnh có số không có claim), sau khi xử lý (bắt LECH-CAU khi claim bị sửa sau kiểm), và trạng thái khớp (thoát mã 0, đếm Đúng, Đã sửa, Đã bỏ). Chưa chạy trên một đợt kiểm chứng thật của agent: chưa biết agent có giữ đúng định dạng bảng và chép nguyên văn câu claim hay không; lần chạy video thật đầu tiên cần xem điểm này.

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
