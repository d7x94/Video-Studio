#!/usr/bin/env bash
# Build lai video-studio/assets/venet/venet-chu.js (net chu viet tay tieng Viet) tu phong Patrick Hand (SIL OFL 1.1).
# Dung:  bash tools/build_venet_chu.sh           (ghi de venet-chu.js)
#        bash tools/build_venet_chu.sh --check   (chi kiem tra venet-chu.js khop, khong ghi)
# Phong tai tu npm goi @fontsource/patrick-hand, ghim phien ban va sha256 cua file .tgz (khong khop thi dung).
# Can: node, npm, python3 voi Pillow, numpy, scipy, fonttools.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTDIR="$ROOT/video-studio/assets/venet"
VER="5.3.0"
SHA256="c3428d02610c7b8fa92b044cf766f8c30b88bb32a47460b4ac42fa14e0bcdcc0"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
( cd "$TMP" && npm pack "@fontsource/patrick-hand@$VER" --silent >/dev/null )
TGZ="$TMP/fontsource-patrick-hand-$VER.tgz"
GOT="$(sha256sum "$TGZ" | cut -d' ' -f1)"
[ "$GOT" = "$SHA256" ] || { echo "[LOI] sha256 goi phong khong khop: $GOT"; exit 1; }
mkdir -p "$TMP/x" && tar -xzf "$TGZ" -C "$TMP/x"
python3 -I "$ROOT/tools/venet_chu.py" "$TMP/x/package/files" "$TMP/venet-chu.js"
if [ "${1:-}" = "--check" ]; then
  if cmp -s "$TMP/venet-chu.js" "$OUTDIR/venet-chu.js"; then echo "[OK] venet-chu.js khop"; else echo "[LOI] venet-chu.js khong khop: chay bash tools/build_venet_chu.sh roi commit"; exit 1; fi
else
  cp "$TMP/venet-chu.js" "$OUTDIR/venet-chu.js"
  cp "$TMP/x/package/LICENSE" "$OUTDIR/LICENSE-patrick-hand-OFL.txt"
  echo "Da ghi $OUTDIR/venet-chu.js"
fi
