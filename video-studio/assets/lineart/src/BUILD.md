# Build lại lineart.js

Nguồn: `lib/` lấy từ github.com/JDhruv14/line-art-animation (commit c43d698, MIT), `cast/` viết cho studio.
`cast/main.ts` + `cast/index.html` là cảnh giới thiệu dàn nhân vật (chạy bằng Vite, không dùng trong HyperFrames).

Bản gốc của skill nằm ở github.com/d7x94/Video-Studio. Sửa nguồn ở đó rồi build:

```bash
bash tools/build_lineart.sh          # ghi đè assets/lineart/lineart.js (esbuild 0.28.2)
bash tools/build_lineart.sh --check  # chỉ kiểm tra lineart.js khớp nguồn
```

Sửa nhân vật: sửa `cast/roster.ts` (đã khóa, chỉ sửa khi người dùng yêu cầu), build lại, chụp thử.
