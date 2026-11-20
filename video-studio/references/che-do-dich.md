# Chế độ dịch video (phụ đề, thuyết minh)

Tài liệu tham khảo của `SKILL.md`. Dùng khi người dùng gửi một video nói tiếng nước ngoài và nhờ dịch sang tiếng Việt: làm phụ đề, hoặc thuyết minh. Hồ sơ thể loại: `profiles/dich.md`. Không dựng hình mới.

Bản hiện tại làm trọn được **phụ đề**. Thuyết minh (lồng tiếng Việt theo mốc, giữ tiếng gốc nhỏ lại) chưa có script: nếu brief cần thuyết minh, báo người dùng và chỉ làm phụ đề, hoặc dùng `ghep_loi_video_co_san.py` của chế độ video có sẵn với lời Việt đã dịch (tiếng gốc khi đó bị thay hẳn, chưa giữ nhỏ lại được).

## Đầu vào

- File video. Workspace không tải được từ youtube.com (thử ngày 2026-11-18, kết nối bị chặn), nên người dùng tải về trước rồi gửi file.
- Ngôn ngữ gốc: mặc định tự nhận dạng; người dùng biết trước thì ghi `--ngon-ngu`.
- Nguồn video gốc: không ghi trong `credits.md` khi người dùng đã nói tự chịu trách nhiệm về quyền sử dụng; vẫn ghi công cụ (Whisper, VieNeu nếu thuyết minh).

## Môi trường

`bash SKILL/scripts/setup.sh --dich`: dựng như thường lệ, cài thêm `faster-whisper`, `ctranslate2`, `av` (`av` mới hơn 17.0.0 làm `faster_whisper` lỗi `metadata_errors`), `sherpa-onnx` và `opencc` cho bước kiểm chéo bằng FireRedASR2, `rapidocr` cho bước đọc chữ trên hình (ghim phiên bản trong `setup.sh`; `--firered` nay giống `--dich`). Mô hình Whisper tải lúc chạy bằng `scripts/lay_whisper.py` (GitHub Release của repo, dự phòng huggingface, kiểm sha256): bản `medium` khoảng 1,5 GB, tải một lần mỗi workspace. FireRedASR2 (khoảng 1,2 GB) tải bằng `scripts/lay_asr.py` khi chạy kiểm chéo lần đầu. Bản `large-v3` (`--ban large-v3`, khoảng 3,1 GB) là tùy chọn; FireRedLID (`setup.sh --lid`) là tùy chọn.

## Quy trình

0. **Chép video vào dự án giữ nguyên tên gốc** (không đổi thành `goc.mp4`): tên file ra là `<tên>-phu-de-vi.mp4`, nên đổi tên thì người dùng mất dấu file của mình. Các lệnh dưới ghi `goc.mp4` chỉ là ví dụ.
1. **Chép lời gốc**: `python3 SKILL/scripts/chep_loi_goc.py goc.mp4 PROJECT`. Mặc định Whisper `medium`, bật lọc khoảng lặng (VAD). Ra `PROJECT/dich/chep-goc.json` và `chep-goc.md`.
   - Ngôn ngữ: cắt khúc 30 giây, chỉ dùng khúc có ít nhất 3 giây tiếng nói, nhận dạng trên mọi ngôn ngữ. Script in `[CAN HOI]` khi các khúc không cùng ngôn ngữ, xác suất trung bình dưới 0,8, cách ngôn ngữ thứ hai dưới 0,3, hoặc ngôn ngữ ngoài danh sách đã thử (en, zh, vi). Khi đó dừng hỏi người dùng rồi chạy lại với `--ngon-ngu`.
   - Mốc đoạn lấy theo mốc từ đầu và từ cuối (cộng 0,4 giây), vì mốc đoạn gốc của Whisper có thể trùm cả khoảng nhạc sau câu.
1b. **Kiểm chéo bằng FireRedASR2** (mặc định khi ngôn ngữ là `zh` hoặc `en`; `chep_loi_goc.py` in sẵn lệnh ở dòng `[TIEP]`): `python3 SKILL/scripts/chep_loi_firered.py goc.mp4 PROJECT`. Ra `dich/chep-firered.md`: dòng `KHÁC` kèm đúng chữ hai bên nghe khác nhau, và lời FireRed nghe được ở khoảng Whisper không có đoạn nào. Xem mục "Kiểm chéo bằng FireRedASR2". Ngôn ngữ khác thì bỏ bước này (FireRedASR2 chỉ chép tiếng Trung, tiếng Anh).
1c. **Đọc chữ trên hình** (mọi ngôn ngữ; sau bước 1b nếu có, để bảng ghi kèm chỗ `KHÁC` của FireRed): `python3 SKILL/scripts/chu_tren_hinh.py goc.mp4 PROJECT`. Ra `dich/chu-tren-hinh.md`: đoạn Whisper khác phụ đề cứng cùng ngôn ngữ, và các dòng chữ khác (thực đơn, biển hiệu, tên riêng). Bắt được lỗi hai mô hình cùng nghe sai mà kiểm chéo bỏ lọt. Video không có chữ thì script dừng sau 5 khung thăm dò. Xem mục "Đọc chữ trên hình".
2. **Cổng duyệt bản chép gốc** (dừng chờ người dùng): `python3 SKILL/scripts/phu_de_dich.py duyet-chep PROJECT`. Script gộp ba bảng (Whisper có cờ, `KHÁC` của FireRed, chỗ khác chữ trên hình) thành **một** bảng `dich/duyet-chep.md` chỉ gồm chỗ cần xem, mỗi chỗ kèm lệnh áp sẵn; thêm lời FireRed nghe được ở khoảng trống (kèm lệnh `them`), khoảng không có lời, chữ khác trên hình (bỏ phụ đề chữ Hán khi lời gốc không phải chữ Hán), và tạo `dich/ban-dich.json` nếu chưa có. Gửi bảng này (không gửi ba bảng riêng); `chep-goc.md`, `chep-firered.md`, `chu-tren-hinh.md` vẫn còn để xem chi tiết khi cần.
   - Người dùng chọn bên nào ở từng chỗ; điều phối áp đúng lựa chọn đó, không tự chọn:
     - `phu_de_dich.py sua PROJECT d002 --thay "bend=spend"` (thay theo cả từ, không phân biệt hoa thường, giữ chữ hoa đầu từ; chữ Hán thay chuỗi; lặp `--thay` được; `--thay "也="` để xóa) hoặc `--goc "cả câu mới"`. Lời Whisper cũ lưu ở `goc_whisper`, `chep-goc.json` giữ nguyên.
     - `phu_de_dich.py them PROJECT 112.9 114.9 "Here's some ASMR typing."`: thêm đoạn Whisper bỏ sót (chặn khi chồng đoạn khác; mốc lấy theo bảng, sửa cho sát câu nếu nghe được).
   - Không áp thì lời gốc sai vẫn vào phụ đề song ngữ và bản giao (đã gặp: phụ đề song ngữ hiện "Bend the day...", "port panini" dù bản dịch đúng).
   - **Luôn hỏi người nói ở cổng này**, kể cả khi bước 0 đã bỏ qua câu hỏi của hồ sơ: video có mấy người, ai nói câu nào, ai nói với ai. Xưng hô trong bản dịch phụ thuộc vào đây, Whisper và FireRed đều không tách người nói. Người chỉ nghe tiếng ngoài khung hình (người quay) cũng là một người nói. Gán bằng `phu_de_dich.py nguoi PROJECT d001-d003=be d004-d007=me` (mã ngắn; video một người nói thì bỏ qua) để lượt kiểm dịch đọc được, không chỉ để trong chat.
   - `nghi-bia`: câu Whisper hay tự thêm ở đoạn không có lời ("Thanks for watching", lặp chữ, xác suất không có lời cao). Câu bịa thì ghi `"bo": true` (hoặc `sua --goc` nếu nghe được lời thật).
   - `tin-thap`: nghe chưa chắc (avg_logprob dưới -0,7).
   - Khoảng không có lời dài hơn 2 giây: VAD có thể đã bỏ câu nói nhỏ trên nền nhạc hay tiếng gõ phím; nhắc người dùng nghe lại.
3. **Gộp mảnh câu, rồi dịch**:
   - `python3 SKILL/scripts/phu_de_dich.py goi-y-gop PROJECT goc.mp4` in lệnh `gop` cho các chuỗi mảnh liền nhau (cách dưới 0,3 giây), cùng người nói, có mảnh dưới 1,2 giây hoặc câu chưa kết thúc (lời có dấu câu), tổng tối đa 6 giây và không quá thời gian đọc hết hai dòng phụ đề (khổ dọc 1080 rộng: khoảng 3,6 giây). Đọc lại từng gợi ý, chỉ chạy lệnh gộp những mảnh cùng một câu hoặc một ý. `gop` chặn khi khác người nói (trừ `--khac-nguoi-noi`) hoặc không liền nhau. **Gộp trước khi dịch**: Whisper cắt câu thành mảnh (clip Trung 27,6 giây: 19 đoạn, 9 đoạn dưới 1 giây), dịch từng mảnh rồi mới gộp thì phải dịch lại. Đo 2026-11-20: vlog Anh 29 đoạn còn 19, cảnh báo của `kiem` từ 8 xuống 0; clip Trung 19 đoạn còn 14, cảnh báo từ 18 xuống 3, và không còn gợi ý gộp câu của mẹ vào câu của bé như bản cũ.
   - Dịch (điều phối, hoặc agent biên kịch, model sonnet) vào một file văn bản, mỗi dòng `ID<TAB>bản dịch` (hoặc `ID | bản dịch`; dòng bắt đầu `#` bỏ qua), rồi `phu_de_dich.py nhap PROJECT dich.tsv`. Không sửa JSON tay. `nhap` chặn mã không có hoặc đã gộp vào đoạn khác, in các đoạn còn thiếu.
   - Dịch ý, giữ đúng số, tên riêng, phủ định, ai nói với ai. Xưng hô theo quan hệ người nói (vlog một người: "mình"; cha mẹ nói với con: "bố/mẹ" và "con").
   - Tên riêng viết theo cách người Việt quen đọc ("Đại học Melbourne", không "uni melb"). Tên người Trung Quốc viết theo âm Hán Việt (胡一天: "Hồ Nhất Thiên").
   - Hồ sơ sức khỏe, thủ tục: số liệu, khuyến cáo trong lời gốc vẫn kiểm chứng nguồn ngoài như quy trình thường. Hồ sơ khác: chỉ kiểm dịch trung thực, ghi "theo lời người nói" khi cần.
4. **Kiểm bản dịch**: `python3 SKILL/scripts/phu_de_dich.py kiem PROJECT goc.mp4`. Lỗi chặn: thiếu bản dịch, đoạn chồng nhau, vượt thời lượng, chữ số trong lời gốc mất ở bản dịch (3.5 và 3,5 coi là một số; 1,000 và 1.000 coi là một nghìn), quá 2 dòng, chữ chưa NFC. Cảnh báo: đọc nhanh hơn `--cps` (mặc định 15 ký tự mỗi giây, không tính khoảng trắng, lấy theo `doc_chu.py`, chưa đo riêng cho phụ đề tiếng Việt), đoạn hiện dưới 1 giây, đoạn gốc có cờ.
   - Đoạn đọc nhanh tự được kéo dài thời gian hiện vào khoảng trống phía sau, tối đa `--keo-dai` giây (mặc định 1,5), cách đoạn sau 0,1 giây. Vẫn nhanh thì rút gọn bản dịch hoặc gộp.
   - Đoạn ngắn nằm sát đoạn sau (cách dưới 0,2 giây): cùng người nói thì `kiem` in sẵn lệnh `gop`; khác người nói thì chỉ báo rút gọn (không gộp lời hai người vào một dòng). Hỏi đáp nhanh kiểu "不知道" 0,48 giây: dịch gọn nhất ("Không biết.") vẫn 20,8 ký tự mỗi giây; hỏi người dùng giữ riêng hay rút ở cổng duyệt bản dịch.
   - **Lượt kiểm dịch độc lập** (agent khác người dịch, sonnet; opus với sức khỏe, thủ tục) đọc `dich/ban-dich.md` (tạo ở bước 5) hoặc `ban-dich.json`: sai nghĩa, sót ý, sai số, sai người nói, xưng hô. **Không bỏ lượt này kể cả với clip ngắn** (đã có job 6 đoạn bị bỏ qua). Ghi kết quả vào `dich/kiem-dich.md` theo mẫu cố định, để trọng tài chỉ nhận các dòng bất đồng:

     | Mã | Loại (nghĩa, sót, số, người nói, xưng hô, văn) | Bản dịch hiện tại | Đề xuất | Người dịch đồng ý? |
     |---|---|---|---|---|

     Người dịch trả lời cột cuối; dòng "không" mới gửi trọng tài. Áp đề xuất được chấp nhận bằng `nhap` (file chỉ chứa các dòng sửa).
5. **Cổng duyệt bản dịch** (dừng chờ người dùng): `python3 SKILL/scripts/phu_de_dich.py bang PROJECT goc.mp4` tạo `dich/ban-dich.md` (mã, giây, người nói, gốc, dịch, ghi chú: lời gốc đã sửa kèm lời Whisper cũ, đoạn thêm tay, đoạn gộp, cảnh báo của `kiem`). Gửi bảng này kèm tóm tắt `kiem-dich.md`. Duyệt xong thì không đổi nội dung nữa.
6. **Ghi phụ đề**: `python3 SKILL/scripts/phu_de_dich.py ghi PROJECT goc.mp4`. Ra `output/phu-de-vi.srt`, `output/<tên>-phu-de-vi.mp4` (giữ độ phân giải, chép nguyên tiếng gốc) và bảng khung kiểm `dich/qa-phu-de.png`.
   - Xem bảng khung kiểm trước khi giao. Video gốc đã có phụ đề cứng (ví dụ song ngữ Trung Anh ở đáy) thì chữ dịch chồng lên: chạy lại với `--che-day 0.2` (làm mờ dải đáy cao 20% khung rồi ghi phụ đề dịch lên đó) hoặc `--vi-tri tren`.
   - `--song-ngu`: dòng gốc nhỏ dưới dòng dịch (để học ngoại ngữ). Dòng gốc lấy từ `ban-dich.json` (đã sửa ở bước 2). Dòng gốc dài được ngắt dòng riêng (cỡ chữ 0,7 lần bản dịch) và dòng dịch tự đẩy lên theo số dòng gốc; vẫn xem bảng khung kiểm.
7. **Giao**: video có phụ đề, `phu-de-vi.srt`, `ban-dich.md` (bảng gốc đã sửa và dịch, thay cho `chep-goc.md` vốn là bản Whisper chưa sửa). Nêu chỗ đã sửa lời gốc (cột Ghi chú), câu chưa chắc nghĩa, đoạn VAD bỏ mà chưa ai nghe lại.

## Kiểm chéo bằng FireRedASR2 (mặc định với tiếng Trung, tiếng Anh) và chép bổ sung

Từ 1.21.0, FireRedASR2 là bước kiểm chéo mặc định (bước 1b) cho tiếng Trung và tiếng Anh: hai mô hình khác họ ít sai cùng một chỗ, nên chỗ hai bên nghe khác nhau là chỗ đáng nghe lại. `large-v3` vẫn là tùy chọn, không làm mặc định (đo 2026-11-20: chậm hơn `medium`, mốc từ lệch hơn, tiếng Trung không đúng hơn). Cả hai mô hình chép nguyên bản lên Release riêng `asr-large-v3-firered2-edaa852-374cff1` (danh mục, revision và sha256 ở `assets/asr-models.json`; `model.bin` của large-v3 chia hai phần vì mỗi file trong release phải dưới 2 GiB, `lay_asr.py` ghép lại và kiểm sha256).

- **Whisper large-v3**: `python3 chep_loi_goc.py VIDEO PROJECT --ban large-v3`. Cùng cách chạy như `medium`, chỉ đổi mô hình.
- **FireRedASR2-AED int8 (ONNX)**: `bash setup.sh --dich` (đã gồm `sherpa-onnx`, `opencc` bản ghim), rồi `python3 chep_loi_firered.py VIDEO PROJECT` sau khi đã có `dich/chep-goc.json`. Ra `dich/chep-firered.md` và `chep-firered.json`: bảng đối chiếu từng đoạn Whisper, FireRed nghe cả cụm (cửa sổ tối đa 30 giây) và FireRed nghe đoạn cắt rời. Dòng `KHÁC` là đoạn mà lời Whisper khác bản chép FireRed của cả cụm: tách từ (tiếng Anh theo từ, tiếng Trung theo chữ), bỏ dấu câu, đổi cả hai bên về chữ giản thể bằng OpenCC (`t2s`), vì Whisper hay chép tiếng phổ thông bằng phồn thể còn FireRed ra giản thể, rồi gióng hàng lời Whisper của cả cụm với bản FireRed; chỗ khác gán cho đoạn Whisper chứa nó (FireRed nghe thêm từ ở ranh giới hai đoạn thì gán cho đoạn trước). Cột "Chỗ khác" ghi `Whisper / FireRed` (ví dụ `bend / spend`). So theo từ chứ không theo chuỗi chữ liền: trước 1.21.0 so theo chuỗi liền nên "bend" lọt vì nằm trong "spend". Hai bên chỉ khác cách tách từ ("beef balls" / "beefballs") thì coi là khớp.
  - Lời trong khoảng trống: khoảng từ 2 giây trở lên không có đoạn Whisper nào (`khoang_trong` của `chep-goc.json`) được cho FireRed nghe lại theo cửa sổ 8 giây; có lời thì ghi ở mục riêng cuối `chep-firered.md` (trường `khoang_trong` của JSON). Bỏ kết quả `<sil>`, chỉ có tiếng đệm (嗯, 呃) hoặc trợ từ, hoặc lặp một hai từ từ 6 lần trở lên. Cửa sổ dài hơn làm FireRed hỏng: trên đoạn gõ phím 30 giây chỉ ra `<sil>`, cửa sổ 14 giây ra câu đúng kèm "LA LA LA..." lặp; 6 đến 10 giây ra đúng câu. Bảng vẫn giữ nguyên chữ của từng mô hình. Chưa quy đổi số: "3" và "三" vẫn báo `KHÁC`. Đoạn chỉ khác trợ từ ở cuối câu Whisper (啊, 呀, 吧, 呢, 哦, 嘛, 啦, 哈, 呗, 哟, 嘿, 诶) thì ghi "trợ từ" thay cho `KHÁC` (trường `chi_tro_tu` trong JSON): không đổi nghĩa, không cần nghe lại; chỉ bỏ trợ từ ở cuối, không bỏ giữa câu. Không ghi đè `chep-goc.json`: gửi bảng này kèm bản chép gốc ở cổng duyệt, người dùng quyết định lấy bên nào.
  - Chỉ hỗ trợ tiếng Trung (phổ thông, hơn 20 giọng địa phương) và tiếng Anh; ngôn ngữ khác thì script dừng. Theo tác giả, FireRedASR2-AED đạt CER trung bình 3,05% trên 4 bộ kiểm tra tiếng Trung phổ thông (bảng trong [thẻ model](https://huggingface.co/FireRedTeam/FireRedASR2-AED), báo cáo [arXiv:2603.10420](https://arxiv.org/abs/2603.10420)); số này không so với Whisper.
  - Dùng bản ONNX int8 của [csukuangfj2](https://huggingface.co/csukuangfj2/sherpa-onnx-fire-red-asr2-zh_en-int8-2026-02-26), chạy bằng `sherpa-onnx` vì `download.pytorch.org` bị chặn ở workspace (HTTP 403 từ proxy, thử 2026-11-19) nên không cài được PyTorch cho mã gốc. Đây là bản đóng gói của người khác, thẻ model không ghi giấy phép; mô hình gốc `FireRedTeam/FireRedASR2-AED` là Apache-2.0 (xem README, mục Ghi công).
  - Đoạn cắt rời hay lẫn chữ của đoạn bên cạnh và có thể ra khác cụm, nên cột đó chỉ để tham khảo.
- Số đo (2026-11-19, workspace 2 lõi CPU, không GPU, video 27,6 giây tiếng Trung, mô hình đã có trên đĩa): `--ban large-v3` 34 giây (có VAD, chỉ định `--ngon-ngu zh`); `chep_loi_firered.py` 39 giây, gồm 1 cụm và 19 đoạn.
- Giới hạn đã thấy trên clip đó: ba lần chạy Whisper (medium, large-v3 có VAD, large-v3 không VAD) ra ba bản khác nhau ở cùng một cụm ba chữ, và `large-v3` không chắc đúng hơn `medium`. FireRedASR2 ra bản mạch lạc hơn khi nghe cả cụm, nhưng cắt rời từng đoạn lại cho chữ khác (một cụm "头发" khi nghe liền, "豆腐" khi cắt rời). Chưa có người biết tiếng Trung nghe kiểm lại: coi chỗ `KHÁC` là chỗ cần nghe lại, không phải đáp án.
- Số đo kiểm chéo (2026-11-20, 2 lõi CPU, mô hình đã có trên đĩa, Whisper `medium`), so với phụ đề cứng của chính video khi có:
  - Vlog tiếng Anh 143 giây (4 cụm, 29 đoạn): 5 đoạn `KHÁC`, mỗi chỗ đều có một bên sai so với phụ đề: `vlog / blog`, `bend / spend`, `decided / decide`, `randomly / readily`, `napoli / naple` (phụ đề ghi "Naples"). Khoảng trống: FireRed nghe được "here's some asmr typing" ở 112,9 đến 120,9 giây mà Whisper bỏ. Không có cờ báo nhầm. Bỏ lọt: "port panini" (phụ đề ghi "pork"), vì cả hai mô hình cùng nghe "port": kiểm chéo không bắt được lỗi hai bên cùng sai, vẫn phải đối chiếu chữ trên hình. Chạy 139 giây.
  - Hội thoại tiếng Trung 27,6 giây (1 cụm, 19 đoạn): 6 đoạn `KHÁC`: `兜巴 / 头发` (hai lần), `吹 / 伺候`, `给你的 / 跟人家`, `和 / 合`, và `嗯` FireRed nghe thêm. Chưa có bản chuẩn: bản FireRed liền mạch hơn (美女吹个头发吧, 不用你伺候我了), nhưng chưa có người biết tiếng Trung nghe kiểm. Chạy 39 giây.
- Clip thứ hai (2026-11-19, hội thoại 18,6 giây tiếng Trung, một bé trai và một người nói ngoài khung hình): 2 trong 6 đoạn báo `KHÁC` chỉ vì 啊 và 呀, nên đã thêm nhãn "trợ từ". Tên riêng 胡一天 được cả Whisper `medium` và FireRed chép giống nhau: tên riêng mà hai mô hình chép trùng thì đáng tin hơn, nên FireRed vẫn đáng chạy khi video có tên riêng dù không có cờ `tin-thap`. Cột đoạn riêng còn chép cả tiếng cười (嘿嘿嘿, 哈哈) mà bản nghe cả cụm bỏ đi: không đưa vào phụ đề, nhưng là gợi ý ai đang cười khi gán người nói. Chưa đo trên nhiều video, chưa thử tiếng Anh, tiếng Quảng Đông hay video dài trên 5 phút.

## Nhận dạng ngôn ngữ bằng FireRedLID (tùy chọn `--lid`)

Dùng khi Whisper báo `[CAN HOI]` về ngôn ngữ, hoặc video có thể là ngôn ngữ ngoài danh sách đã thử (tránh đưa nhầm vào `chep_loi_firered.py`, vốn chỉ chép tiếng Trung và tiếng Anh). Không bật mặc định vì phải cài torch.

- `bash setup.sh --lid` (cài mọi thứ của `--dich`, thêm `torch`, `kaldiio`, `kaldi_native_fbank` bản ghim; torch từ pypi kèm các gói CUDA, khoảng 4 GB, dù chỉ chạy CPU), rồi `python3 chep_loi_goc.py VIDEO PROJECT --lid`. Bỏ qua khi đã chỉ định `--ngon-ngu`.
- Mô hình FireRedLID (Apache-2.0) chép nguyên bản lên Release riêng `lid-firered-1bb4d28` (danh mục ở `assets/lid-models.json`; `model.pth.tar` 3,55 GB chia ba phần, `lay_asr.py lid` ghép lại và kiểm sha256). Mã suy luận chép nguyên bản ở `scripts/vendor/fireredlid` (nguồn, commit, sha256 trong `NGUON.md`). Checkpoint nạp bằng `mmap`: nạp theo cách gốc làm tràn RAM ở workspace 7 GB.
- Cách chạy: `nhan_dang_lid.py` chạy tiến trình riêng, trước khi nạp Whisper, trên các khúc có tiếng nói theo VAD (khúc dài cắt tối đa 30 giây, bỏ phần dưới 1 giây). Chỉ tính khúc có độ tin từ 0,8 (khúc gõ phím, nhạc cho kết quả bừa với độ tin thấp), cộng thời lượng theo ngôn ngữ. Ra `dich/lid.json`; tóm tắt ghi ở `chep-goc.json` (`ngon_ngu.lid`) và một dòng trong `chep-goc.md`.
- FireRedLID chọn khác Whisper, hoặc không có khúc nào độ tin từ 0,8, thì `[CAN HOI]`: hỏi người dùng rồi chạy lại với `--ngon-ngu`. Không tự chọn bên nào.
- Số đo (2026-11-20, 2 lõi CPU, mô hình đã có trên đĩa; thời gian chạy LID không gồm nạp mô hình khoảng 7 giây):

| Clip | Whisper medium | FireRedLID | LID chạy |
|---|---|---|---|
| Hội thoại tiếng Trung 27,6 giây | `zh` | `zh` (19,11/26,05 giây tin cậy; khúc 22,5 đến 24,0 giây đoán `en` độ tin 0,21, bị loại) | 8,6 giây |
| Vlog tiếng Anh 143 giây | `en` | `en` (73,83/73,83 giây) | 19,0 giây |
| Clip 16 giây ngoài trời | `jw` 0,67, `[CAN HOI]` | `su` (11,7/11,7 giây) | 2,9 giây |

- Giới hạn: clip 16 giây chưa có người nghe xác nhận là tiếng gì, nên chưa biết Whisper (`jw`) hay FireRedLID (`su`) đúng. Theo tác giả, FireRedLID đạt 97,18% trên FLEURS (82 ngôn ngữ), Whisper 79,41% ([thẻ model](https://huggingface.co/FireRedTeam/FireRedLID)); chưa đo trên nhiều video của mình.

## Đọc chữ trên hình (bước 1c)

Kiểm chéo hai mô hình không bắt được chỗ cả hai cùng nghe sai (vlog thử: cả Whisper lẫn FireRed nghe "port panini", phụ đề cứng ghi "pork panini"). Chữ trên hình là nguồn độc lập thứ ba.

- `chu_tren_hinh.py` dùng [RapidOCR](https://github.com/RapidAI/RapidOCR) 3.10.0 (gói pip `rapidocr`, Apache-2.0), mô hình PP-OCRv6 small của PaddleOCR (Apache-2.0) đi kèm gói, không tải thêm. Nhận được chữ Latin và chữ Hán. Đã thử Tesseract 5.3.4 có sẵn trong workspace trên cùng khung: ra chữ vụn, không dùng được.
- Cách làm: thăm dò 5 khung rải đều trong các đoạn có lời, không thấy dòng chữ nào độ tin từ 0,8 thì dừng. Có chữ thì đọc khung giữa mỗi đoạn Whisper (đoạn dài hơn 4 giây đọc thêm khung 1/4 và 3/4). Mỗi dòng chữ so với lời Whisper của đoạn trước, đoạn này và đoạn sau nối lại, vì phụ đề và đoạn Whisper không cắt cùng chỗ (vlog thử: dòng "...the Naples sauce it just tastes even better" hiện ở khung của đoạn sau, đoạn đó chỉ chứa 5/13 từ của dòng); chỗ khác gán cho đoạn chứa từ Whisper bị thay. Dòng chữ khớp khi trùng ít nhất 3 từ (tiếng Trung 4 chữ) và trùng ít nhất 60% số từ của dòng. Chỉ so phần trùng, chỉ báo chỗ thay thế ngắn (mỗi bên tối đa 3 từ), bỏ chỗ chỉ khác cách tách từ. Cùng cách tách từ với `chep_loi_firered.py`.
- `chu-tren-hinh.md`: bảng đoạn khác chữ (`Whisper / chữ trên hình`, kèm chỗ `KHÁC` của FireRed nếu có), rồi danh sách dòng chữ không khớp đoạn nào (thực đơn, biển hiệu, phụ đề ngôn ngữ khác) để đọc lướt khi sửa tên riêng, món ăn.
- Phụ đề cứng của chính video cũng có thể viết sai hoặc viết khác lời nói (vlog thử: phụ đề ghi "decide", Whisper "decided"; người nói nói gì thì vẫn phải nghe). Chỉ là gợi ý ở cổng duyệt, không tự sửa bản chép.
- Số đo (2026-11-20, 2 lõi CPU, thời gian gồm nạp mô hình):

| Clip | Khung đọc | Kết quả | Thời gian |
|---|---|---|---|
| Vlog tiếng Anh 143 giây, 1280x720, phụ đề cứng Anh và Trung | 31 | 25/29 đoạn có dòng phụ đề khớp; 3 đoạn khác chữ: `port / pork` (cả hai mô hình cùng sai), `decided / decide`, `napoli / naples` (hai chỗ sau FireRed cũng báo). Danh sách chữ có thực đơn quán ("Avocado On Toast", "Beef meatballs, napoli sauce..."): thực đơn ghi "napoli", phụ đề ghi "Naples", nên người duyệt vẫn phải chọn | 37 giây |
| Hội thoại tiếng Trung 27,6 giây, 1080x1920, không phụ đề | 19 | 0 đoạn khớp, 0 báo nhầm (thăm dò thấy 1 chữ lẻ nên vẫn đọc hết) | 37 giây |
| Clip 16 giây ngoài trời, không chữ | 5 | Dừng sau thăm dò | 12 giây |

- Chưa bắt được: chữ chỉ hiện ở khung không đọc (phụ đề đổi nhanh hơn một đoạn Whisper; vlog thử: không có phụ đề cho "Spend the day...", nên `bend` chỉ có kiểm chéo FireRed bắt). Chưa thử chữ viết tay, phụ đề chạy chữ, video tối.

## Phân vai (agent và model)

| Việc | Ai làm | Model |
|---|---|---|
| Chạy `chep_loi_goc.py`, `chep_loi_firered.py`, `chu_tren_hinh.py`, `phu_de_dich.py duyet-chep`, báo số chỗ cần chọn | agent chép lời | haiku |
| Áp lựa chọn của người dùng (`sua`, `them`, `nguoi`), duyệt gợi ý gộp (`goi-y-gop`, `gop`) | điều phối | sonnet |
| Dịch (`ban-dich.json`) | điều phối hoặc agent biên kịch | sonnet |
| Kiểm dịch độc lập (bước 4), ghi `dich/kiem-dich.md` theo mẫu | agent khác người dịch | sonnet; opus khi nội dung sức khỏe, thủ tục |
| Trọng tài: chỉ các dòng `kiem-dich.md` người dịch trả lời "không" | agent thứ ba, chỉ nhận các dòng đó | sonnet; opus khi nội dung sức khỏe, thủ tục |

- Agent chép lời chỉ chạy script và báo lại. Không tự sửa bản chép, không tự chọn giữa Whisper và FireRed: chọn chữ nào cần hiểu ngữ cảnh, có khi phải nhìn chữ trên hình, nên để điều phối và người dùng quyết ở cổng duyệt. Script lỗi (thiếu mô hình, lỗi gói) thì báo lên, không tự sửa môi trường.
- Câu trọng tài vẫn không chắc thì đánh dấu và hỏi người dùng ở cổng duyệt bản dịch.

## Số đo (2026-11-18, workspace 2 lõi CPU, không GPU)

| Clip | Ngôn ngữ nhận dạng | Ghi chú |
|---|---|---|
| Vlog 143 giây, một người nói, nhạc nền, gõ phím | `en` 0,97 (trung bình 4 khúc có lời) | Chép gần đúng hết; sai "Bend/Spend", "port/pork" (sửa nhờ thực đơn trên hình) |
| Hội thoại 30 giây, hai người | `zh` 0,999 (medium) | Không tách người nói; small bịa câu ở đoạn im lặng |
| Clip 16 giây ngoài trời | medium `jw` 0,65, small `id` 0,42 | Ngôn ngữ ngoài danh sách, bản chép tin cậy thấp: không dịch được |

- `chep_loi_goc.py` trên vlog 143 giây (medium, VAD, đã có mô hình): khoảng 42 giây với `--ngon-ngu en`. Lần chạy đầu tự nhận dạng mất khoảng 68 giây, gồm cả tải mô hình medium từ GitHub Release.
- Không bật VAD, medium bịa "Thanks for watching!" ở giây 140 trên đoạn chỉ có tiếng gõ phím; bật VAD thì hết, nhưng mất câu "Here's some ASMR typing." nói nhỏ trên nền gõ phím.
- `phu_de_dich.py ghi` 143 giây 1280x720: khoảng 34 giây (thêm `--che-day`: khoảng 42 giây; đo lại 2026-11-20 với `--song-ngu --che-day 0.2`: 48 giây). Clip 27,7 giây 1080x1920: 20 giây.

## Giới hạn đã biết

- Whisper không tách người nói. Video nhiều người: người dùng gán ở cổng duyệt bản chép.
- Video lẫn hai ngôn ngữ: chỉ chọn được một ngôn ngữ chính cho cả video.
- Chưa thử tiếng Quảng Đông, phương ngữ, tiếng Trung có nhạc nền to.
- Ngưỡng cờ (0,6; 2,4; -0,7) và ngưỡng chắc chắn (0,8; 0,3) lấy theo 3 clip trên, chưa hiệu chỉnh trên nhiều video.
- `faster-whisper.transcribe(đường_dẫn)` lỗi ở workspace (`av.open() got an unexpected keyword argument 'metadata_errors'`): script đọc tiếng bằng ffmpeg ra mảng số rồi mới đưa vào.
- Phụ đề cứng dùng phông Inter có sẵn trong workspace (như `chu_may_chu.py`); máy khác thiếu phông thì libass thay phông khác.
