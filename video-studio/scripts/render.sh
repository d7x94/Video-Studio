#!/usr/bin/env bash
# Kiem tra va render mot composition.
# Dung:  bash render.sh BUILD_DIR preview|final OUT.mp4
#   Canh 3D: khoang 13 giay render cho moi giay video o CA HAI che do (ban nhap khong nhanh hon).
#   Video 3D dai hon khoang 40 giay se vuot 10 phut: chay lenh nay o che do nen.
#   preview: chat luong nhap, nhanh, de duyet
#   final:   chat luong mac dinh cua HyperFrames ("looks", CRF 16)
set -euo pipefail
source "${STUDIO_HOME:-$HOME/studio}/studio.env"

BUILD="$(cd "$1" && pwd)"; MODE="$2"; OUT="$(realpath -m "$3")"
mkdir -p "$(dirname "$OUT")"
cd "$BUILD"

# Tranh render lap: neu OUT da co va moi hon moi file cua composition thi dung lai ban do.
# (Agent dung canh da render nhap; dieu phoi vien goi lai lenh nay se khong ton them thoi gian.)
# Ep render lai: FORCE=1 bash render.sh ...
if [ "${FORCE:-0}" != 1 ] && [ -s "$OUT" ] && \
   [ -z "$(find . -type f -newer "$OUT" -not -path './.hyperframes/*' -not -path './snaps/*' -print -quit)" ]; then
  echo "Bo qua render: $OUT con moi hon composition (FORCE=1 de render lai)"
  exit 0
fi

# Lint truoc: loi cu phap composition thi dung som, khoi ton thoi gian render
hyperframes lint || { echo "[LOI] Lint that bai, sua composition truoc khi render"; exit 1; }

case "$MODE" in
  preview) QUALITY=draft ;;
  final)   QUALITY=looks ;;
  *) echo "MODE phai la preview hoac final"; exit 1 ;;
esac

START=$(date +%s)
hyperframes render -o "$OUT" -q "$QUALITY" --quiet
echo "Render $MODE xong sau $(( $(date +%s) - START ))s: $OUT"
