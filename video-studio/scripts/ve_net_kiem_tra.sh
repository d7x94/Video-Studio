#!/usr/bin/env bash
# Kiem tra thoi gian ve cua composition kieu ve-net: moi canh ve xong luc nao, canh nao ve khong kip.
# Dung:  bash ve_net_kiem_tra.sh BUILD_DIR      (vd ~/studio/<slug>/build/portrait)
# In ra tung canh: thoi diem ve xong (drawEnd) so voi thoi diem canh ket thuc (end), va danh sach canh bao.
# Thoat 1 neu co canh bao (net khong kip ve truoc khi canh ket thuc).
set -euo pipefail
source "${STUDIO_HOME:-$HOME/studio}/studio.env"
BUILD="$(cd "$1" && pwd)"
PORT=$((20000 + RANDOM % 20000))
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$BUILD" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1
HTML="$("$HYPERFRAMES_BROWSER_PATH" --headless=new --no-sandbox --disable-gpu --virtual-time-budget=6000 \
  --dump-dom "http://127.0.0.1:$PORT/index.html" 2>/dev/null)"
printf '%s' "$HTML" | python3 -I -c '
import sys, re, json, html
m = re.search(r"data-venet-report=\"([^\"]*)\"", sys.stdin.read())
if not m:
    sys.exit("[LOI] Khong doc duoc bao cao: composition chua dung venet.js hoac co loi script (chay hyperframes check)")
r = json.loads(html.unescape(m.group(1)))
for s in r["scenes"]:
    flag = "  <-- KHONG KIP" if s["drawEnd"] + 0.5 > s["end"] + 0.05 and s["items"] else ""
    print("%s: %d net, ve xong luc %.2fs, canh ket thuc %.2fs%s" % (s["id"], s["items"], s["drawEnd"], s["end"], flag))
for w in r["warnings"]:
    print("[CANH BAO]", w)
sys.exit(1 if r["warnings"] else 0)
'
