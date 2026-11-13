#!/usr/bin/env bash
# Build lai video-studio/assets/chibi/chibi.js tu nguon trong assets/chibi/src (dung chung roster cua line-art).
# Dung:  bash tools/build_chibi.sh          (ghi de chibi.js)
#        bash tools/build_chibi.sh --check  (chi kiem tra chibi.js khop nguon, khong ghi)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ASSETS="$ROOT/video-studio/assets"
OUT="$ASSETS/chibi/chibi.js"
ESBUILD_VER="0.28.2"
BANNER="// chibi.js: nhan vat chibi nhin chinh dien cho video-studio. Dan nhan vat dung chung roster voi line-art. Khong sua tay: sua nguon trong assets/chibi/src roi build lai."
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/chibi" "$TMP/lineart/src"
cp -r "$ASSETS/chibi/src" "$TMP/chibi/"
cp -r "$ASSETS/lineart/src/cast" "$ASSETS/lineart/src/lib" "$TMP/lineart/src/"
( cd "$TMP" && npm i --no-save --no-audit --no-fund "esbuild@$ESBUILD_VER" >/dev/null 2>&1 \
  && npx esbuild chibi/src/index.ts --bundle --format=esm --target=es2020 --legal-comments=inline \
       --banner:js="$BANNER" --outfile="$TMP/chibi.js" --log-level=warning )
if [ "${1:-}" = "--check" ]; then
  if cmp -s "$TMP/chibi.js" "$OUT"; then echo "[OK] chibi.js khop nguon"; else echo "[LOI] chibi.js khong khop nguon: chay bash tools/build_chibi.sh roi commit"; exit 1; fi
else
  cp "$TMP/chibi.js" "$OUT"; echo "Da ghi $OUT"
fi
