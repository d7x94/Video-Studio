#!/usr/bin/env bash
# Chuan hoa am luong ban cuoi ve -14 LUFS, dinh true peak khong qua -1 dBTP (chuan chung cho YouTube va TikTok).
# Dung:  bash chuan_am.sh IN.mp4 [OUT.mp4]       (khong co OUT thi ghi de IN)
# Chay SAU nhac_nen.py (nhac nen da tron vao), TRUOC check_output.py.
# Hai luot loudnorm (mot luot lech khoang 0,5 LU), roi bo han che dinh o 192 kHz de bat dinh giua cac mau sau khi ma hoa AAC.
# Hinh giu nguyen (copy). Am im lang (duoi -70 LUFS) thi bo qua chuan hoa va bao.
# Y tuong va he so lay tu core/render/mux.sh cua Lemo-Opuscar (MIT), viet lai gon hon, xem README muc Ghi cong.
set -euo pipefail
LC_ALL=C; export LC_ALL
die() { echo "[LOI] chuan_am.sh: $*" >&2; exit 1; }

IN="${1:-}"; OUT="${2:-$IN}"
[ -n "$IN" ] || die "dung: bash chuan_am.sh IN.mp4 [OUT.mp4]"
[ -f "$IN" ] || die "khong thay file: $IN"
command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null || die "can ffmpeg va ffprobe"
[ -n "$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_type -of csv=p=0 "$IN")" ] || die "$IN khong co luong tieng"

TARGET="I=-14:TP=-1.2:LRA=11"
M=$(ffmpeg -hide_banner -nostats -i "$IN" -vn -af "loudnorm=$TARGET:print_format=json" -f null - 2>&1) || die "ffmpeg khong doc duoc tieng: $(echo "$M" | tail -2)"
J=$(echo "$M" | sed -n '/{/,/}/p')
g() { echo "$J" | grep "\"$1\"" | sed 's/.*: "\(.*\)".*/\1/'; }
NORM=1
for k in input_i input_tp input_lra input_thresh target_offset; do
  case "$(g $k)" in ''|*inf*|*nan*) NORM=0 ;; esac
done

CEIL=-1.6
lim() { [ "$NORM" = 1 ] || return 0
  echo ",aresample=192000,alimiter=limit=$(awk -v d="$1" 'BEGIN { printf "%.4f", 10 ^ (d / 20) }'):attack=10:release=200:level=disabled:latency=1,aresample=48000"; }

if [ "$NORM" = 1 ]; then
  # loudnorm chi nhan do on toi da 0 LUFS: ban tron qua to (dang meo) thi ha xuong truoc
  PRE=""
  if awk -v i="$(g input_i)" 'BEGIN { exit !(i + 0 > 0) }'; then
    PG=$(awk -v i="$(g input_i)" 'BEGIN { printf "%.2f", i + 14 }'); PRE="volume=-${PG}dB,"
    echo "[CANH BAO] am luong ban tron $(g input_i) LUFS (gan nhu meo tieng), ha $PG dB truoc khi chuan hoa; nen giam nhac nen" >&2
    M=$(ffmpeg -hide_banner -nostats -i "$IN" -vn -af "${PRE}loudnorm=$TARGET:print_format=json" -f null - 2>&1) || die "khong do lai duoc"
    J=$(echo "$M" | sed -n '/{/,/}/p')
  fi
  LN="${PRE}loudnorm=$TARGET:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true"
else
  LN="anull"
  echo "[CANH BAO] tieng im lang hoac duoi -70 LUFS, bo qua chuan hoa am luong" >&2
fi

B=${OUT##*/}; case "$B" in *.*) EXT=${B##*.} ;; *) EXT=mp4 ;; esac
TMP="$OUT.$$.part.$EXT"
trap 'rm -f "$TMP"' EXIT
encode() {  # $1 = tran bo han che (dBFS)
  ffmpeg -y -loglevel error -i "$IN" -map 0:v -map 0:a:0 -c:v copy \
    -af "$LN$(lim "$1")" -c:a aac -b:a 256k -ar 48000 -movflags +faststart "$TMP" || die "ffmpeg loi khi ghi $OUT"
  [ -s "$TMP" ] || die "khong ghi duoc $OUT"
}
measure() { ffmpeg -hide_banner -nostats -i "$TMP" -vn -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):" | head -3; }

encode "$CEIL"; R=$(measure); N=0
# AAC them dinh giua cac mau: con vuot -1 dBTP thi ma hoa lai tieng voi tran thap hon (toi da 3 lan)
while [ "$NORM" = 1 ] && [ $N -lt 3 ]; do
  P=$(echo "$R" | awk '$1 == "Peak:" { print $2 }')
  [ -n "$P" ] || break
  awk -v p="$P" 'BEGIN { exit !(p + 0 > -1) }' || break
  CEIL=$(awk -v c="$CEIL" -v p="$P" 'BEGIN { printf "%.2f", c - (p + 1.3) }'); N=$((N + 1))
  echo "[INFO] true peak $P dB sau khi ma hoa, ma hoa lai tieng voi tran $CEIL dBFS" >&2
  encode "$CEIL"; R=$(measure)
done
# Giu moc gio cua ban goc: nhac_nen.py so moc gio de biet ban nao la ban moi render; file moi hon se bi coi la ban chua co nhac va ghep nhac chong len nhac
touch -r "$OUT" "$TMP"
mv -f "$TMP" "$OUT"
echo "$R"
if [ "$NORM" = 1 ]; then
  OI=$(echo "$R" | awk '$1 == "I:" { print $2 }'); OP=$(echo "$R" | awk '$1 == "Peak:" { print $2 }')
  if awk -v i="$OI" -v p="$OP" 'BEGIN { exit !(i + 0 < -15 || i + 0 > -13 || p + 0 > -1) }'; then
    echo "[CANH BAO] chua dat muc tieu (-14 LUFS, dinh <= -1 dB): do duoc $OI LUFS, dinh $OP dB. Giam nhac nen roi chay lai" >&2
    exit 1
  fi
fi
echo "[OK] $OUT"
