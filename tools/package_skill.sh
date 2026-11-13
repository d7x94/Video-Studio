#!/usr/bin/env bash
# Dong goi skill thanh zip de tai len claude.ai (Settings > Skills).
# Dung:  bash tools/package_skill.sh [OUT.zip]   (mac dinh: dist/video-studio.zip)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(realpath -m "${1:-$ROOT/dist/video-studio.zip}")"
mkdir -p "$(dirname "$OUT")"; rm -f "$OUT"
bash "$ROOT/tools/build_lineart.sh" --check
bash "$ROOT/tools/build_chibi.sh" --check
( cd "$ROOT" && zip -qr "$OUT" video-studio -x '*/__pycache__/*' '*.pyc' '*/.DS_Store' )
echo "Da dong goi: $OUT ($(du -h "$OUT" | cut -f1))"
