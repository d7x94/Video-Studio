#!/usr/bin/env python3
"""Che do dich: chep lai loi goc bang FireRedASR2-AED (int8, ONNX, sherpa-onnx) de doi chieu voi Whisper.

Dung:
  python3 chep_loi_firered.py VIDEO PROJECT              # doc PROJECT/dich/chep-goc.json (da chay chep_loi_goc.py)
  python3 chep_loi_firered.py VIDEO PROJECT --luong 2    # so luong CPU

Dau ra trong PROJECT/dich/:
  chep-firered.json   cum (nhom doan lien nhau, toi da 30 giay) va doan (id, loi Whisper, loi FireRed khi doc rieng doan)
  chep-firered.md     bang doi chieu de nguoi dung duyet; dong KHAC la doan ma loi Whisper khong nam trong ban
                      chep FireRed cua ca cum (hai mo hinh nghe khac nhau)

Khong ghi de chep-goc.json: day chi la nguon doi chieu bo sung, nguoi duyet quyet dinh lay ben nao.
FireRedASR2 ho tro tieng Trung (pho thong va hon 20 giong dia phuong) va tieng Anh; ngon ngu khac thi dung lai.
Moi cum dung nguyen am thanh trong cua so. Doan cat rieng hay lan chu cua doan ben canh (mep cat) va co the cho
ket qua khac cum (da gap tren mot clip 27 giay: cum doc "吹头发", cat rieng doan lai ra "吃豆腐"), nen ca hai
deu duoc ghi, nhung co KHAC chi dua tren cum: loi Whisper khong nam trong ban chep cua cum thi moi bao khac.
Mo hinh: scripts/lay_asr.py firered2 (GitHub Release, du phong HuggingFace, kiem sha256).
So sanh KHAC: ca hai ben chuyen ve chu Han gian the bang OpenCC (t2s) truoc khi so, vi Whisper hay chep tieng
pho thong bang phon the con FireRed ra gian the. Bang .md van giu nguyen chu cua tung mo hinh. Chua quy doi so
(Whisper "3", FireRed "三" van bao KHAC).
Can: pip install sherpa-onnx opencc (ban ghim trong setup.sh, chay: bash setup.sh --firered). AED gioi han 60 giay moi lan
doc; script dung cua so toi da 30 giay.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 16000
DEM = 0.2        # giay them hai dau moi doan khi cat rieng
CUA_SO = 30.0    # giay toi da cho mot cum
HO_TRO = ["zh", "en"]
SCRIPTS = Path(__file__).resolve().parent


def doc_tieng(video: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def thu_muc_mo_hinh() -> Path:
    r = subprocess.run([sys.executable, str(SCRIPTS / "lay_asr.py"), "firered2"], capture_output=True, text=True)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        sys.exit(r.returncode)
    return Path(r.stdout.strip().splitlines()[-1])


_T2S = None


def chuan(s: str) -> str:
    """Chuyen ve gian the (OpenCC t2s), chi giu chu, so de so sanh (bo dau cau, khoang trang)."""
    global _T2S
    if _T2S is None:
        import opencc
        _T2S = opencc.OpenCC("t2s")
    return re.sub(r"[^\w]", "", _T2S.convert(s), flags=re.UNICODE).lower()


def gom_cum(doan):
    cum, cur = [], []
    for d in doan:
        if cur and d["end"] - cur[0]["start"] + 2 * DEM > CUA_SO:
            cum.append(cur)
            cur = []
        cur.append(d)
    if cur:
        cum.append(cur)
    return cum


def ghi_md(path: Path, kq):
    lines = [f"# Đối chiếu FireRedASR2: {kq['video']}", "",
             "- Mô hình: FireRedASR2-AED int8 (ONNX, sherpa-onnx). Bản này chỉ để đối chiếu với Whisper, không thay bản chép gốc.",
             "- Cột FireRed (đoạn riêng) là đoạn cắt rời, hay lẫn chữ của đoạn bên cạnh và có thể nghe khác cụm; chỉ để tham khảo.",
             "- Cột Khác báo KHÁC khi lời Whisper không nằm trong bản chép FireRed của cả cụm (bỏ dấu câu, khoảng trắng, "
             "đổi cả hai bên về giản thể). Chưa quy đổi số: \"3\" và \"三\" vẫn báo KHÁC.",
             "", "| Mã | Giây | Whisper | FireRed (đoạn riêng) | Khác |", "|---|---|---|---|---|"]
    for d in kq["doan"]:
        lines.append(f"| {d['id']} | {d['start']:.1f}-{d['end']:.1f} | {d['whisper'].replace('|', '/')} | "
                     f"{d['firered_doan'].replace('|', '/')} | {'KHÁC' if d['khac'] else ''} |")
    lines += ["", "Cụm (FireRed nghe liền nhau):", ""]
    for c in kq["cum"]:
        lines.append(f"- {c['start']:.1f}-{c['end']:.1f} ({', '.join(c['ids'])}): {c['text']}")
    lines += ["", "Chỗ KHÁC cần người nghe lại (hoặc người biết ngôn ngữ) quyết định; không tự sửa bản chép gốc theo FireRed."]
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
    ngon_ngu = goc["ngon_ngu"].get("chon")
    if ngon_ngu not in HO_TRO:
        sys.exit(f"[LOI] Ngon ngu {ngon_ngu} ngoai danh sach FireRedASR2 ho tro {HO_TRO}.")
    try:
        import opencc  # noqa: F401  (dung trong chuan)
        import sherpa_onnx
    except ImportError as e:
        sys.exit(f"[LOI] Thieu {e.name}: chay bash setup.sh --firered")

    md = thu_muc_mo_hinh()
    rec = sherpa_onnx.OfflineRecognizer.from_fire_red_asr(
        encoder=str(md / "encoder.int8.onnx"), decoder=str(md / "decoder.int8.onnx"),
        tokens=str(md / "tokens.txt"), num_threads=a.luong)
    x = doc_tieng(video)
    dur = len(x) / SR

    def chay(t0, t1):
        t0, t1 = max(0.0, t0), min(dur, t1)
        s = rec.create_stream()
        s.accept_waveform(SR, x[int(t0 * SR):int(t1 * SR)])
        rec.decode_stream(s)
        return s.result.text.strip()

    cum_kq, cum_cua = [], {}
    for c in gom_cum(goc["doan"]):
        txt = chay(c[0]["start"] - DEM, c[-1]["end"] + DEM)
        cum_kq.append({"ids": [d["id"] for d in c], "start": round(c[0]["start"], 2), "end": round(c[-1]["end"], 2),
                       "text": txt})
        for d in c:
            cum_cua[d["id"]] = txt
    doan_kq = []
    for d in goc["doan"]:
        t = chay(d["start"] - DEM, d["end"] + DEM)
        doan_kq.append({"id": d["id"], "start": d["start"], "end": d["end"], "whisper": d["goc"],
                        "firered_doan": t, "khac": chuan(d["goc"]) not in chuan(cum_cua[d["id"]])})
    kq = {"phien_ban": 1, "video": video.name, "mo_hinh": "FireRedASR2-AED int8 (sherpa-onnx)",
          "cum": cum_kq, "doan": doan_kq}
    (proj / "dich").mkdir(parents=True, exist_ok=True)
    (proj / "dich" / "chep-firered.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    ghi_md(proj / "dich" / "chep-firered.md", kq)
    n = sum(d["khac"] for d in doan_kq)
    print(f"[OK] dich/chep-firered.json: {len(cum_kq)} cum, {len(doan_kq)} doan, {n} doan khac Whisper (xem chep-firered.md)")


if __name__ == "__main__":
    main()
