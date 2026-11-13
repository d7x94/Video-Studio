# Video-Studio

Mã nguồn skill **video-studio** cho Claude: studio sản xuất video tiếng Việt nhiều agent (biên kịch, kiểm chứng, lồng tiếng VieNeu, dựng hình HyperFrames, QA, metadata), giao gói MP4 16:9 và 9:16, phụ đề .srt, metadata, thumbnail để tự đăng YouTube và TikTok.

Ba kiểu hình:
- `2d`: chữ và biểu tượng (mặc định)
- `line-art`: dàn 12 nhân vật nét mực người Việt đã khóa (`video-studio/references/nhan-vat-line-art.md`)
- `3d`: nhân vật 3D kiểu The Sims (Quaternius, `video-studio/references/nhan-vat-3d.md`)

## Cấu trúc

```
video-studio/          thư mục skill (đúng như được cài vào claude.ai)
  SKILL.md             quy trình 8 bước cho điều phối viên
  agents/              thẻ nhiệm vụ từng vai
  profiles/            hồ sơ thể loại
  references/          tài liệu tham khảo
  scripts/             setup, lồng tiếng, ghép phụ đề, render, đóng gói
  templates/           composition HyperFrames (2D, 3D, line-art; dọc và ngang)
  assets/sim3d/        thư viện 3D
  assets/lineart/      thư viện line-art (lineart.js) và nguồn TypeScript (src/)
tools/
  build_lineart.sh     build lại lineart.js từ nguồn
  package_skill.sh     đóng gói zip để tải lên claude.ai
```

## Cài và cập nhật skill

1. Tải `video-studio.zip` ở mục [Releases](../../releases/tag/latest) (GitHub Actions tự đóng gói mỗi lần `main` đổi), hoặc chạy `bash tools/package_skill.sh`.
2. Vào claude.ai > Settings > Skills, tải zip lên để thay bản cũ. Bản mới có hiệu lực ở các cuộc chat mở sau đó.

## Ghi công

- Thư viện nét vẽ line-art: [JDhruv14/line-art-animation](https://github.com/JDhruv14/line-art-animation), MIT (`video-studio/assets/lineart/LICENSE-line-art-animation.txt`).
- Nhân vật 3D: Quaternius Ultimate Animated Character Pack, CC0 (tải khi dựng môi trường, không lưu trong repo).
