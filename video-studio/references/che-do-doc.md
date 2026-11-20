# Chế độ đọc văn bản (truyện, tài liệu)

Dùng cho hồ sơ `profiles/doc-van-ban.md`: người dùng gửi văn bản, studio đọc thành tiếng bằng VieNeu. Không có kịch bản mới, không kiểm chứng nguồn, không dựng hình. Script: `scripts/doc_van_ban.py`; lồng tiếng dùng lại `scripts/tts.py`.

## Quy trình

1. **Bước 0.** Chuẩn hóa brief: file, khoảng chương, giọng, tốc độ, có cần `.srt` không. Chạy `setup.sh` (không cần `--dich`).
2. **Tách và làm sạch** (`doc_van_ban.py tach NGUON DU_AN --chuong 1-3`). Script:
   - trích văn bản (PDF qua `pdftotext`, `.docx` đọc thẳng XML, `.txt`, `.md`);
   - bỏ dòng quảng cáo hoặc đường dẫn ngắn (ví dụ tên trang), dãy `***`, ký hiệu trang trí (loại `So` của Unicode), đường kẻ trang trí; mọi thứ đã bỏ được đếm vào `cach-doc.md`;
   - tìm tiêu đề `Chương N: ...`. Tiêu đề mà phần thân dưới 200 ký tự bị coi là mục lục, không thành chương. Không có tiêu đề chương nào thì cả văn bản là một chương `Toàn văn`;
   - nối các dòng bị ngắt cứng thành đoạn: dòng ngắn kết bằng dấu câu, hoặc dòng thoại mới (mở bằng `“`, `—`, `-`), kết thúc đoạn;
   - gom đoạn thành cảnh tối đa 700 ký tự (đoạn dài hơn thì cắt theo câu). Cảnh đầu của chương là tiêu đề; cảnh thân đầu tiên nghỉ 0,8 giây sau tiêu đề. Các đoạn trong một cảnh cách nhau một dòng trống để VieNeu nghỉ theo ngắt đoạn;
   - ghi `chuong-NNNN/scenes.json` (cùng định dạng `tts.py`, gồm `voice`, `speed`), `chuong-NNNN/van-ban.txt`, `muc-luc.json`, `cach-doc.md`.
3. **Cách đọc.** `cach-doc.md` liệt kê chỗ dễ đọc sai: chữ Hán, viết tắt in hoa, chữ lẫn số, chữ Latin lạ (có f, j, w, z). Muốn đổi thì ghi `chữ => cách đọc` mỗi dòng vào `DU_AN/cach-doc.txt` (khớp nguyên từ, phân biệt hoa thường), chạy lại `tach`. Cách đọc chỉ áp vào `scenes.json`; `van-ban.txt` giữ nguyên chữ gốc. `tts.py` có vân tay theo từng cảnh nên chỉ đọc lại cảnh có chữ đổi.
4. **Lồng tiếng và xuất** (`doc_van_ban.py doc DU_AN --chuong 1-3 [--srt]`): chạy `tts.py` cho từng chương, đổi `voiceover.wav` sang MP3 mono 96 kbps, chuẩn hóa `loudnorm` về -16 LUFS, ghi `ra/NNNN-ten-chuong.mp3` và `ra/danh-sach.m3u`. `--srt` ghi `.srt` theo câu; mốc là ước lượng, chia thời lượng của cảnh theo số ký tự mỗi câu.
5. **Giao.** Gửi MP3 các chương đã đọc kèm `cach-doc.md`; liệt kê chỗ studio tự quyết cách đọc.

## Số, ngày, đơn vị, viết tắt

VieNeu tự chuẩn hóa văn bản trước khi đọc (đo bằng `vieneu_utils.phonemize_text.normalize_to_chunks_v3_with_gaps`, VieNeu 3.8.4): "2024" thành "hai nghìn không trăm hai mươi bốn", "3,5 mg/dL" thành "ba phẩy năm mi li gam trên đê xi lít", "10:30 ngày 5/6/2026" thành giờ, ngày, tháng, năm; "HCDC" đọc theo chữ cái. Vì vậy script không tự đổi số hay viết tắt. Chưa kiểm bằng tai cách đọc của từng giọng; bảng cách viết riêng ở `references/giong-doc.md`.

Chữ `***` (từ bị che trong bản gốc) VieNeu đọc là "sao sao sao", nên script bỏ dãy này và ghi số lần vào `cach-doc.md`.

## Giới hạn và số đo

- Số đo (2026-11-20, 2 lõi CPU, VieNeu int8, giọng Hải Đăng, tốc độ 1.0): xem mục "Chạy thử" trong CHANGELOG của phiên bản này.
- Quyển rất dài (ví dụ hơn 2000 chương) không đọc một lần: chọn khoảng chương. Thời gian đọc xấp xỉ thời lượng âm thanh nhân với hệ số đo được.
- Tên riêng, từ Hán Việt đọc theo phiên âm mặc định của VieNeu; chỗ đọc sai ghi vào `cach-doc.txt`.
- Nhiều giọng theo nhân vật chưa làm: một chương một giọng. Muốn dùng, thêm trường `voice` cho cảnh trong `scenes.json` (cơ chế của `tts.py`, quy tắc một nhân vật một giọng như hồ sơ `ke-chuyen.md`).
- Video chữ chạy theo lời chưa có script riêng ở chế độ này.
- Văn bản là của người dùng, chỉ để nghe riêng; studio không đăng tải.
