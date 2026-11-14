# Video-Studio

Mã nguồn skill **video-studio** cho Claude: studio sản xuất video tiếng Việt nhiều agent (ý tưởng, biên kịch, kiểm chứng, lồng tiếng VieNeu, dựng hình HyperFrames, QA, metadata), giao gói MP4 16:9 và 9:16, phụ đề .srt, metadata, thumbnail để tự đăng YouTube và TikTok.

Sáu kiểu hình:
- `2d`: chữ và biểu tượng (mặc định)
- `line-art`: dàn 12 nhân vật nét mực người Việt đã khóa (`video-studio/references/nhan-vat-line-art.md`)
- `chibi`: cùng dàn nhân vật đó vẽ kiểu hoạt hình đầu to nhìn chính diện, viền sticker, biểu cảm, nhép miệng theo lời đọc (`video-studio/references/nhan-vat-chibi.md`)
- `ve-tay`: mỗi cảnh một bức tranh minh họa (người dùng tạo bằng công cụ tạo ảnh AI theo câu lệnh studio viết) hiện dần theo vệt cọ, có bàn tay cầm bút (`video-studio/references/ve-tay.md`)
- `ve-net`: bút vẽ từng nét thật (đường thẳng, vòng tròn, tia sáng, gạch chéo, chữ viết ra) bằng code, không cần ảnh, hợp mọi chủ đề (`video-studio/references/ve-net.md`)
- `3d`: nhân vật 3D kiểu The Sims (Quaternius, `video-studio/references/nhan-vat-3d.md`)

## Cấu trúc

```
video-studio/          thư mục skill (đúng như được cài vào claude.ai)
  SKILL.md             quy trình 8 bước cho điều phối viên
  agents/              thẻ nhiệm vụ từng vai
  profiles/            hồ sơ thể loại
  references/          tài liệu tham khảo
  scripts/             setup, lồng tiếng, ghép phụ đề, render, đóng gói
  templates/           composition HyperFrames (2D, 3D, line-art, chibi, vẽ tay, vẽ nét; dọc và ngang)
  assets/sim3d/        thư viện 3D
  assets/lineart/      thư viện line-art (lineart.js) và nguồn TypeScript (src/), gồm dàn nhân vật (roster.ts)
  assets/chibi/        thư viện chibi (chibi.js) và nguồn TypeScript (src/), dùng chung roster.ts
  assets/vetay/        thư viện vẽ tay (vetay.js, viết thẳng JavaScript, không cần build)
  assets/venet/        thư viện vẽ nét (venet.js, viết thẳng JavaScript, không cần build)
tools/
  build_lineart.sh     build lại lineart.js từ nguồn
  build_chibi.sh       build lại chibi.js từ nguồn
  mocap/               bvh2que.py và catalog.json: chuyển clip mocap CMU thành động tác cho chibi tay chân que
  package_skill.sh     đóng gói zip để tải lên claude.ai
  publish_voice_models.sh  đăng mô hình giọng đọc lên Release (Actions tự chạy)
  publish_characters.sh    đăng nhân vật 3D lên Release (Actions tự chạy)
```

## Cài và cập nhật skill

1. Tải `video-studio.zip` ở mục [Releases](../../releases/tag/latest) (GitHub Actions tự đóng gói mỗi lần `main` đổi), hoặc chạy `bash tools/package_skill.sh`.
2. Vào claude.ai > Settings > Skills, tải zip lên để thay bản cũ. Bản mới có hiệu lực ở các cuộc chat mở sau đó.

## Ghi công

- Thư viện nét vẽ line-art: [JDhruv14/line-art-animation](https://github.com/JDhruv14/line-art-animation), MIT (`video-studio/assets/lineart/LICENSE-line-art-animation.txt`).
- Quy tắc viết tween GSAP (`video-studio/references/gsap.md`): rút và chuyển thể từ [greensock/gsap-skills](https://github.com/greensock/gsap-skills) (commit `aed9cfd`), MIT, Copyright (c) 2026 GreenSock (`video-studio/references/LICENSE-gsap-skills.txt`). Chỉ là tài liệu hướng dẫn, không chép mã vào skill.
- Nhân vật chibi: đồ họa tự vẽ bằng code trong repo này, không dùng thư viện hay hình của bên thứ ba.
- Nhạc nền (`scripts/nhac_nen.py`): studio tự sáng tác bằng code (tổng hợp âm thanh bằng numpy), không dùng nhạc, mẫu âm thanh hay thư viện nhạc bên ngoài.
- Động tác mocap của chibi tay chân que (`play`): chuyển động từ [CMU Graphics Lab Motion Capture Database](http://mocap.cs.cmu.edu), bản BVH của Bruce Hahne chép tại [una-dinosauria/cmu-mocap](https://github.com/una-dinosauria/cmu-mocap) (ghim commit, kích thước và sha256 từng file trong `tools/mocap/catalog.json`). Điều khoản CMU: dùng tự do cho nghiên cứu và sản phẩm thương mại, không được bán lại dữ liệu kể cả ở dạng đã chuyển đổi. "The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217." Repo chỉ lưu clip 2D đã chuyển (`assets/chibi/src/mocap-clips.ts`), không lưu file BVH.
- Tiếng bút của kiểu `ve-net` (`scripts/tieng_but.py`): studio tự tổng hợp bằng code (nhiễu lọc bằng numpy), không dùng mẫu âm thanh bên ngoài. Ý tưởng "mỗi nét có tiếng" tham khảo style Whiteboard Explainer của [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar); không chép mã hay tài liệu của họ.
- Hiệu ứng vẽ tay và bàn tay cầm bút: đồ họa tự vẽ bằng code trong repo này. Tranh của từng video do người dùng tạo, không lưu trong repo.
- Nét vẽ, chữ viết ra và bàn tay cầm bút của kiểu `ve-net`: đồ họa tự vẽ bằng code trong repo này, không dùng thư viện hay hình của bên thứ ba.
- Nhân vật 3D: [Quaternius Ultimate Animated Character Pack](https://quaternius.com/packs/ultimatedanimatedcharacter.html), CC0 1.0 (file giấy phép trong gói ghi CC0 1.0 Universal). Bản chép nguyên vẹn nằm ở Release `quaternius-characters-v1` (không lưu trong git), danh mục và sha256 ở `video-studio/assets/sim3d/characters.json`, cấu hình dàn diễn viên ở `video-studio/assets/sim3d/cast.json`.
- Giọng đọc: [pnnbao-ump/VieNeu-TTS-v3-Turbo](https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo) (dự án gốc [pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS)) và [OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX](https://huggingface.co/OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX), Apache-2.0. Bản chép nguyên vẹn nằm ở Release `vieneu-v3-turbo-61b85e3` (không lưu trong git), danh mục và sha256 ở `video-studio/assets/voice-models.json`.
