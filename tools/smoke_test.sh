#!/usr/bin/env bash
# Thu nhanh cac script khong can mo hinh giong doc, trinh duyet hay mang (chay trong CI va tren may).
# Dung:  bash tools/smoke_test.sh
# Can: python3 (numpy, soundfile), node (vai.py doc dan nhan vat); khong can ffmpeg. Khong thay the buoc chay thu tron mot video mau (xem CLAUDE.md).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
S="$ROOT/video-studio/scripts"
T="$ROOT/video-studio/templates"
P="$(mktemp -d)"; trap 'rm -rf "$P"' EXIT
pass() { echo "[DAT] $*"; }
loi()  { echo "[LOI] $*"; exit 1; }
expect_fail() { if "$@" >/dev/null 2>&1; then loi "le ra phai that bai: $*"; fi; }

# 1. Du an mau: 2 canh, co claim, co subtitle khac narration; tieng gia (sine) thay cho VieNeu
mkdir -p "$P/audio"
cat > "$P/scenes.json" <<'EOF'
{"voice": "Mai Anh", "scenes": [
 {"id": "s01", "narration": "Xin chào các bạn, hôm nay mình nói về muỗi vằn và cách phòng bệnh sốt xuất huyết.",
  "visual": "Chị cán bộ đứng cạnh chậu nước đọng, chỉ tay vào bọ gậy đang bơi", "claims": []},
 {"id": "s02", "narration": "Muỗi vằn đẻ trứng trong nước đọng sạch, như lu, chậu, lốp xe cũ.",
  "subtitle": "Muỗi vằn đẻ trứng trong nước đọng sạch, như lu, chậu, lốp xe cũ.",
  "visual": "Ba hình lu, chậu, lốp xe hiện lần lượt, mỗi hình có giọt nước rơi xuống",
  "claims": ["Muỗi vằn đẻ trứng trong nước đọng sạch"]}]}
EOF
python3 -I - "$P" <<'PY'
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf
p = Path(sys.argv[1]); sr = 24000
sc = json.loads((p / "scenes.json").read_text(encoding="utf-8"))["scenes"]
t, out = 0.0, []
for i, s in enumerate(sc):
    gap = 0.4 if i == 0 else 0.35
    t += gap
    n = len(s["narration"].split())
    # tieng gia: moi tieng 0,22 s am, 0,06 s lang, de moc_tu tach duoc
    seg = np.concatenate([np.concatenate([0.3 * np.sin(2 * np.pi * 220 * np.arange(int(0.22 * sr)) / sr),
                                          np.zeros(int(0.06 * sr))]) for _ in range(n)]).astype(np.float32)
    sf.write(p / "audio" / f"{s['id']}.wav", seg, sr)
    d = round(len(seg) / sr, 3)
    out.append({"id": s["id"], "start": round(t, 3), "duration": d, "audio": f"audio/{s['id']}.wav",
                "narration": s["narration"], "voice": "Mai Anh", "speed": 1.0, "pause_before": gap})
    t += d
total = round(t + 1.0, 3)
for i, s in enumerate(out):
    s["visual_start"] = 0.0 if i == 0 else s["start"]
    s["visual_duration"] = round((out[i + 1]["start"] if i + 1 < len(out) else total) - s["visual_start"], 3)
(p / "timeline.json").write_text(json.dumps({"voice": "Mai Anh", "voices": ["Mai Anh"], "speed": 1.0,
    "lead_in": 0.4, "total": total, "scenes": out}, ensure_ascii=False, indent=2), encoding="utf-8")
PY
cp "$P/audio/s01.wav" "$P/voiceover.wav"

# 2. inject.py tren template doc va ngang (them hai section canh, chu go dang NFD)
for f in portrait landscape; do
  mkdir -p "$P/build/$f"
  python3 -I - "$T/$f.html" "$P/build/$f/index.html" <<'PY'
import sys, unicodedata
s = open(sys.argv[1], encoding="utf-8").read()
sec = ('<section id="sc-s01" class="clip scene" data-start="0" data-duration="1"><h1>'
       + unicodedata.normalize("NFD", "Muỗi vằn") + '</h1></section>\n'
       '<section id="sc-s02" class="clip scene" data-start="0" data-duration="1"><h1>Nước đọng</h1></section>\n')
s = s.replace("<!-- SCENES:END -->", sec + "<!-- SCENES:END -->", 1)
open(sys.argv[2], "w", encoding="utf-8").write(s)
PY
  python3 "$S/inject.py" "$P/timeline.json" "$P/build/$f/index.html" >/dev/null
  python3 -I - "$P/build/$f" <<'PY'
import sys, unicodedata
from pathlib import Path
d = Path(sys.argv[1]); h = (d / "index.html").read_text(encoding="utf-8"); srt = (d / "phu-de.srt").read_text(encoding="utf-8")
assert unicodedata.is_normalized("NFC", h), "index.html chua NFC"
assert 'id="sc-s02" class="clip scene" data-start="' in h and 'data-start="0" data-duration="1"' not in h, "chua dong bo moc canh"
assert "const T = {" in h and h.count('<audio id="vo-') == 2 and 'class="cap clip"' in h, "thieu T, audio hoac phu de"
assert "00:00:00,400 --> " in srt and "Muỗi vằn đẻ trứng" in srt, "phu-de.srt sai"
PY
done
pass "inject.py khung doc va ngang (moc canh, audio, phu de, NFC)"

python3 "$S/inject.py" "$P/timeline.json" "$P/build/portrait/index.html" --tung-tu >/dev/null 2>"$P/tung-tu.err"
grep -q "TUNG-TU:BEGIN" "$P/build/portrait/index.html" || loi "--tung-tu khong them khoi to mau tu"
grep -q 'class="w" data-t=' "$P/build/portrait/index.html" || { cat "$P/tung-tu.err"; loi "--tung-tu khong sinh moc tung tu"; }
python3 "$S/inject.py" "$P/timeline.json" "$P/build/portrait/index.html" >/dev/null
grep -q "TUNG-TU:BEGIN" "$P/build/portrait/index.html" && loi "chay lai khong --tung-tu khong go khoi to mau"
pass "inject.py --tung-tu them va go khoi to mau"

python3 "$S/inject.py" "$P/timeline.json" --srt-only "$P/a.srt"
cmp -s "$P/a.srt" "$P/build/landscape/phu-de.srt" || loi "--srt-only khac phu de khung ngang"
pass "inject.py --srt-only khop phu de khung ngang"

# Dong phu de chi co dau cau khong lam --tung-tu vo (truoc 1.12.1: StopIteration)
python3 -I - "$S" <<'PY'
import sys; sys.path.insert(0, sys.argv[1])
import inject
inject.merge_short = lambda chunks, dur, mc: chunks
inject.split_text = lambda text, mc: ["...", "Rửa tay.", "—", "Xong."]
tl = {"scenes": [{"id": "s01", "start": 0.4, "duration": 3.0, "narration": "x"}]}
moc = {"scenes": [{"id": "s01", "sub": [{"s": 0.5}, {"s": 0.9}, {"s": 1.6}]}]}
caps = inject.word_captions(tl, 48, moc)
assert [c["text"] for c in caps] == ["Rửa tay —", "Xong"], caps
PY
pass "inject.py --tung-tu voi dong chi co dau cau"

# 3. Ma khang dinh va bang kiem chung
python3 "$S/ma_khang_dinh.py" gan "$P" >/dev/null
python3 "$S/ma_khang_dinh.py" gan "$P" >/dev/null   # chay lai khong doi gi
python3 "$S/ma_khang_dinh.py" liet-ke "$P" | grep -q "k01" || loi "liet-ke thieu k01"
cat > "$P/kiem-chung.md" <<'EOF'
| Mã | Cảnh | Thông tin | Kết luận | Nguồn | Trích đoạn | Đề xuất |
|---|---|---|---|---|---|---|
| k01 | s02 | Muỗi vằn đẻ trứng trong nước đọng sạch | Cần sửa | Nguồn mẫu | trích đoạn mẫu | |
EOF
expect_fail python3 "$S/ma_khang_dinh.py" kiem "$P"
sed -i 's/| Cần sửa |/| Đúng |/' "$P/kiem-chung.md"
python3 "$S/ma_khang_dinh.py" kiem "$P" >/dev/null || loi "ma_khang_dinh kiem le ra khop"
pass "ma_khang_dinh.py gan, liet-ke, kiem (chan Can sua, khop khi Dung)"

# 4. Khoa kich ban
expect_fail python3 "$S/khoa_kich_ban.py" kiem "$P"
python3 "$S/khoa_kich_ban.py" khoa "$P" >/dev/null
python3 "$S/khoa_kich_ban.py" kiem "$P" >/dev/null || loi "khoa_kich_ban kiem le ra khop"
sed -i 's/lốp xe cũ/lốp xe hỏng/g' "$P/scenes.json"
expect_fail python3 "$S/khoa_kich_ban.py" kiem "$P"
pass "khoa_kich_ban.py khoa, kiem (bat canh doi loi)"

# 5. Soat canh, trang thai, ho so vai
python3 "$S/soat_canh.py" "$P/scenes.json" --kieu line-art --muc-tieu 12 >/dev/null
python3 "$S/trang_thai.py" ghi "$P" 2 xong --tep scenes.json >/dev/null
python3 "$S/trang_thai.py" xem "$P" --json | python3 -c "import json,sys; json.load(sys.stdin)"
python3 "$S/vai.py" kiem >/dev/null
pass "soat_canh.py, trang_thai.py, vai.py kiem"

# 5b. Che do dich: ban dich, kiem, srt (khong can Whisper hay video)
D="$P/dich-thu"; mkdir -p "$D/dich"
cat > "$D/dich/chep-goc.json" <<'EOF'
{"phien_ban": 1, "ngon_ngu": {"chon": "en"}, "doan": [
 {"id": "d001", "start": 0.5, "end": 3.0, "goc": "I studied for 12 hours today.", "co": []},
 {"id": "d002", "start": 3.2, "end": 5.0, "goc": "Thanks for watching!", "co": ["nghi-bia"]}]}
EOF
python3 "$S/phu_de_dich.py" khoi "$D" >/dev/null
expect_fail python3 "$S/phu_de_dich.py" kiem "$D"
python3 -I - "$D" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]) / "dich/ban-dich.json"; bd = json.loads(p.read_text(encoding="utf-8"))
bd["doan"][0]["dich"] = "Hôm nay mình học mười hai tiếng."
bd["doan"][1]["bo"] = True
p.write_text(json.dumps(bd, ensure_ascii=False), encoding="utf-8")
PY
expect_fail python3 "$S/phu_de_dich.py" kiem "$D"
sed -i 's/mười hai/12/' "$D/dich/ban-dich.json"
python3 "$S/phu_de_dich.py" srt "$D" >/dev/null || loi "phu_de_dich srt le ra dat"
grep -q "^Hôm nay mình học 12 tiếng.$" "$D/output/phu-de-vi.srt" || loi "phu-de-vi.srt sai noi dung"
[ "$(grep -c -- '-->' "$D/output/phu-de-vi.srt")" = 1 ] || loi "doan bo van con trong srt"
pass "phu_de_dich.py khoi, kiem (chan thieu dich, mat so), srt (bo doan danh dau bo)"

# 6. Script shell: cu phap
for f in "$S"/*.sh "$ROOT"/tools/*.sh; do bash -n "$f"; done
pass "cu phap script shell"
echo "Tat ca dat."
