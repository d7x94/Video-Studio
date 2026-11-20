#!/usr/bin/env python3
"""Che do dich: doc chu tren hinh (phu de cung, thuc don, bien hieu) bang RapidOCR de doi chieu voi ban chep Whisper.

Dung:
  python3 chu_tren_hinh.py VIDEO PROJECT              # doc PROJECT/dich/chep-goc.json (da chay chep_loi_goc.py)
  python3 chu_tren_hinh.py VIDEO PROJECT --luong 2

Dau ra trong PROJECT/dich/:
  chu-tren-hinh.json  tung doan (khung da doc, dong chu khop nhat, cho khac), danh sach dong chu da thay
  chu-tren-hinh.md    bang de nguoi dung duyet: doan Whisper khac dong chu tren hinh khop voi no; danh sach dong
                      chu khong khop doan nao (thuc don, bien hieu, phu de ngon ngu khac)

Vi sao: hai mo hinh chep loi co the cung nghe sai mot tu (da gap: Whisper va FireRed cung nghe "port panini", phu de
cung cua video ghi "pork panini"); kiem cheo giua hai mo hinh khong bat duoc, chu tren hinh thi bat duoc.

Cach lam:
  1. Tham do: doc 5 khung rai deu trong cac doan co loi; khong thay dong chu nao do tin >= 0,8 thi dung, ghi
     "khong co chu tren hinh" (video khong co phu de, bien hieu: khoi ton thoi gian).
  2. Moi doan Whisper doc khung o giua doan; doan dai hon 4 giay doc them khung o 1/4 va 3/4.
  3. Moi dong chu (do tin >= 0,8) so voi loi Whisper cua doan truoc, doan nay va doan sau noi lai (phu de va doan
     Whisper khong cat cung cho; tach tu nhu chep_loi_firered.py: tieng Anh theo tu, tieng Trung theo chu, gian the).
     Cho khac gan cho doan chua tu Whisper bi thay. Dong chu duoc coi la khop doan khi co it nhat 3 tu (tieng Trung: 4 chu) trung
     va trung it nhat 60% so tu cua dong. Chi so phan dong chu nam trong khoang trung (bo phan thua hai dau: phu
     de va doan Whisper khong cat cung cho). Bao cho thay the ngan (moi ben toi da 3 tu), bo cho chi khac cach tach tu.
  4. Neu co chep-firered.json: ghi kem cho KHAC cua FireRed de nguoi duyet xem chu tren hinh ung ben nao.
Chi la goi y cho nguoi duyet, khong tu sua ban chep. Phu de cung co the chinh no viet sai hoac viet khac loi noi.

Mo hinh: RapidOCR (goi pip rapidocr, ban ghim trong setup.sh --dich), mo hinh PP-OCRv6 small di kem goi (khong tai
them). Do 2026-11-20 (2 loi CPU): khoang 1,3 giay moi khung 1280x720, 2,6 giay moi khung 1080x1920.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from chep_loi_firered import noi, tach  # noqa: E402  (cung cach tach tu voi kiem cheo FireRed)

NGUONG_TIN = 0.8
TOI_THIEU = {"zh": 4, "khac": 3}   # so tu (chu) trung toi thieu de coi dong chu khop doan
TY_LE = 0.6
TOI_DA_THAY = 3


def doc_khung(video: Path, t: float, out: Path) -> Path:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", str(out)],
                   check=True)
    return out


def ocr_dong(eng, anh: Path) -> list:
    r = eng(str(anh))
    return [(t, round(float(s), 3)) for t, s in zip(r.txts or [], r.scores or []) if float(s) >= NGUONG_TIN and t.strip()]


def so_dong(w: list, dong: list, la_zh: bool):
    """So loi Whisper (da tach) voi mot dong chu. Tra ve (khop, [(i1, i2, whisper, chu)]) hoac (False, []);
    i1, i2 la vi tri tu Whisper bi thay (de gan cho dung doan)."""
    if not w or not dong:
        return False, []
    sm = SequenceMatcher(None, w, dong, autojunk=False)
    khop = [m for m in sm.get_matching_blocks() if m.size]
    trung = sum(m.size for m in khop)
    if trung < TOI_THIEU["zh" if la_zh else "khac"] or trung < TY_LE * len(dong):
        return False, []
    a0, a1 = khop[0].a, khop[-1].a + khop[-1].size
    b0, b1 = khop[0].b, khop[-1].b + khop[-1].size
    cho = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, w[a0:a1], dong[b0:b1], autojunk=False).get_opcodes():
        if op != "replace" or i2 - i1 > TOI_DA_THAY or j2 - j1 > TOI_DA_THAY:
            continue
        x, y = w[a0 + i1:a0 + i2], dong[b0 + j1:b0 + j2]
        if "".join(x) != "".join(y):
            cho.append((a0 + i1, a0 + i2, noi(x), noi(y)))
    return True, cho


def moc_doc(d: dict) -> list:
    s, e = d["start"], d["end"]
    if e - s > 4.0:
        return [s + (e - s) * k for k in (0.25, 0.5, 0.75)]
    return [(s + e) / 2]


def ghi_md(path: Path, kq: dict):
    lines = [f"# Chữ trên hình: {kq['video']}", ""]
    if not kq["co_chu"]:
        lines += ["Không thấy chữ trên hình ở các khung thăm dò (độ tin từ 0,8). Bỏ qua bước đối chiếu chữ trên hình."]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    lines += [f"- Mô hình: RapidOCR (PP-OCRv6 small); {kq['so_khung']} khung đã đọc. Chỉ là gợi ý: phụ đề cứng "
              "cũng có thể viết sai hoặc viết khác lời nói.",
              "- Bảng dưới chỉ có các đoạn mà lời Whisper khác dòng chữ trên hình khớp với nó. Cột Chỗ khác ghi "
              "`Whisper / chữ trên hình`.", "",
              "| Mã | Giây | Whisper | Chữ trên hình | Chỗ khác | FireRed KHÁC |", "|---|---|---|---|---|---|"]
    for d in kq["doan"]:
        if d["cho_khac"]:
            lines.append(f"| {d['id']} | {d['start']:.1f}-{d['end']:.1f} | {d['whisper'].replace('|', '/')} | "
                         f"{' / '.join(d['dong_khop']).replace('|', '/')} | "
                         f"{'; '.join(f'{a} / {b}' for a, b in d['cho_khac']).replace('|', '/')} | "
                         f"{'; '.join(d.get('firered', [])).replace('|', '/')} |")
    n = sum(1 for d in kq["doan"] if d["dong_khop"])
    lines += ["", f"{n}/{len(kq['doan'])} đoạn có dòng chữ khớp (phụ đề cứng cùng ngôn ngữ); "
              f"{sum(1 for d in kq['doan'] if d['cho_khac'])} đoạn khác chữ.", "",
              "Dòng chữ khác đã thấy, không khớp đoạn nào (giây đầu tiên thấy; thực đơn, biển hiệu, tên riêng, phụ đề "
              "ngôn ngữ khác): đọc lướt để sửa tên riêng, món ăn mà hai mô hình chép sai.", ""]
    for c in kq["chu"]:
        lines.append(f"- {c['t']:.1f}: {c['text']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("project")
    ap.add_argument("--luong", type=int, default=2, help="so luong CPU (mac dinh 2)")
    a = ap.parse_args()

    video, proj = Path(a.video), Path(a.project)
    goc_path = proj / "dich" / "chep-goc.json"
    if not goc_path.exists():
        sys.exit(f"[LOI] Chua co {goc_path}: chay chep_loi_goc.py truoc.")
    goc = json.loads(goc_path.read_text(encoding="utf-8"))
    try:
        from rapidocr import RapidOCR
    except ImportError:
        sys.exit("[LOI] Chua cai rapidocr. Chay: bash SKILL/scripts/setup.sh --dich")
    eng = RapidOCR(params={"Global.log_level": "error", "EngineConfig.onnxruntime.intra_op_num_threads": a.luong})
    la_zh = goc["ngon_ngu"].get("chon") in ("zh", "yue")
    fr = {}
    fr_path = proj / "dich" / "chep-firered.json"
    if fr_path.exists():
        for d in json.loads(fr_path.read_text(encoding="utf-8"))["doan"]:
            if d.get("khac"):
                fr[d["id"]] = d.get("cho_khac", [])
    doan = goc["doan"]
    kq = {"phien_ban": 1, "video": video.name, "mo_hinh": "RapidOCR (PP-OCRv6 small)", "co_chu": False,
          "so_khung": 0, "doan": [], "chu": []}
    out = proj / "dich"
    with tempfile.TemporaryDirectory() as tmp:
        cache = {}

        def doc(t):
            t = round(t, 1)
            if t not in cache:
                cache[t] = ocr_dong(eng, doc_khung(video, t, Path(tmp) / "k.png"))
            return cache[t]

        if doan:
            tham = [(doan[int(i * (len(doan) - 1) / 4)]["start"] + doan[int(i * (len(doan) - 1) / 4)]["end"]) / 2
                    for i in range(5)]
            kq["co_chu"] = any(doc(t) for t in tham)
        if not kq["co_chu"]:
            kq["so_khung"] = len(cache)
            (out / "chu-tren-hinh.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
            ghi_md(out / "chu-tren-hinh.md", kq)
            print(f"[OK] dich/chu-tren-hinh.md: khong thay chu tren hinh ({len(cache)} khung tham do)")
            return
        tu = [tach(d["goc"]) for d in doan]
        dong_khop = [[] for _ in doan]
        cho = [[] for _ in doan]
        for k, d in enumerate(doan):
            # phu de va doan Whisper khong cat cung cho: so dong chu voi loi cua doan truoc, doan nay, doan sau
            ks = [x for x in (k - 1, k, k + 1) if 0 <= x < len(doan)]
            w, ai = [], []
            for x in ks:
                w += tu[x]
                ai += [x] * len(tu[x])
            for t in moc_doc(d):
                for txt, _ in doc(t):
                    ok, c = so_dong(w, tach(txt), la_zh)
                    if not ok:
                        continue
                    for x in sorted(set(ai[i] for i1, i2, _, _ in c for i in range(i1, i2)) | {k}):
                        if txt not in dong_khop[x] and (x == k or any(ai[i1] == x for i1, _, _, _ in c)):
                            dong_khop[x].append(txt)
                    for i1, i2, a_, b_ in c:
                        if (a_, b_) not in cho[ai[i1]]:
                            cho[ai[i1]].append((a_, b_))
        for k, d in enumerate(doan):
            kq["doan"].append({"id": d["id"], "start": d["start"], "end": d["end"], "whisper": d["goc"],
                               "dong_khop": dong_khop[k], "cho_khac": cho[k], "firered": fr.get(d["id"], [])})
        da_khop = {x for d in kq["doan"] for x in d["dong_khop"]}
        thay = {}
        for t in sorted(cache):
            for txt, _ in cache[t]:
                if txt not in da_khop:
                    thay.setdefault(txt, t)
        kq["chu"] = [{"t": t, "text": txt} for txt, t in sorted(thay.items(), key=lambda x: x[1])]
        kq["so_khung"] = len(cache)
    (out / "chu-tren-hinh.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    ghi_md(out / "chu-tren-hinh.md", kq)
    n = sum(1 for d in kq["doan"] if d["dong_khop"])
    m = sum(1 for d in kq["doan"] if d["cho_khac"])
    print(f"[OK] dich/chu-tren-hinh.md: {kq['so_khung']} khung, {n}/{len(doan)} doan co dong chu khop, "
          f"{m} doan khac chu tren hinh, {len(kq['chu'])} dong chu khong khop doan nao")


if __name__ == "__main__":
    main()
