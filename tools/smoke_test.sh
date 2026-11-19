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
python3 "$S/ap_sua_srt.py" "$V" "$V/lech.srt" 2>&1 | grep -q "lech moc canh" || loi "ap_sua_srt khong bao srt lech moc"
touch -d "2000-01-01" "$V/timeline_ghep.json"
python3 "$S/kiem_loi_doc.py" "$V" 2>&1 | grep -q "timeline_ghep.json cu hon" || loi "kiem_loi_doc khong bao timeline_ghep.json cu"
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
pass "phu_de_tung_tu.py (moc ghep, kiem dinh dang), ap_sua_srt.py (xem truoc, ap, dong bo so khang dinh, srt lech, thu tu theo moc, cau doi chu), phu de khong chong, kiem_loi_doc timeline cu, giu hinh lien tiep, cue sau giu_hinh va loi vuot cuoi video"

# 6. Script shell: cu phap
for f in "$S"/*.sh "$ROOT"/tools/*.sh; do bash -n "$f"; done
pass "cu phap script shell"
echo "Tat ca dat."
