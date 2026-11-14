#!/usr/bin/env bash
# Dong goi skill thanh zip de tai len claude.ai (Settings > Skills).
# Dung:  bash tools/package_skill.sh [OUT.zip]   (mac dinh: dist/video-studio.zip)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(realpath -m "${1:-$ROOT/dist/video-studio.zip}")"
mkdir -p "$(dirname "$OUT")"; rm -f "$OUT"
# So phien ban: file VERSION phai dung dinh dang X.Y.Z va khop dong "Phien ban skill" trong SKILL.md
VER="$(tr -d '[:space:]' < "$ROOT/video-studio/VERSION")"
[[ "$VER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "VERSION khong dung dinh dang X.Y.Z: $VER"; exit 1; }
grep -qF "Phiên bản skill: $VER " "$ROOT/video-studio/SKILL.md" || { echo "SKILL.md khong co dong 'Phiên bản skill: $VER'"; exit 1; }
grep -qF "## [$VER]" "$ROOT/CHANGELOG.md" || { echo "CHANGELOG.md thieu muc [$VER]"; exit 1; }
bash "$ROOT/tools/build_lineart.sh" --check
bash "$ROOT/tools/build_chibi.sh" --check
python3 "$ROOT/video-studio/scripts/vai.py" kiem   # ho so vai phai hop le truoc khi dong goi
( cd "$ROOT" && zip -qr "$OUT" video-studio -x '*/__pycache__/*' '*.pyc' '*/.DS_Store' )
echo "Da dong goi: $OUT ($(du -h "$OUT" | cut -f1))"
