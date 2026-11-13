#!/usr/bin/env bash
# Tao mot composition HyperFrames tu template cua skill.
# Dung:  bash new_project.sh PROJECT_DIR portrait|landscape [3d|lineart|chibi|vetay]
#   them "3d" de dung canh co nhan vat 3D (Three.js + thu vien sim3d.js)
#   them "lineart" de dung canh co nhan vat net muc (SVG + thu vien lineart.js, dan nhan vat da khoa)
#   them "chibi" de dung canh co nhan vat chibi nhin chinh dien (SVG + thu vien chibi.js, cung dan nhan vat)
#   them "vetay" de dung canh ve tay: tranh hien dan theo vet co, co ban tay cam but (thu vien vetay.js)
# Ket qua: PROJECT_DIR/build/<format>/ voi index.html, gsap.min.js, fonts/ san sang.
set -euo pipefail
source "${STUDIO_HOME:-$HOME/studio}/studio.env"

PROJECT="$1"; FORMAT="$2"; MODE="${3:-2d}"
case "$FORMAT" in portrait|landscape) ;; *) echo "FORMAT phai la portrait hoac landscape"; exit 1;; esac
case "$MODE" in 2d|3d|lineart|chibi|vetay) ;; *) echo "Tham so thu ba chi nhan 3d, lineart, chibi hoac vetay"; exit 1;; esac

OUT="$PROJECT/build/$FORMAT"
# Khong ghi de composition da dung: chay lai lenh nay se xoa het canh agent da viet.
if [ -f "$OUT/index.html" ] && [ "${FORCE:-0}" != 1 ]; then
  echo "[LOI] $OUT/index.html da ton tai. Muon tao lai tu template: FORCE=1 bash $0 $*"; exit 1
fi
mkdir -p "$OUT/fonts" "$OUT/assets"
NAME="$(basename "$PROJECT")-$FORMAT"

if [ "$MODE" = 3d ]; then
  cp "$STUDIO_SKILL/templates/$FORMAT-3d.html" "$OUT/index.html"
  TH="$STUDIO_TOOLS/node_modules/three"
  [ -d "$TH" ] || { echo "[LOI] Chua cai three. Chay lai setup.sh"; exit 1; }
  cp "$TH/build/three.module.min.js" "$TH/build/three.core.min.js" "$OUT/"
  mkdir -p "$OUT/jsm/loaders" "$OUT/jsm/utils"
  cp "$TH/examples/jsm/loaders/GLTFLoader.js" "$OUT/jsm/loaders/"
  cp "$TH/examples/jsm/utils/BufferGeometryUtils.js" "$TH/examples/jsm/utils/SkeletonUtils.js" "$OUT/jsm/utils/"
  cp "$STUDIO_SKILL/assets/sim3d/sim3d.js" "$OUT/"
  echo "window.SPEECH = { fps: 30, env: [] };" > "$OUT/speech.js"
elif [ "$MODE" = lineart ]; then
  cp "$STUDIO_SKILL/templates/$FORMAT-lineart.html" "$OUT/index.html"
  cp "$STUDIO_SKILL/assets/lineart/lineart.js" "$OUT/"
  echo "window.SPEECH = { fps: 30, env: [] };" > "$OUT/speech.js"
elif [ "$MODE" = chibi ]; then
  cp "$STUDIO_SKILL/templates/$FORMAT-chibi.html" "$OUT/index.html"
  cp "$STUDIO_SKILL/assets/chibi/chibi.js" "$OUT/"
  echo "window.SPEECH = { fps: 30, env: [] };" > "$OUT/speech.js"
elif [ "$MODE" = vetay ]; then
  cp "$STUDIO_SKILL/templates/$FORMAT-vetay.html" "$OUT/index.html"
  cp "$STUDIO_SKILL/assets/vetay/vetay.js" "$OUT/"
  mkdir -p "$OUT/img"
else
  cp "$STUDIO_SKILL/templates/$FORMAT.html" "$OUT/index.html"
fi
cp "$STUDIO_TOOLS/node_modules/gsap/dist/gsap.min.js" "$OUT/"
FS="$STUDIO_TOOLS/node_modules/@fontsource/be-vietnam-pro"
cp "$FS"/400.css "$FS"/600.css "$FS"/800.css "$OUT/fonts/"
mkdir -p "$OUT/fonts/files"
cp "$FS"/files/be-vietnam-pro-{vietnamese,latin,latin-ext}-{400,600,800}-normal.woff* "$OUT/fonts/files/"

cat > "$OUT/package.json" <<EOF
{ "name": "$NAME", "private": true, "type": "module" }
EOF
cat > "$OUT/hyperframes.json" <<'EOF'
{ "paths": { "blocks": "compositions", "components": "compositions/components", "assets": "assets" },
  "media": { "autoProxy": true } }
EOF
cat > "$OUT/meta.json" <<EOF
{ "id": "$NAME", "name": "$NAME" }
EOF
echo "$OUT"
