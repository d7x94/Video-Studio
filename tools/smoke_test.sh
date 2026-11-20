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
OUT=$(python3 "$S/ma_khang_dinh.py" liet-ke "$P" || true)
grep -q "k01" <<<"$OUT" || loi "liet-ke thieu k01"
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

# 5b. phu_de_dich: so thap phan viet kieu Viet, ky tu dac biet cua libass, dong goc song ngu dai
python3 -I - "$S/phu_de_dich.py" "$P" <<'PY'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("pdd", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.so_thieu("Up 3.5 percent from 1,000 to 2.500", "Tăng 3,5% từ 1.000 lên 2,500") == [], "so kieu Viet bi chan"
assert m.so_thieu("Up 3.5 percent", "Tăng 35%") == ["3.5"], "mat so khong bi bat"
assert m.so_thieu("In 2024 it was 10", "Năm 2024") == ["10"], "mat so nguyen khong bi bat"
proj = Path(sys.argv[2]) / "ass"; (proj / "dich").mkdir(parents=True, exist_ok=True)
goc = "So what we are really trying to say is that the whole thing is much more complicated than anyone admitted at the time."
doan = [{"start": 0.0, "end": 3.0, "dich": "Chọn {mục 2} rồi bấm \\N tiếp", "goc": goc}]
txt = m.ghi_ass(doan, proj, 720, 1280, "Inter", True).read_text(encoding="utf-8")
ev = [l for l in txt.splitlines() if l.startswith("Dialogue")]
assert len(ev) == 2 and "{" not in ev[0].split(",,", 1)[1] and "(mục 2)" in ev[0], "ky tu dac biet khong duoc thoat"
assert "/N" in ev[0], "dau gach nguoc cua nguoi dich khong duoc doi"
assert ev[1].count("\\N") >= 2, "dong goc dai khong duoc ngat dong"
PY
pass "phu_de_dich.py so thap phan kieu Viet, thoat ky tu libass, ngat dong goc song ngu"

# 5b. phu_de_dich: goi y gop doan ngan sat doan sau, canh bao gan nguoi_noi mot phan
python3 -I - "$S/phu_de_dich.py" "$P" <<'PY'
import importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("pdd", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
proj = Path(sys.argv[2]) / "gop"; (proj / "dich").mkdir(parents=True, exist_ok=True)
doan = [{"id": "d001", "start": 0.0, "end": 2.0, "goc": "你知道吗", "dich": "Em biết không?", "nguoi_noi": "chi"},
        {"id": "d002", "start": 2.0, "end": 2.5, "goc": "不知道", "dich": "Không biết.", "nguoi_noi": ""},
        {"id": "d003", "start": 2.5, "end": 4.5, "goc": "现在知道了", "dich": "Giờ biết rồi đó.", "nguoi_noi": "chi"}]
(proj / "dich" / "ban-dich.json").write_text(json.dumps({"phien_ban": 1, "doan": doan}, ensure_ascii=False), encoding="utf-8")
loi, canh, _ = m.kiem(proj, 15.0)
assert not loi, loi
assert any("gop PROJECT d002 d003" in c for c in canh), "thieu goi y gop doan ngan"
assert any("thieu nguoi_noi o d002" in c for c in canh), "thieu canh bao nguoi_noi gan mot phan"
assert not any(c.startswith("d001") and "goi y gop" in c for c in canh), "goi y gop cho doan khong ngan"
PY
pass "phu_de_dich.py goi y gop doan ngan, canh bao nguoi_noi"

# 5b. phu_de_dich: bang duyet chep, sua goc, them doan, gan nguoi noi, goi y gop va gop (khong gop khac nguoi noi), nhap, bang
D="$P/dich-quy-trinh"; mkdir -p "$D/dich"
cat > "$D/dich/chep-goc.json" <<'EOF2'
{"phien_ban": 1, "video": "v.mp4", "ban": "medium", "ngon_ngu": {"chon": "en"}, "khoang_trong": [[9.0, 14.0]], "doan": [
 {"id": "d001", "start": 0.0, "end": 2.0, "goc": "Bend the day at the library with me.", "co": []},
 {"id": "d002", "start": 3.0, "end": 4.0, "goc": "Before going there,", "co": []},
 {"id": "d003", "start": 4.1, "end": 6.0, "goc": "my friend ordered a port panini.", "co": []},
 {"id": "d004", "start": 6.1, "end": 6.8, "goc": "Really?", "co": []},
 {"id": "d005", "start": 6.9, "end": 8.0, "goc": "Yes.", "co": []}]}
EOF2
cat > "$D/dich/chep-firered.json" <<'EOF2'
{"doan": [{"id": "d001", "khac": true, "cho_khac": ["bend / spend"]}], "khoang_trong": [{"start": 9.0, "end": 11.0, "text": "ASMR TYPING"}]}
EOF2
cat > "$D/dich/chu-tren-hinh.json" <<'EOF2'
{"co_chu": true, "doan": [{"id": "d003", "cho_khac": [["port", "pork"]]}], "chu": [{"t": 1.0, "text": "Pork Panini"}, {"t": 2.0, "text": "猪肉帕尼尼"}]}
EOF2
X="python3 $S/phu_de_dich.py"
$X duyet-chep "$D" >/dev/null || loi "duyet-chep le ra dat"
[ -f "$D/dich/ban-dich.json" ] || loi "duyet-chep khong tao ban-dich.json"
grep -q 'sua d001 --thay "bend=spend"' "$D/dich/duyet-chep.md" || loi "duyet-chep thieu lenh sua theo FireRed"
grep -q 'sua d003 --thay "port=pork"' "$D/dich/duyet-chep.md" || loi "duyet-chep thieu lenh sua theo chu tren hinh"
grep -q 'them 9.0 11.0' "$D/dich/duyet-chep.md" || loi "duyet-chep thieu lenh them khoang trong"
grep -q '猪肉' "$D/dich/duyet-chep.md" && loi "duyet-chep giu phu de chu Han khi loi goc tieng Anh"
$X sua "$D" d001 --thay "bend=spend" >/dev/null
$X sua "$D" d003 --thay "port=pork" >/dev/null
expect_fail $X sua "$D" d003 --thay "beef=pork"
$X them "$D" 9.0 11.0 "Here's some ASMR typing." >/dev/null
expect_fail $X them "$D" 5.0 7.0 "chong"
$X nguoi "$D" d001-d004=a d005=b >/dev/null
OUT=$($X goi-y-gop "$D" || true)      # lay het dau ra roi moi grep: grep -q thoat som lam Python bao BrokenPipeError
grep -q "gop .* d002 d003 d004" <<<"$OUT" || loi "goi-y-gop khong goi y gop manh cau cung nguoi noi"
! grep -q "d005" <<<"$OUT" || loi "goi-y-gop gop sang nguoi noi khac"
expect_fail $X gop "$D" d004 d005
$X gop "$D" d002 d003 >/dev/null
printf 'd001\tCùng mình dành cả ngày ở thư viện nhé.\nd002 | Trước khi đến đó, bạn mình gọi panini thịt heo.\nd004\tThật á?\nd005\tỪ.\nd006\tCòn đây là âm thanh gõ phím ASMR.\n' > "$D/dich.tsv"
$X nhap "$D" "$D/dich.tsv" >/dev/null || loi "nhap le ra dat"
printf 'd003\tx\n' > "$D/sai.tsv"; expect_fail $X nhap "$D" "$D/sai.tsv"
$X kiem "$D" >/dev/null || loi "kiem sau quy trinh le ra dat"
$X bang "$D" >/dev/null
python3 -I - "$D" <<'PY'
import json, sys
from pathlib import Path
d = Path(sys.argv[1]) / "dich"
bd = {x["id"]: x for x in json.loads((d / "ban-dich.json").read_text(encoding="utf-8"))["doan"]}
assert bd["d001"]["goc"] == "Spend the day at the library with me." and bd["d001"]["goc_whisper"].startswith("Bend"), bd["d001"]
assert bd["d002"]["goc"] == "Before going there, my friend ordered a pork panini." and bd["d002"]["end"] == 6.0, bd["d002"]
assert bd["d003"]["bo"] and bd["d003"]["gop_vao"] == "d002" and bd["d002"]["gop_tu"] == ["d002", "d003"]
assert bd["d006"]["them"] and bd["d006"]["goc"] == "Here's some ASMR typing."
assert list(bd) == ["d001", "d002", "d003", "d004", "d005", "d006"]
md = (d / "ban-dich.md").read_text(encoding="utf-8")
assert "Whisper: Bend the day" in md and "gộp d002, d003" in md and "đoạn thêm tay" in md and "| d003 |" not in md
PY
python3 -I - "$S/phu_de_dich.py" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("pdd", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.thay_tu("Bend the day", "bend", "spend") == "Spend the day"
assert m.thay_tu("a portable port", "port", "pork") == "a portable pork"
assert m.thay_tu("美女也吹个兜巴吧", "兜巴", "头发") == "美女也吹个头发吧"
assert m.noi_loi("你回家了", "你要") == "你回家了你要" and m.noi_loi("Before,", "my") == "Before, my"
# kiem: goi y gop co lenh, khong goi y gop sang nguoi noi khac
PY
pass "phu_de_dich.py duyet-chep, sua, them, nguoi, goi-y-gop, gop (chan khac nguoi noi), nhap, bang"

# 5b. chep_loi_firered: doan chi khac tro tu cuoi cau khong bao KHAC (can opencc; khong co thi bo qua)
if python3 -c "import opencc, numpy" 2>/dev/null; then
python3 -I - "$S/chep_loi_firered.py" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("clf", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
cum = "你再叫一声呀姐姐我去你长得好帅呀你长得可像胡一天你知道吗"
assert m.so_cum("你再叫一声啊", cum) == (False, True), "chi khac tro tu van bao KHAC"
assert m.so_cum("姐姐", cum) == (False, False), "doan trung bi danh dau"
assert m.so_cum("你长得可像胡二天", cum) == (True, False), "doan khac that khong bao KHAC"
assert m.so_cum("哈哈", "我们") == (True, False), "chuoi chi co tro tu bi coi la khop"
# tieng Anh so theo tu: "bend" nam trong chuoi "spend" nhung la tu khac
c = "HEY GUYS WELCOME BACK TO ANOTHER ENGLISH BLOG SPEND THE DAY AT THE LIBRARY WITH ME"
assert m.so_cum("Bend the day at the library with me.", c) == (True, False), "bend/spend khong bao KHAC"
assert m.so_cum("Spend the day at the library with me.", c) == (False, False)
assert m.so_cum("The beef balls literally", "THE BEEFBALLS LITERALLY JUST") == (False, False), "chi khac tach tu van bao KHAC"
# ca cum: cho khac vat qua ranh gioi doan duoc tach dung doan, ghi chu tung ben
d = [{"id": "a", "goc": "Hey guys, welcome back to another English vlog."},
     {"id": "b", "goc": "Bend the day at the library with me."}]
assert m.so_ca_cum(d, c) == {"a": (True, False, ["vlog / blog"]), "b": (True, False, ["bend / spend"])}, m.so_ca_cum(d, c)
d = [{"id": "a", "goc": "你再叫一声啊"}, {"id": "b", "goc": "姐姐"}, {"id": "c", "goc": "走"}]
r = m.so_ca_cum(d, "你再叫一声呀姐姐走嗯")
assert r["a"][:2] == (False, True) and r["b"] == (False, False, []) and r["c"] == (True, False, ["(trống) / 嗯"]), r
# khoang trong: bo tieng dem, lap chu
assert m.co_loi_that(m.tach("HERE'S SOME ASMR TYPING")) and not m.co_loi_that(m.tach("嗯嗯嗯"))
assert not m.co_loi_that(m.tach("LA LA LA LA LA LA LA")) and not m.co_loi_that(m.tach(""))
PY
pass "chep_loi_firered.py nhan tro tu cuoi cau, so theo tu tieng Anh, tach cho khac theo doan, loc khoang trong"
python3 -I - "$S/chu_tren_hinh.py" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("cth", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
t = m.tach
w = t("so I'll grab something. And my friend ordered a port panini. The beef balls")
assert m.so_dong(w, t("anà my friend ordered a pork panini"), False) == (True, [(9, 10, "port", "pork")])
assert m.so_dong(w, t("Beef Meatballs & Pork Panini"), False)[0] is False      # thuc don: trung it, khong coi la phu de
assert m.so_dong(w, t("my friend ordered a port panini"), False) == (True, [])
assert m.so_dong(t("美女吹个兜巴吧"), t("美女吹个头发吧"), True) == (True, [(4, 6, "兜巴", "头发")])
assert m.so_dong(t("你好"), t("你好"), True)[0] is False                         # tieng Trung can it nhat 4 chu trung
assert m.moc_doc({"start": 0, "end": 2}) == [1.0] and len(m.moc_doc({"start": 0, "end": 8})) == 3
PY
pass "chu_tren_hinh.py (so dong chu voi loi Whisper, bo thuc don trung it, nguong tieng Trung, khung doc)"
else
echo "[BO QUA] chep_loi_firered.py, chu_tren_hinh.py: thieu opencc hoac numpy"
fi

# 5c. phu_de_tung_tu.py (khong can ffmpeg khi khong --ghi), ap_sua_srt.py, canh bao timeline_ghep.json cu cua kiem_loi_doc.py
V="$P/vct"; mkdir -p "$V"
cat > "$V/scenes.json" <<'EOF'
{"voice": "Hải Đăng", "scenes": [
 {"id": "s01", "narration": "Hôm nay hàng về rồi, khui ngay thôi.", "visual": "x", "on_screen": {}},
 {"id": "s02", "narration": "Mặt trước ghi chữ Bel-kin, cáp hát đê em ai.", "subtitle": "Mặt trước ghi chữ Belkin, cáp HDMI.", "visual": "x", "on_screen": {}}]}
EOF
cat > "$V/timeline.json" <<'EOF'
{"total": 6.0, "scenes": [{"id": "s01", "start": 0.4, "duration": 2.0}, {"id": "s02", "start": 3.0, "duration": 3.0}]}
EOF
cat > "$V/timeline_ghep.json" <<'EOF'
{"start": {"s01": 0.4, "s02": 10.0}, "tong_giay": 14.0}
EOF
cat > "$V/moc-tu.json" <<'EOF'
{"scenes": [
 {"id": "s01", "sub": [{"w": "Hôm", "s": 0.45, "e": 0.6}, {"w": "nay", "s": 0.6, "e": 0.9}, {"w": "hàng", "s": 0.9, "e": 1.2}]},
 {"id": "s02", "sub": [{"w": "Mặt", "s": 3.05, "e": 3.3}, {"w": "trước", "s": 3.3, "e": 3.8}]}]}
EOF
python3 "$S/phu_de_tung_tu.py" "$V" --font Inter >/dev/null || loi "phu_de_tung_tu.py le ra dat"
D5="$(grep -c '^Dialogue' "$V/phu-de-tung-tu.ass")"; [ "$D5" = 5 ] || loi "phu_de_tung_tu: $D5 su kien, can 5"
grep -qF '0:00:10.00,0:00:10.30,Cap,,,{\c&H0066D1FF&}Mặt{\c&H00FFFFFF&} trước' "$V/phu-de-tung-tu.ass" || loi "phu_de_tung_tu: moc canh s02 khong dich sang moc ghep"
grep -q "^Dialogue" "$V/phu-de-tung-tu.ass" && ! grep -q "^Dialogue: 0,[^,]*,[^,]*,Cap,,0,0,0,," "$V/phu-de-tung-tu.ass" || loi "phu_de_tung_tu: dong Dialogue thua truong"
python3 -I - "$S/phu_de_tung_tu.py" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("pdt", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.kiem_dinh_dang("Dialogue: 0,0:00:01.00,0:00:02.00,Cap,,,Xin chào") == [], "dong dung bi bao loi"
assert m.kiem_dinh_dang("Dialogue: 0,0:00:01.00,0:00:02.00,Cap,,0,0,0,,Xin chào"), "dong thua truong khong bi bat"
assert m.kiem_dinh_dang("Dialogue: 0,0:00:01.00,0:00:02.00,Cap,,,2,5 mét dây cáp") == [], "so thap phan kieu Viet dau cau bi bao nham"
PY
# hai loi cach nhau 0,2 giay: su kien khong duoc chong (tu cuoi s01 keo dai 0,25 giay, tu dau s02 hien som 0,05 giay)
V2="$P/vct2"; mkdir -p "$V2"
echo '{"total": 3.0, "scenes": [{"id": "s01", "start": 0.0, "duration": 1.0}, {"id": "s02", "start": 1.2, "duration": 1.0}]}' > "$V2/timeline.json"
echo '{"start": {"s01": 0.0, "s02": 1.2}, "tong_giay": 3.0}' > "$V2/timeline_ghep.json"
echo '{"scenes": [{"id": "s01", "sub": [{"w": "Một", "s": 0.1, "e": 0.5}, {"w": "hai", "s": 0.5, "e": 1.0}]}, {"id": "s02", "sub": [{"w": "Ba", "s": 1.2, "e": 2.0}]}]}' > "$V2/moc-tu.json"
python3 "$S/phu_de_tung_tu.py" "$V2" --font Inter >/dev/null || loi "phu_de_tung_tu.py (vct2) le ra dat"
python3 -I - "$V2/phu-de-tung-tu.ass" <<'PY'
import sys
def g(x):
    h, m, s = x.split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
ev = sorted((g(d.split(",")[1]), g(d.split(",")[2])) for d in open(sys.argv[1], encoding="utf-8") if d.startswith("Dialogue:"))
assert len(ev) == 3, ev
assert all(e1 <= s2 + 1e-6 for (_, e1), (s2, _) in zip(ev, ev[1:])), f"su kien phu de chong nhau: {ev}"
PY
cat > "$V/sua.srt" <<'EOF'
1
00:00:00,400 --> 00:00:02,000
Hôm nay hàng về, khui ngay!
2
00:00:10,000 --> 00:00:13,000
Mặt trước ghi chữ Belkin, cáp HDMI, dài 2 mét.
EOF
cat > "$V/khang-dinh.json" <<'EOF'
{"khang_dinh": [
 {"canh": "s01", "cau": "Hôm nay hàng về rồi, khui ngay thôi.", "loai": "khong-khang-dinh"},
 {"canh": "s02", "cau": "Mặt trước ghi chữ Belkin, cáp HDMI.", "loai": "nhan", "moc_giay": 43.1, "nhan_doc": "belkin"}]}
EOF
python3 "$S/ap_sua_srt.py" "$V" "$V/sua.srt" >/dev/null || loi "ap_sua_srt xem truoc le ra dat"
grep -q "hàng về rồi" "$V/scenes.json" || loi "ap_sua_srt xem truoc khong duoc ghi"
python3 "$S/ap_sua_srt.py" "$V" "$V/sua.srt" --ap >/dev/null || loi "ap_sua_srt --ap le ra dat"
python3 -I - "$V" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]); sc = json.loads((p / "scenes.json").read_text(encoding="utf-8"))["scenes"]
assert sc[0]["narration"] == "Hôm nay hàng về, khui ngay!" and "subtitle" not in sc[0]
assert sc[1]["subtitle"].endswith("dài 2 mét.") and sc[1]["narration"].startswith("Mặt trước ghi chữ Bel-kin"), "narration cach doc phai giu nguyen"
kd = json.loads((p / "khang-dinh.json").read_text(encoding="utf-8"))["khang_dinh"]
assert kd[0]["loai"] == "chua-phan-loai" and kd[0].get("loai_cu") == "khong-khang-dinh", "cau khong-khang-dinh doi chu phai ve chua-phan-loai"
assert kd[1]["loai"] == "chua-phan-loai" and kd[1].get("nhan_doc") == "belkin", "canh nhan doi chu phai ve chua-phan-loai, giu goi y"
assert (p / "scenes.truoc-sua.json").exists()
PY
expect_fail python3 "$S/so_khang_dinh.py" kiem "$V"
printf '1\n00:00:09,000 --> 00:00:10,000\nSai moc\n' > "$V/lech.srt"
OUT=$(python3 "$S/ap_sua_srt.py" "$V" "$V/lech.srt" 2>&1 || true)
grep -q "lech moc canh" <<<"$OUT" || loi "ap_sua_srt khong bao srt lech moc"
touch -d "2000-01-01" "$V/timeline_ghep.json"
OUT=$(python3 "$S/kiem_loi_doc.py" "$V" 2>&1 || true)
grep -q "timeline_ghep.json cu hon" <<<"$OUT" || loi "kiem_loi_doc khong bao timeline_ghep.json cu"
# scenes.json khac thu tu thoi gian: khoi srt ghep theo moc; cau giu nguyen chu giu muc; canh chua co trong so duoc them muc
V3="$P/vct3"; mkdir -p "$V3"
cat > "$V3/scenes.json" <<'EOF'
{"voice": "Hải Đăng", "scenes": [
 {"id": "s02", "narration": "Cáp dài hai mét. Màu đen.", "visual": "x", "on_screen": {}},
 {"id": "s01", "narration": "Mở hộp ra.", "visual": "x", "on_screen": {}}]}
EOF
echo '{"start": {"s01": 1.0, "s02": 5.0}, "tong_giay": 8.0}' > "$V3/timeline_ghep.json"
cat > "$V3/khang-dinh.json" <<'EOF'
{"khang_dinh": [
 {"canh": "s02", "cau": "Cáp dài hai mét.", "loai": "nhan", "moc_giay": 5.2, "nhan_doc": "2m"},
 {"canh": "s02", "cau": "Màu đen.", "loai": "quan-sat", "moc_giay": 5.5, "xac_nhan": "co"}]}
EOF
printf '1\n00:00:01,000 --> 00:00:02,000\nMở hộp ra, dài 3 mét.\n\n2\n00:00:05,000 --> 00:00:07,000\nCáp dài hai mét. Màu đen nhám.\n' > "$V3/sua.srt"
python3 "$S/ap_sua_srt.py" "$V3" "$V3/sua.srt" --ap >/dev/null 2>&1 || loi "ap_sua_srt (vct3) le ra dat"
python3 -I - "$V3" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1]); sc = {s["id"]: s for s in json.loads((p / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
assert sc["s01"]["narration"] == "Mở hộp ra, dài 3 mét.", "khoi 1 phai vao canh som nhat (s01), khong phai canh dau scenes.json"
assert sc["s02"]["narration"] == "Cáp dài hai mét. Màu đen nhám."
kd = json.loads((p / "khang-dinh.json").read_text(encoding="utf-8"))["khang_dinh"]
s02 = [e for e in kd if e["canh"] == "s02"]
assert s02[0]["loai"] == "nhan" and s02[0]["cau"] == "Cáp dài hai mét.", "cau giu nguyen chu phai giu muc cu"
assert s02[1]["loai"] == "chua-phan-loai" and "xac_nhan" not in s02[1] and s02[1]["loai_cu"] == "quan-sat"
s01 = [e for e in kd if e["canh"] == "s01"]
assert len(s01) == 1 and s01[0]["loai"] == "chua-phan-loai", "canh doi chua co trong so phai duoc them muc"
PY
# kiem_loi_doc truoc khi ghep: hai canh giu hinh lien tiep, canh sau bi day lui boi phan keo dai cua canh truoc (khong bao chong gia)
V4="$P/vct4"; mkdir -p "$V4/audio"
cat > "$V4/scenes.json" <<'EOF'
{"voice": "Hải Đăng", "scenes": [
 {"id": "s05", "narration": "Ảnh thứ nhất.", "visual": "x", "on_screen": {}},
 {"id": "s06", "narration": "Ảnh thứ hai.", "visual": "x", "on_screen": {}}]}
EOF
echo '{"canh": {"s05": {"giu_hinh": {"hien_ro": 41.87, "dong_bang": 44.3}}, "s06": {"giu_hinh": {"hien_ro": 45.05, "dong_bang": 47.3}}}}' > "$V4/job.json"
python3 -I - "$V4" <<'PY'
import sys, numpy as np, soundfile as sf
for k, d in (("s05", 3.7), ("s06", 2.0)):
    sf.write(f"{sys.argv[1]}/audio/{k}.wav", np.zeros(int(d * 48000), np.float32), 48000)
PY
# ffprobe gia (chi cho ca kiem nay, smoke test khong can ffmpeg): in do dai file wav tu header
mkdir -p "$V4/bin"
printf '#!/usr/bin/env python3\nimport sys, wave\nw = wave.open(sys.argv[-1]); print(w.getnframes() / w.getframerate())\n' > "$V4/bin/ffprobe"
chmod +x "$V4/bin/ffprobe"
PATH="$V4/bin:$PATH" python3 "$S/kiem_loi_doc.py" "$V4" > "$V4/kq.txt" 2>&1 || { cat "$V4/kq.txt"; loi "kiem_loi_doc bao chong gia giua hai canh giu hinh lien tiep (chua co timeline_ghep.json)"; }
# kiem_loi_doc: cue tinh tren video goc phai cong phan keo dai cua giu_hinh dung truoc no; loi vuot cuoi video bi chan
V5="$P/vct5"; mkdir -p "$V5/audio" "$V5/bin"
cat > "$V5/scenes.json" <<'EOF'
{"voice": "Hải Đăng", "scenes": [
 {"id": "s01", "narration": "Ảnh giữ hình.", "visual": "x", "on_screen": {}},
 {"id": "s02", "narration": "Cảnh cue sau.", "visual": "x", "on_screen": {}}]}
EOF
echo '{"video_goc": "v.mp4", "canh": {"s01": {"giu_hinh": {"hien_ro": 0.5, "dong_bang": 1.0}}, "s02": {"cue": 2.0}}}' > "$V5/job.json"
: > "$V5/v.mp4"
# ffprobe gia: wav in do dai tu header, file khac (video) in 5.0
printf '#!/usr/bin/env python3\nimport sys, wave\nf = sys.argv[-1]\nif f.endswith(".wav"):\n    w = wave.open(f); print(w.getnframes() / w.getframerate())\nelse:\n    print(5.0)\n' > "$V5/bin/ffprobe"
chmod +x "$V5/bin/ffprobe"
vct5_audio() { python3 -I - "$V5" "$1" <<'PY'
import sys, numpy as np, soundfile as sf
for k, d in (("s01", 2.0), ("s02", float(sys.argv[2]))):
    sf.write(f"{sys.argv[1]}/audio/{k}.wav", np.zeros(int(d * 48000), np.float32), 48000)
PY
}
vct5_audio 1.0
# s01 keo dai 2,0 s (ket thuc 2,65 s); neu cue s02 khong duoc dich thi s02 bat dau 2,0 s va bi bao chong gia
PATH="$V5/bin:$PATH" python3 "$S/kiem_loi_doc.py" "$V5" > "$V5/kq.txt" 2>&1 || { cat "$V5/kq.txt"; loi "kiem_loi_doc khong dich cue theo phan keo dai giu_hinh (bao chong gia)"; }
# video 5 s + keo dai 2 s = 7 s; s02 bat dau 4 s, dai 4 s thi ket thuc 8 s, vuot cuoi video
vct5_audio 4.0
if PATH="$V5/bin:$PATH" python3 "$S/kiem_loi_doc.py" "$V5" > "$V5/kq.txt" 2>&1; then loi "kiem_loi_doc khong chan loi vuot cuoi video"; fi
grep -q "sau cuoi video" "$V5/kq.txt" || loi "kiem_loi_doc thieu thong bao loi vuot cuoi video"
# kiem_loi_doc: anh_tinh_khong_loi canh bao loi tran vao doan anh tinh; check_output --co-san ha loi do phan giai thanh canh bao
V6="$P/vct6"; mkdir -p "$V6/audio" "$V6/bin"
cat > "$V6/scenes.json" <<'EOF'
{"voice": "Hải Đăng", "scenes": [
 {"id": "s01", "narration": "Lời tràn vào ảnh tĩnh.", "visual": "x", "on_screen": {}}]}
EOF
echo '{"video_goc": "v.mp4", "anh_tinh": [{"tu": 5.0, "den": 9.0}], "canh": {"s01": {"cue": 3.0}}}' > "$V6/job.json"
: > "$V6/v.mp4"
printf '#!/usr/bin/env python3\nimport sys, wave\nf = sys.argv[-1]\nif f.endswith(".wav"):\n    w = wave.open(f); print(w.getnframes() / w.getframerate())\nelse:\n    print(20.0)\n' > "$V6/bin/ffprobe"
chmod +x "$V6/bin/ffprobe"
python3 -I - "$V6" <<'PY'
import sys, numpy as np, soundfile as sf
sf.write(f"{sys.argv[1]}/audio/s01.wav", np.zeros(int(3.0 * 48000), np.float32), 48000)
PY
PATH="$V6/bin:$PATH" python3 "$S/kiem_loi_doc.py" "$V6" > "$V6/kq.txt" 2>&1 || { cat "$V6/kq.txt"; loi "kiem_loi_doc loi bat ngo o ca anh_tinh_khong_loi"; }
if grep -q "anh_tinh_khong_loi" "$V6/kq.txt"; then loi "kiem_loi_doc canh bao anh_tinh_khong_loi khi chua bat"; fi
echo '{"video_goc": "v.mp4", "anh_tinh": [{"tu": 5.0, "den": 9.0}], "anh_tinh_khong_loi": true, "canh": {"s01": {"cue": 3.0}}}' > "$V6/job.json"
PATH="$V6/bin:$PATH" python3 "$S/kiem_loi_doc.py" "$V6" > "$V6/kq.txt" 2>&1 || { cat "$V6/kq.txt"; loi "kiem_loi_doc loi bat ngo khi bat anh_tinh_khong_loi"; }
grep -q "anh_tinh_khong_loi" "$V6/kq.txt" || { cat "$V6/kq.txt"; loi "kiem_loi_doc khong canh bao loi tran vao doan anh tinh"; }
# loi ket thuc truoc doan anh tinh (cue 0,5, dai 3 s -> den 3,5 s) thi khong canh bao
echo '{"video_goc": "v.mp4", "anh_tinh": [{"tu": 5.0, "den": 9.0}], "anh_tinh_khong_loi": true, "canh": {"s01": {"cue": 0.5}}}' > "$V6/job.json"
PATH="$V6/bin:$PATH" python3 "$S/kiem_loi_doc.py" "$V6" > "$V6/kq.txt" 2>&1 || { cat "$V6/kq.txt"; loi "kiem_loi_doc loi bat ngo (loi truoc anh tinh)"; }
if grep -q "anh_tinh_khong_loi" "$V6/kq.txt"; then loi "kiem_loi_doc canh bao nham loi ket thuc truoc doan anh tinh"; fi
OUT=$(python3 "$S/check_output.py" --help || true)
grep -q -- "--co-san" <<<"$OUT" || loi "check_output thieu --co-san"
pass "phu_de_tung_tu.py (moc ghep, kiem dinh dang), ap_sua_srt.py (xem truoc, ap, dong bo so khang dinh, srt lech, thu tu theo moc, cau doi chu), phu de khong chong, kiem_loi_doc timeline cu, giu hinh lien tiep, cue sau giu_hinh va loi vuot cuoi video, anh_tinh_khong_loi"

# so_khang_dinh.py dong-bo: sua loi thi giu muc cu cua cau khong doi, cau doi chu ve chua-phan-loai, ban sao truoc khi dong bo
V7="$P/vct7"; mkdir -p "$V7"
cat > "$V7/scenes.json" <<'EOF'
{"voice": "Hải Đăng", "scenes": [
 {"id": "s01", "narration": "Hàng đã về. Túi nguyên vẹn.", "visual": "x", "on_screen": {}},
 {"id": "s02", "narration": "Dây chỉnh được bằng khóa.", "visual": "x", "on_screen": {}}]}
EOF
python3 "$S/so_khang_dinh.py" khoi "$V7" > /dev/null
python3 -I - "$V7" <<'PY'
import json, sys
p = sys.argv[1] + "/khang-dinh.json"
d = json.load(open(p, encoding="utf-8"))
for e in d["khang_dinh"]:
    if e["cau"].startswith("Hàng"):
        e["loai"] = "khong-khang-dinh"
    elif e["cau"].startswith("Túi"):
        e.update({"loai": "quan-sat", "moc_giay": 4.5, "xac_nhan": "co"})
    else:
        e.update({"loai": "quan-sat", "moc_giay": 50.0, "xac_nhan": "co"})
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
sc = json.load(open(sys.argv[1] + "/scenes.json", encoding="utf-8"))
sc["scenes"][0]["narration"] = "Hàng đã về. Túi nguyên vẹn, không móp."
sc["scenes"][1]["narration"] = "Dây chỉnh được bằng khóa."
json.dump(sc, open(sys.argv[1] + "/scenes.json", "w", encoding="utf-8"), ensure_ascii=False)
PY
python3 "$S/so_khang_dinh.py" dong-bo "$V7" > "$V7/kq.txt" || { cat "$V7/kq.txt"; loi "so_khang_dinh dong-bo loi"; }
python3 -I - "$V7" <<'PY' || loi "so_khang_dinh dong-bo: ket qua sai"
import json, sys
d = json.load(open(sys.argv[1] + "/khang-dinh.json", encoding="utf-8"))["khang_dinh"]
by = {e["cau"]: e for e in d}
assert by["Hàng đã về."]["loai"] == "khong-khang-dinh", by
assert by["Dây chỉnh được bằng khóa."]["xac_nhan"] == "co" and by["Dây chỉnh được bằng khóa."]["moc_giay"] == 50.0, by
moi = by["Túi nguyên vẹn, không móp."]
assert moi["loai"] == "chua-phan-loai" and moi.get("loai_cu") == "quan-sat" and "xac_nhan" not in moi, moi
assert len(d) == 3, d
PY
[ -f "$V7/khang-dinh.truoc-dong-bo.json" ] || loi "so_khang_dinh dong-bo khong giu ban sao"
grep -q "CAN PHAN LOAI" "$V7/kq.txt" || loi "so_khang_dinh dong-bo khong liet ke cau can phan loai"
expect_fail python3 "$S/so_khang_dinh.py" kiem "$V7"
pass "so_khang_dinh.py dong-bo (giu muc cu cua cau khong doi, cau doi chu ve chua-phan-loai, ban sao, kiem chan)"

# giao_co_san.py: gom thanh pham video co san, credits sinh tu job.json, thieu kiem-chung.md thi chan
V9="$P/vct9"; mkdir -p "$V9/output"
echo '{"ten": "demo", "giong": "Hải Đăng", "nhac": {"kieu": "nhe-nhang"}, "lam_mo": [{"cach": "tay"}]}' > "$V9/job.json"
for f in demo.mp4 demo-phu-de-tung-tu.mp4; do echo x > "$V9/output/$f"; done
echo 1 > "$V9/output/phu-de.srt"; echo 1 > "$V9/output/loi-doc.md"
printf 'Style: Cap,Inter,64,&H00FFFFFF\n' > "$V9/phu-de-tung-tu.ass"
expect_fail python3 "$S/giao_co_san.py" "$V9"
echo kc > "$V9/kiem-chung.md"
python3 "$S/giao_co_san.py" "$V9" > "$V9/kq.txt" || { cat "$V9/kq.txt"; loi "giao_co_san loi bat ngo"; }
for f in demo_khong-phu-de.mp4 demo_phu-de-tung-tu.mp4 phu-de.srt loi-doc.md kiem-chung.md credits.md; do
  [ -s "$V9/giao/$f" ] || loi "giao_co_san thieu $f"
done
[ ! -e "$V9/giao/demo_chu.mp4" ] || loi "giao_co_san chep file khong co"
grep -q "Hải Đăng" "$V9/giao/credits.md" && grep -q "nhe-nhang" "$V9/giao/credits.md" && grep -q "font Inter" "$V9/giao/credits.md" || loi "giao_co_san: credits thieu giong, nhac hoac font"
grep -q "metadata.md" "$V9/kq.txt" || loi "giao_co_san khong canh bao thieu metadata.md"
pass "giao_co_san.py (gom file, credits tu job.json, chan thieu kiem-chung.md, canh bao thieu metadata.md)"

# nhac_nen.py --doan: nhac chi nghe trong doan chi dinh (can ffmpeg that; bo qua khi may khong co ffmpeg)
if command -v ffmpeg >/dev/null 2>&1; then
  V8="$P/vct8"; mkdir -p "$V8/renders"
  echo '{"total": 10.0, "scenes": []}' > "$V8/timeline.json"
  ffmpeg -v error -y -f lavfi -i testsrc=size=160x90:rate=10:duration=10 -f lavfi -i anullsrc=r=48000:cl=stereo -t 10 \
    -c:v libx264 -pix_fmt yuv420p -c:a aac "$V8/renders/final_t.mp4"
  python3 "$S/nhac_nen.py" "$V8" --kieu nhe-nhang --doan 6,9 "$V8/renders/final_t.mp4" > /dev/null || loi "nhac_nen --doan that bai"
  expect_fail python3 "$S/nhac_nen.py" "$V8" --kieu nhe-nhang --doan 9,6 "$V8/renders/final_t.mp4"
  ffmpeg -v error -y -i "$V8/renders/final_t.mp4" -f f32le -ac 1 -ar 8000 "$V8/a.f32"
  python3 -I - "$V8/a.f32" <<'PY' || loi "nhac_nen --doan: nhac nghe ngoai doan hoac khong nghe trong doan"
import sys, numpy as np
x = np.fromfile(sys.argv[1], dtype=np.float32)
def db(a, b):
    seg = x[int(a * 8000):int(b * 8000)]
    return 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)
assert db(0, 5) < -60 and db(9.2, 10) < -60, (db(0, 5), db(9.2, 10))
assert db(6.5, 8.5) > -45, db(6.5, 8.5)
PY
  pass "nhac_nen.py --doan (nhac chi nghe trong doan, loi tham so)"
else
  echo "[BO QUA] nhac_nen.py --doan: may khong co ffmpeg"
fi

# V10. kiem_khung_lam_mo: diem chu (giay trang co chu in giam manh sau khi mo)
if python3 -I -c 'import cv2' 2>/dev/null; then
python3 -I - "$S" <<'PY'
import sys
import cv2
import numpy as np
sys.path.insert(0, sys.argv[1])
import kiem_khung_lam_mo as k
img = np.full((300, 400, 3), 235, np.uint8)
for y in range(20, 280, 14):
    for x in range(20, 380, 10):
        if (x * 7 + y * 3) % 5 < 3:
            cv2.rectangle(img, (x, y), (x + 5, y + 8), (20, 20, 20), -1)
mo = cv2.GaussianBlur(img, (0, 0), 12)
d0, d1 = k.diem_chu(img), k.diem_chu(mo)
assert d0 >= 12 and d1 < 12, (d0, d1)
assert k.diem_chu(np.full((300, 400, 3), 235, np.uint8)) == 0
PY
  pass "kiem_khung_lam_mo diem_chu (chu ro cao, sau khi mo thap, giay tron bang 0)"
else
  echo "[BO QUA] kiem_khung_lam_mo diem_chu: may khong co opencv"
fi

# may_tinh_tien.py: kiem cau hinh va xuat khung lop phu (can ffmpeg, ffprobe, fc-match, Pillow; render day du da thu tay, xem CHANGELOG)
if command -v ffmpeg >/dev/null 2>&1 && command -v fc-match >/dev/null 2>&1 && python3 -c "import PIL" 2>/dev/null; then
  V10="$P/vct10"; mkdir -p "$V10/src"
  ffmpeg -v error -y -f lavfi -i testsrc=size=160x284:rate=10:duration=30 -c:v libx264 -pix_fmt yuv420p "$V10/src/v.mp4"
  cat > "$V10/tien-bay.json" <<'EOF2'
{"video": "src/v.mp4", "ngay": "01/01/2026", "tong_hoa_don": 150000,
 "mo_dau": {"tu": 1.0, "dai": 3.0}, "ket": {"nen_tu": 2.0, "dai": 9.0},
 "mon": [
  {"ten": "Mon dat", "so_luong": 2, "gia": 100000, "nhom": "A", "chia": {"so": 8, "don_vi": "cai"}, "anh": {"tu": 5.0, "dai": 4.0}},
  {"ten": "Mon re", "so_luong": 1, "gia": 50000, "nhom": "B", "mo": {"tu": 10.0, "dai": 2.0}, "anh": {"tu": 13.0, "dai": 3.2}}]}
EOF2
  python3 "$S/may_tinh_tien.py" "$V10" kiem > "$V10/kq.txt" || loi "may_tinh_tien kiem that bai tren cau hinh dung"
  python3 "$S/may_tinh_tien.py" "$V10" khung > /dev/null || loi "may_tinh_tien khung that bai"
  [ "$(ls "$V10"/qa/tien-bay/khung_*.png | wc -l)" -ge 5 ] || loi "may_tinh_tien khung: thieu anh"
  sed 's/"tong_hoa_don": 150000/"tong_hoa_don": 140000/' "$V10/tien-bay.json" > "$V10/x.json"
  cp "$V10/tien-bay.json" "$V10/ok.json"; cp "$V10/x.json" "$V10/tien-bay.json"
  expect_fail python3 "$S/may_tinh_tien.py" "$V10" kiem
  sed 's/"tu": 13.0, "dai": 3.2/"tu": 29.0, "dai": 3.2/' "$V10/ok.json" > "$V10/tien-bay.json"
  expect_fail python3 "$S/may_tinh_tien.py" "$V10" kiem
  sed 's/"dai": 4.0}/"dai": 2.0}/' "$V10/ok.json" > "$V10/tien-bay.json"
  expect_fail python3 "$S/may_tinh_tien.py" "$V10" kiem
  sed 's/"nen_tu": 2.0/"nen_tu": 45.0/' "$V10/ok.json" > "$V10/tien-bay.json"
  expect_fail python3 "$S/may_tinh_tien.py" "$V10" kiem
  sed 's/"tu": 1.0, "dai": 3.0/"tu": -1.0, "dai": 3.0/' "$V10/ok.json" > "$V10/tien-bay.json"
  expect_fail python3 "$S/may_tinh_tien.py" "$V10" kiem
  pass "may_tinh_tien.py (kiem dung, xuat khung, chan tong lech, doan cat vuot video, the gia qua ngan, nen ket ngoai video, tu am)"
else
  echo "[BO QUA] may_tinh_tien.py: may thieu ffmpeg, fc-match hoac Pillow"
fi

# 5d. Danh muc mo hinh ASR bo sung (asr-models.json) va nhan dang ngon ngu (lid-models.json): kich thuoc, sha256,
#     parts, tep giay phep, ten ban khong trung giua hai danh muc (khong can mang)
for DM in asr-models.json lid-models.json; do
python3 -I - "$ROOT" "$DM" <<'PY'
import json, re, sys
from pathlib import Path
root = Path(sys.argv[1]); m = json.load(open(root / "video-studio/assets" / sys.argv[2]))
bans = {s["dir"] for s in m["sources"].values()}
assert m["release_tag"] and "{tag}" in m["release_url"] and "{asset}" in m["release_url"]
for s in m["sources"].values():
    assert re.fullmatch(r"[0-9a-f]{40}", s["revision"]), s
    assert (root / "video-studio/references" / s["license_file"]).exists(), s["license_file"]
for f in m["files"]:
    assert f["path"].split("/")[0] in bans and f["repo"] in m["sources"], f["path"]
    assert re.fullmatch(r"[0-9a-f]{64}", f["sha256"]) and f["size"] > 0, f["path"]
    if f["size"] >= 2 << 30:
        assert f.get("parts"), f["path"] + ": file tu 2 GiB tro len phai chia parts"
    if f.get("parts"):
        assert sum(p["size"] for p in f["parts"]) == f["size"], f["path"]
        assert all(p["size"] < 2 << 30 and re.fullmatch(r"[0-9a-f]{64}", p["sha256"]) for p in f["parts"]), f["path"]
assert len({f["asset"] for f in m["files"]}) == len(m["files"])
PY
pass "$DM (kich thuoc, sha256, parts duoi 2 GiB, revision 40 ky tu, tep giay phep)"
done
python3 -I - "$ROOT" <<'PY'
import json, sys
from pathlib import Path
a = Path(sys.argv[1]) / "video-studio/assets"
ban = [{s["dir"] for s in json.load(open(a / t))["sources"].values()} for t in ("asr-models.json", "lid-models.json")]
tag = [json.load(open(a / t))["release_tag"] for t in ("asr-models.json", "lid-models.json")]
assert not (ban[0] & ban[1]) and tag[0] != tag[1], (ban, tag)
PY
pass "asr-models.json va lid-models.json khong trung ban, khong trung release"

# 5e. nhan_dang_lid.py: cat khuc va bau ngon ngu (khong can torch, mo hinh)
python3 -I - "$S" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from nhan_dang_lid import bau, chia_khuc
assert chia_khuc([(0, 0.5), (1, 71)]) == [(1, 31), (31, 61), (61, 71)]
assert chia_khuc([(0, 30.5)]) == [(0, 30.0)]          # phan du duoi 1 giay bi bo
k = [{"tu": 0, "den": 10, "ngon_ngu": "zh", "tin": 0.95}, {"tu": 10, "den": 12, "ngon_ngu": "en", "tin": 0.2},
     {"tu": 12, "den": 15, "ngon_ngu": "en", "tin": 0.9}]
r = bau(k)
assert r["chon"] == "zh" and r["giay_tin_cay"] == 13 and r["tong"] == {"zh": 10, "en": 3}, r
assert bau([{"tu": 0, "den": 5, "ngon_ngu": "ja", "tin": 0.3}])["chon"] is None
PY
pass "nhan_dang_lid.py (cat khuc toi da 30 giay, bo khuc do tin thap khi bau)"

# 5d. doc_van_ban.py tach: muc luc bi bo, ***, ky hieu, doan van, cach doc, canh, doc thieu nguon
python3 -I - "$S/doc_van_ban.py" "$P" <<'PY'
import json, subprocess, sys
from pathlib import Path
script, p = sys.argv[1], Path(sys.argv[2]) / "dv"
p.mkdir()
body1 = ("Y mở mắt ra, thấy trần nhà trắng.\nMột mình y nằm đó.\n“Ngươi là ai?”\nY hỏi nhỏ.\n"
         "Đồ *** này, ta ★ tới đây.\n" + "Câu dài để đủ nội dung cho chương một. " * 8)
body2 = "Sáng hôm sau, VieNeu lên đường.\n" + "Chương hai có đủ chữ để không bị coi là mục lục. " * 8
(p / "n.txt").write_text(
    "TRUYỆN THỬ\nDTV-EBOOK.COM\nMục Lục\nChương 1: Mở đầu\nChương 2: Lên đường\n\n\fChương 1: Mở đầu\n" + body1 +
    "\n\fChương 2: Lên đường\n" + body2 + "\n", encoding="utf-8")
(p / "cd.txt").write_text("VieNeu => viu niu\n", encoding="utf-8")
out = p / "du-an"
subprocess.run([sys.executable, script, "tach", str(p / "n.txt"), str(out), "--cach-doc", str(p / "cd.txt"),
                "--giong", "Mai Anh"], check=True, capture_output=True)
muc = json.loads((out / "muc-luc.json").read_text(encoding="utf-8"))
assert [m["so"] for m in muc] == [1, 2], muc                     # muc luc khong thanh chuong
sc = json.loads((out / "chuong-0001" / "scenes.json").read_text(encoding="utf-8"))
assert sc["voice"] == "Mai Anh" and sc["scenes"][0]["narration"] == "Chương 1. Mở đầu."
n1 = sc["scenes"][1]["narration"]
assert "***" not in n1 and "★" not in n1, n1
assert "\n\n“Ngươi là ai?”" in n1 or n1.startswith("Y mở mắt"), n1     # doan van duoc dung lai
assert "Một mình y nằm đó." in n1.replace("\n", " ")
sc2 = json.loads((out / "chuong-0002" / "scenes.json").read_text(encoding="utf-8"))
assert "viu niu" in sc2["scenes"][1]["narration"] and "VieNeu" not in sc2["scenes"][1]["narration"]
assert "VieNeu" in (out / "chuong-0002" / "van-ban.txt").read_text(encoding="utf-8")    # van ban goc giu nguyen
bc = (out / "cach-doc.md").read_text(encoding="utf-8")
assert "DTV-EBOOK.COM" in bc and "***" in bc, bc                  # da bo gi duoc ghi lai
r = subprocess.run([sys.executable, script, "tach", str(p / "khong-co.txt"), str(out)], capture_output=True)
assert r.returncode != 0
r = subprocess.run([sys.executable, script, "doc", str(p / "chua-tach")], capture_output=True)
assert r.returncode != 0
PY
pass "doc_van_ban.py tach (muc luc, ***, ky hieu, doan van, cach doc chi ap vao scenes.json, bao cao, thieu nguon)"

# 6. Script shell: cu phap
for f in "$S"/*.sh "$ROOT"/tools/*.sh; do bash -n "$f"; done
pass "cu phap script shell"
echo "Tat ca dat."
