#!/usr/bin/env bash
# Build lai video-studio/assets/lineart/lineart.js tu nguon trong assets/lineart/src.
# Dung:  bash tools/build_lineart.sh          (ghi de lineart.js)
#        bash tools/build_lineart.sh --check  (chi kiem tra lineart.js khop nguon, khong ghi)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/video-studio/assets/lineart/src"
OUT="$ROOT/video-studio/assets/lineart/lineart.js"
ESBUILD_VER="0.28.2"
BANNER="// lineart.js: dan nhan vat net muc cho video-studio. Build tu lib/ cua JDhruv14/line-art-animation (MIT, xem LICENSE-line-art-animation.txt) va cast/ (rig, roster, stage). Khong sua tay: sua nguon roi build lai."
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cp -r "$SRC/lib" "$SRC/cast" "$TMP/"
( cd "$TMP" && npm i --no-save --no-audit --no-fund "esbuild@$ESBUILD_VER" >/dev/null 2>&1 \
  && npx esbuild cast/index.ts --bundle --format=esm --target=es2020 --legal-comments=inline \
       --banner:js="$BANNER" --outfile="$TMP/lineart.js" --log-level=warning )
if [ "${1:-}" = "--check" ]; then
  if cmp -s "$TMP/lineart.js" "$OUT"; then echo "[OK] lineart.js khop nguon"; else echo "[LOI] lineart.js khong khop nguon: chay bash tools/build_lineart.sh roi commit"; exit 1; fi
else
  cp "$TMP/lineart.js" "$OUT"; echo "Da ghi $OUT"
fi
