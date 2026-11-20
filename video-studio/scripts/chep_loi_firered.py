#!/usr/bin/env python3
"""Che do dich: chep lai loi goc bang FireRedASR2-AED (int8, ONNX, sherpa-onnx) de doi chieu voi Whisper.

Dung:
  python3 chep_loi_firered.py VIDEO PROJECT              # doc PROJECT/dich/chep-goc.json (da chay chep_loi_goc.py)
  python3 chep_loi_firered.py VIDEO PROJECT --luong 2    # so luong CPU

Dau ra trong PROJECT/dich/:
  chep-firered.json   cum (nhom doan lien nhau, toi da 30 giay) va doan (id, loi Whisper, loi FireRed khi doc rieng doan)
  chep-firered.md     bang doi chieu de nguoi dung duyet; dong KHAC la doan ma loi Whisper khac ban chep FireRed
                      cua ca cum (hai mo hinh nghe khac nhau), cot Cho khac ghi dung tu, chu khac nhau; muc
                      "Loi trong khoang trong" la loi FireRed nghe duoc o khoang Whisper khong co doan nao

Khong ghi de chep-goc.json: day chi la nguon doi chieu bo sung, nguoi duyet quyet dinh lay ben nao.
FireRedASR2 ho tro tieng Trung (pho thong va hon 20 giong dia phuong) va tieng Anh; ngon ngu khac thi dung lai.
Moi cum dung nguyen am thanh trong cua so. Doan cat rieng hay lan chu cua doan ben canh (mep cat) va co the cho
ket qua khac cum (da gap tren mot clip 27 giay: cum doc "吹头发", cat rieng doan lai ra "吃豆腐"), nen ca hai
deu duoc ghi, nhung co KHAC chi dua tren cum.
So KHAC: tach tu (tieng Anh theo tu, tieng Trung theo chu), giong hang loi Whisper cua ca cum voi ban FireRed cua cum
(difflib), cho nao khac thi gan cho doan Whisper chua cho do (FireRed nghe them tu o ranh gioi hai doan thi gan cho
doan truoc). So theo tu de "bend" khong bi coi la khop voi "spend" (so theo chuoi chu lien thi "bend" nam trong
"spend"). Hai ben chi khac cach tach tu ("beef balls" / "beefballs") thi coi la khop.
Khoang trong: khoang tu 2 giay tro len khong co doan Whisper nao (khoang_trong trong chep-goc.json) duoc cho FireRed
nghe lai theo cua so 8 giay; co loi thi ghi vao muc rieng. Da gap: Whisper (co VAD) bo cau "here's some asmr typing"
noi nho tren nen go phim; FireRed nghe duoc voi cua so 6 den 10 giay, cua so 30 giay chi ra "<sil>", cua so 14 giay
ra cau do kem "LA LA LA..." lap (do 2026-11-20). Bo qua ket qua "<sil>", chi co tieng dem (嗯, 呃, tro tu) hoac lap
mot hai tu tu 6 lan tro len (nghi bia).
Mo hinh: scripts/lay_asr.py firered2 (GitHub Release, du phong HuggingFace, kiem sha256).
So sanh KHAC: ca hai ben chuyen ve chu Han gian the bang OpenCC (t2s) truoc khi so, vi Whisper hay chep tieng
pho thong bang phon the con FireRed ra gian the. Bang .md van giu nguyen chu cua tung mo hinh. Chua quy doi so
(Whisper "3", FireRed "三" van bao KHAC).
Tro tu cuoi cau (啊 呀 吧 呢 哦 嘛 啦 哈 呗 哟 嘿 诶): doan Whisper khac cum chi vi tro tu o cuoi (vd Whisper "好帅啊",
FireRed "好帅呀") thi khong bao KHAC ma danh dau "chi_tro_tu" (cot Khac ghi "trợ từ"): khong doi nghia, khong can nghe
lai. Chi bo tro tu o cuoi doan Whisper, khong bo giua cau (哈 trong 哈尔滨 van giu). Da gap tren mot clip 18,6 giay:
ca 2 dong KHAC deu chi khac 啊 va 呀.
Can: faster-whisper, sherpa-onnx, opencc (ban ghim trong setup.sh; bash setup.sh --dich cai ca ba). AED gioi han 60 giay moi lan
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
CUA_TRONG = 8.0  # giay moi lan nghe lai khoang trong (cua so dai hon FireRed hay ra "<sil>" hoac lap chu)
DEM_TIENG = "嗯呃唔额"  # tieng dem: chi co nhung tieng nay (va tro tu) o khoang trong thi khong bao
HO_TRO = ["zh", "en"]
TRO_TU = "啊呀吧呢哦嘛啦哈呗哟嘿诶"
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
    """Chuyen ve gian the (OpenCC t2s) va chu thuong; giu khoang trang de tach tu tieng Anh."""
    global _T2S
    if _T2S is None:
        import opencc
        _T2S = opencc.OpenCC("t2s")
    return _T2S.convert(s).lower()


def tach(s: str) -> list:
    """Tach tu de so: tieng Anh (chu Latin, so) theo tu, chu Han tung chu; bo dau cau, khoang trang."""
    return [t.strip("'") for t in re.findall(r"[a-z0-9']+|[^\W_a-z0-9]", chuan(s)) if t.strip("'")]


def noi(tu: list) -> str:
    """Noi tu de hien: chu Han viet lien, tu Latin cach nhau."""
    out = ""
    for t in tu:
        if out and (t[0].isascii() or out[-1].isascii()):
            out += " "
        out += t
    return out


def giong(w: list, c: list) -> list:
    """Cac cho khac giua hai day tu: (i1, i2, j1, j2). Bo cho chi khac cach tach tu ("beef balls" / "beefballs")."""
    from difflib import SequenceMatcher
    out = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, w, c, autojunk=False).get_opcodes():
        if op == "equal" or "".join(w[i1:i2]) == "".join(c[j1:j2]):
            continue
        out.append((i1, i2, j1, j2))
    return out


def chi_tro_tu(w: list, c: list, cho: list) -> bool:
    """Moi cho khac deu chi la tro tu o cuoi doan Whisper (ben FireRed cung chi la tro tu hoac khong co)."""
    if not cho or not [t for t in w if t not in TRO_TU]:
        return False
    for i1, i2, j1, j2 in cho:
        if i2 != len(w) or i1 == i2 or any(t not in TRO_TU for t in w[i1:i2] + c[j1:j2]):
            return False
    return True


def so_cum(whisper: str, cum: str):
    """So mot doan Whisper voi ban chep cua ca cum (phan cum ngoai doan bo qua).
    Tra ve (khac, chi_tro_tu)."""
    from difflib import SequenceMatcher
    w, c = tach(whisper), tach(cum)
    khop = [m for m in SequenceMatcher(None, w, c, autojunk=False).get_matching_blocks() if m.size]
    if not khop:
        return bool(w), False
    # chi lay phan cum tuong ung voi doan: tu khop dau den khop cuoi, noi them so tu Whisper con thua o hai dau
    lo = max(0, khop[0].b - khop[0].a)
    hi = khop[-1].b + khop[-1].size + (len(w) - khop[-1].a - khop[-1].size)
    c = c[lo:hi]
    cho = giong(w, c)
    if not cho:
        return False, False
    if chi_tro_tu(w, c, cho):
        return False, True
    return True, False


def co_loi_that(tu: list) -> bool:
    """Ket qua nghe khoang trong co loi that: con tu ngoai tieng dem, tro tu, va khong phai mot hai tu lap lai."""
    tu = [t for t in tu if t not in TRO_TU + DEM_TIENG]
    return bool(tu) and not (len(tu) >= 6 and len(set(tu)) <= 2)


def so_ca_cum(doan_cum: list, cum: str) -> dict:
    """Giong hang loi Whisper cua ca cum voi ban FireRed cua cum; tra ve {id: (khac, chi_tro_tu, [chi tiet])}."""
    w, ai = [], []
    for k, d in enumerate(doan_cum):
        t = tach(d["goc"])
        w += t
        ai += [k] * len(t)
    c = tach(cum)
    theo = {k: [] for k in range(len(doan_cum))}
    for i1, i2, j1, j2 in giong(w, c):
        if i1 == i2:   # FireRed nghe them tu: gan cho doan truoc (dau cum thi doan dau)
            theo[ai[i1 - 1] if i1 > 0 else 0].append((i1, i2, j1, j2))
            continue
        # cho khac vat qua ranh gioi doan: cat theo doan, phan FireRed chia theo ti le so tu
        i, j = i1, j1
        while i < i2:
            k = ai[i]
            e = i
            while e < i2 and ai[e] == k:
                e += 1
            je = j2 if e == i2 else j1 + round((e - i1) * (j2 - j1) / (i2 - i1))
            theo[k].append((i, e, j, je))
            i, j = e, je
    kq = {}
    dau = 0
    for k, d in enumerate(doan_cum):
        n = ai.count(k)
        cho = theo[k]
        wd = w[dau:dau + n]
        rel = [(i1 - dau, i2 - dau, j1, j2) for i1, i2, j1, j2 in cho]
        tt = chi_tro_tu(wd, c, rel)
        ct = [f"{noi(w[i1:i2]) or '(trống)'} / {noi(c[j1:j2]) or '(trống)'}" for i1, i2, j1, j2 in cho]
        kq[d["id"]] = (bool(cho) and not tt, tt, ct)
        dau += n
    return kq


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
             "- Cột Khác báo KHÁC khi lời Whisper khác bản chép FireRed của cả cụm (so theo từ với tiếng Anh, theo chữ với "
             "tiếng Trung; bỏ dấu câu, đổi cả hai bên về giản thể). Cột Chỗ khác ghi `Whisper / FireRed`. "
             "Chưa quy đổi số: \"3\" và \"三\" vẫn báo KHÁC.",
             "- Cột Khác ghi \"trợ từ\" khi hai bên chỉ khác trợ từ cuối câu (啊, 呀, 吧, 呢...): không đổi nghĩa, không cần nghe lại.",
             "", "| Mã | Giây | Whisper | FireRed (đoạn riêng) | Khác | Chỗ khác |", "|---|---|---|---|---|---|"]
    for d in kq["doan"]:
        lines.append(f"| {d['id']} | {d['start']:.1f}-{d['end']:.1f} | {d['whisper'].replace('|', '/')} | "
                     f"{d['firered_doan'].replace('|', '/')} | {'KHÁC' if d['khac'] else ('trợ từ' if d.get('chi_tro_tu') else '')} | "
                     f"{'; '.join(d.get('cho_khac', [])).replace('|', '/')} |")
    if kq.get("khoang_trong"):
        lines += ["", "Lời trong khoảng trống (FireRed nghe được ở khoảng Whisper không có đoạn nào; có thể Whisper bỏ "
                  "sót, cũng có thể FireRed nghe nhầm tiếng nhạc, tiếng ồn: nghe lại):", ""]
        for k in kq["khoang_trong"]:
            lines.append(f"- **{k['start']:.1f}-{k['end']:.1f}**: {k['text']}")
    lines += ["", "Cụm (FireRed nghe liền nhau):", ""]
    for c in kq["cum"]:
        lines.append(f"- {c['start']:.1f}-{c['end']:.1f} ({', '.join(c['ids'])}): {c['text']}")
    lines += ["", "Chỗ KHÁC và lời trong khoảng trống cần người nghe lại (hoặc người biết ngôn ngữ) quyết định; không tự sửa bản chép gốc theo FireRed."]
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
        sys.exit(f"[LOI] Thieu {e.name}: chay bash setup.sh --dich")

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
    ss = {}
    for c in gom_cum(goc["doan"]):
        ss.update(so_ca_cum(c, cum_cua[c[0]["id"]]))
    doan_kq = []
    for d in goc["doan"]:
        t = chay(d["start"] - DEM, d["end"] + DEM)
        khac, tro_tu, ct = ss[d["id"]]
        doan_kq.append({"id": d["id"], "start": d["start"], "end": d["end"], "whisper": d["goc"],
                        "firered_doan": t, "khac": khac, "chi_tro_tu": tro_tu, "cho_khac": ct})
    trong = []
    for a0, a1 in goc.get("khoang_trong", []):
        t = a0
        while a1 - t > 0.5:
            b = min(a1, t + CUA_TRONG)
            txt = chay(t, b).replace("<sil>", "").strip()
            if co_loi_that(tach(txt)):
                trong.append({"start": round(t, 2), "end": round(b, 2), "text": txt})
            t = b
    kq = {"phien_ban": 2, "video": video.name, "mo_hinh": "FireRedASR2-AED int8 (sherpa-onnx)",
          "cum": cum_kq, "doan": doan_kq, "khoang_trong": trong}
    (proj / "dich").mkdir(parents=True, exist_ok=True)
    (proj / "dich" / "chep-firered.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    ghi_md(proj / "dich" / "chep-firered.md", kq)
    n = sum(d["khac"] for d in doan_kq)
    ntt = sum(d["chi_tro_tu"] for d in doan_kq)
    print(f"[OK] dich/chep-firered.json: {len(cum_kq)} cum, {len(doan_kq)} doan, {n} doan khac Whisper, "
          f"{ntt} doan chi khac tro tu, {len(trong)} khoang trong co loi (xem chep-firered.md)")
    print(f"[TIEP] Doc chu tren hinh: python3 {SCRIPTS / 'chu_tren_hinh.py'} {video} {proj}")


if __name__ == "__main__":
    main()
