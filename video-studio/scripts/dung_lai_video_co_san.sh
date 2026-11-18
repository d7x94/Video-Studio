#!/usr/bin/env bash
# Dung lai video co san sau moi lan sua loi doc hoac lam mo: ghep loi, cap nhat timeline, nhac nen (neu co),
# chuan am, chep ra output/. Chay sau khi da doc lai cac canh bi sua (tts.py --only ...).
# Dung:  bash dung_lai_video_co_san.sh PROJECT [--cau-hinh ghep.json] [--kieu nhe-nhang|khong] [--muc -13] [--ten ten-video]
#   --kieu   kieu nhac nen cua nhac_nen.py; "khong" (mac dinh) = khong them nhac
#   --muc    muc nhac nen dB truoc khi giam theo loi (mac dinh -13; video loi thua nen nhe hon mac dinh -10 cua nhac_nen.py)
#   --ten    ten file ra o PROJECT/output/<ten>.mp4 (mac dinh video)
#   --tung-tu  them output/<ten>-phu-de-tung-tu.mp4: phu de tung tu (tu dang doc doi mau) ghi cung vao hinh
#              (moc_tu.py roi phu_de_tung_tu.py --ghi); giu nguyen output/<ten>.mp4 khong phu de cung
# Am luong chua dat muc tieu chi canh bao (van chep ra output/); loi that cua chuan_am.sh (dong [LOI]) van dung chuoi.
# Tao renders/final_portrait.mp4 (hoac ten khac) tu hinh trong ghep.json. Bao loi neu loi doc chong nhau (script ghep in canh bao).
set -euo pipefail
die() { echo "[LOI] dung_lai_video_co_san.sh: $*" >&2; exit 1; }

PROJECT="${1:-}"; [ -d "$PROJECT" ] || die "dung: bash dung_lai_video_co_san.sh PROJECT [--cau-hinh ghep.json] [--kieu K] [--muc dB] [--ten ten] [--tung-tu]"
shift
CFG="ghep.json"; KIEU="khong"; MUC="-13"; TEN="video"; TUNG_TU=0
while [ $# -gt 0 ]; do
  case "$1" in
    --cau-hinh) CFG="$2"; shift 2 ;;
    --kieu) KIEU="$2"; shift 2 ;;
    --muc) MUC="$2"; shift 2 ;;
    --ten) TEN="$2"; shift 2 ;;
    --tung-tu) TUNG_TU=1; shift ;;
    *) die "tham so la: $1" ;;
  esac
done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV="${STUDIO_HOME:-$HOME/studio}/studio.env"
[ -f "$ENV" ] && . "$ENV"
cd "$PROJECT"
[ -f "$CFG" ] || die "khong thay $CFG"
[ -f scenes.json ] && [ -f timeline.json ] || die "can scenes.json va timeline.json (chay tts.py truoc)"
mkdir -p renders output
OUT="renders/final_portrait.mp4"
rm -f "$OUT" "renders/final_portrait.khong-nhac.mp4"

python3 "$HERE/ghep_loi_video_co_san.py" . "$CFG" --ra "$OUT"
# nhac_nen.py doc tong thoi luong tu timeline.json; sau khi giu khung hinh thi tong da doi
python3 - <<'PY'
import json
g = json.load(open("timeline_ghep.json"))
t = json.load(open("timeline.json"))
t["total"] = g["tong_giay"]
json.dump(t, open("timeline.json", "w"))
PY
if [ "$KIEU" != "khong" ]; then
  python3 "$HERE/nhac_nen.py" . --kieu "$KIEU" --muc "$MUC" "$OUT"
fi
# chuan_am.sh thoat ma 1 ca khi chi lech muc tieu (da ghi file chuan hoa) lan khi loi that. Chi bo qua truong hop thu nhat:
# van chep ra output/ va in lai canh bao o cuoi; co dong [LOI] trong stderr thi dung chuoi.
AM_CB=0; AM_RC=0; AM_LOG="$(mktemp)"
bash "$HERE/chuan_am.sh" "$OUT" 2>"$AM_LOG" || AM_RC=$?
cat "$AM_LOG" >&2
if [ "$AM_RC" != 0 ]; then
  grep -q '^\[LOI\]' "$AM_LOG" && { rm -f "$AM_LOG"; die "chuan_am.sh that bai"; }
  AM_CB=1
fi
rm -f "$AM_LOG"
cp "$OUT" "output/$TEN.mp4"
if [ "$TUNG_TU" = 1 ]; then
  python3 "$HERE/moc_tu.py" . >/dev/null
  python3 "$HERE/phu_de_tung_tu.py" . --ghi "$OUT" "output/$TEN-phu-de-tung-tu.mp4"
fi
cp phu-de.srt output/phu-de.srt
python3 - <<'PY'
import json
sc = json.load(open("scenes.json"))["scenes"]
st = json.load(open("timeline_ghep.json"))["start"]
open("output/loi-doc.md", "w", encoding="utf-8").write(
    "# Loi doc\n\n" + "\n".join(f"- {st[s['id']]:.1f}s: {s.get('subtitle') or s['narration']}" for s in sc if s['id'] in st) + "\n")
PY
[ "$AM_CB" = 1 ] && echo "[CANH BAO] chuan_am.sh bao am luong chua dat muc tieu (xem tren): nghe lai truoc khi giao" >&2
echo "[OK] output/$TEN.mp4"
