#!/usr/bin/env python3
"""Doc van ban (truyen, tai lieu) thanh am thanh bang VieNeu: tach chuong, lam sach, long tieng, MP3.

Dung:
  python3 doc_van_ban.py tach NGUON.(pdf|txt|md|docx) DU_AN [--chuong 1-3] [--giong "Hai Dang"] [--toc 1.0]
                                                            [--cach-doc cach-doc.txt] [--toi-da 700]
  python3 doc_van_ban.py doc DU_AN [--chuong 1-3] [--srt]

`tach` ghi trong DU_AN:
  van-ban-sach.txt          van ban da lam sach (ca quyen), de doi chieu
  chuong-NNNN/scenes.json   kich ban long tieng cua chuong (mo dau bang tieu de chuong)
  chuong-NNNN/van-ban.txt   van ban chuong da lam sach (chua ap cach doc)
  cach-doc.md               bao cao: da bo gi, cho chua chac cach doc (ky hieu, chu Han, viet tat), de nguoi dung sua
  muc-luc.json              danh sach chuong
`doc` chay tts.py cho tung chuong (giu van tay: chay lai chi doc canh da doi), ra:
  ra/NNNN-ten-chuong.mp3    tieng doc cua chuong (mono, loudnorm -16 LUFS)
  ra/danh-sach.m3u          danh sach phat theo thu tu chuong
  ra/NNNN-ten-chuong.srt    neu co --srt (moc theo cau, chia theo so ky tu trong canh: uoc luong)

Sua cach doc: ghi `tu => cach doc` moi dong vao cach-doc.txt (khop nguyen tu, phan biet hoa thuong),
chay lai `tach` roi `doc`; chi canh co chu doi moi bi doc lai.
Chi doi cach phat am, khong doi loi van: van-ban.txt giu nguyen chu goc, cach doc chi ap vao scenes.json.
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_VOICE = "Hải Đăng"      # quyet dinh cua nguoi dung 2026-11-14: giong mac dinh cho moi job
TERMINAL = tuple(".!?…”\"»)」")
HEADING = re.compile(r"^\s*(?:Chương|CHƯƠNG|Chuong)\s+(\d+|[IVXLC]+)\b\s*[:.\-–—]?\s*(.*?)\s*$")
URL_LINE = re.compile(r"(https?://|www\.|\b[\w-]+\.(?:com|net|org|vn)\b)", re.I)
STAR_RUN = re.compile(r"\*{2,}")
MIN_BODY = 200      # tieu de chuong co noi dung it hon so ky tu nay thi coi la muc luc, khong phai chuong


def log(msg):
    print(msg, flush=True)


def trich(nguon: Path) -> str:
    ext = nguon.suffix.lower()
    if ext == ".pdf":
        r = subprocess.run(["pdftotext", str(nguon), "-"], capture_output=True, text=True, check=True)
        return r.stdout
    if ext in (".txt", ".md"):
        return nguon.read_text(encoding="utf-8", errors="replace")
    if ext == ".docx":
        with zipfile.ZipFile(nguon) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<w:tab/>", " ", xml)
        xml = re.sub(r"<[^>]+>", "", xml)
        import html
        return html.unescape(xml)
    sys.exit(f"[LOI] chua ho tro dinh dang {ext} (pdf, txt, md, docx)")


def lam_sach(text: str, bao: Counter):
    """Tra ve danh sach dong da lam sach. Dem cac thu da bo vao `bao`."""
    text = unicodedata.normalize("NFC", text).replace("\r", "")
    dong = []
    for raw in text.split("\n"):
        s = raw.replace("\f", "").replace(" ", " ").strip()
        if s and URL_LINE.search(s) and len(s) < 80:
            bao[f"dong quang cao/duong dan: {s}"] += 1
            continue
        n = len(STAR_RUN.findall(s))
        if n:
            bao["day dau sao (***) da bo"] += n
            s = STAR_RUN.sub("", s)
            s = re.sub(r"\s{2,}", " ", s).strip()
        s2 = "".join(ch for ch in s if unicodedata.category(ch) != "So")
        if s2 != s:
            for ch in set(s) - set(s2):
                bao[f"ky hieu da bo: {ch}"] += 1
            s = s2.strip()
        if re.fullmatch(r"[-—–_=~·•o O]{3,}", s):    # duong ke trang tri ("——— o O o ———")
            bao["duong ke trang tri da bo"] += 1
            continue
        dong.append(s)
    return dong


def tach_chuong(dong):
    """Tra ve [(so, tieu_de, [dong])]. Muc luc (tieu de khong co noi dung) bi bo."""
    mốc = [(i, m) for i, d in enumerate(dong) if (m := HEADING.match(d))]
    if not mốc:
        return [("0", "Toàn văn", dong)]
    out = []
    for k, (i, m) in enumerate(mốc):
        j = mốc[k + 1][0] if k + 1 < len(mốc) else len(dong)
        than = dong[i + 1:j]
        if sum(len(x) for x in than) < MIN_BODY:
            continue
        out.append((m.group(1), m.group(2).strip(" :.-"), than))
    return out


def dung_doan(than):
    """Noi cac dong bi ngat cung thanh doan van. Dong ngan ket bang dau cau hoac dong thoai moi = het doan."""
    lens = sorted(len(x) for x in than if x)
    ref = lens[int(len(lens) * 0.9)] if lens else 0
    doan, cur = [], []
    for d in than:
        if not d:
            if cur:
                doan.append(" ".join(cur)); cur = []
            continue
        if cur and d[0] in "“\"—-–" and cur[-1].endswith(TERMINAL):
            doan.append(" ".join(cur)); cur = []
        cur.append(d)
        if d.endswith(TERMINAL) and len(d) < 0.8 * ref:
            doan.append(" ".join(cur)); cur = []
    if cur:
        doan.append(" ".join(cur))
    return [re.sub(r"\s{2,}", " ", p).strip() for p in doan if p.strip()]


def cat_cau(p, toi_da):
    """Doan qua dai thi cat theo cau."""
    if len(p) <= toi_da:
        return [p]
    cau = re.split(r"(?<=[.!?…])\s+", p)
    out, cur = [], ""
    for c in cau:
        if cur and len(cur) + len(c) + 1 > toi_da:
            out.append(cur); cur = c
        else:
            cur = (cur + " " + c).strip()
    if cur:
        out.append(cur)
    return out


def gom_canh(doan, toi_da):
    """Gop cac doan thanh canh <= toi_da ky tu; doan trong canh ngan cach nhau dong trong (VieNeu nghi dai hon)."""
    mảnh = [x for p in doan for x in cat_cau(p, toi_da)]
    canh, cur = [], ""
    for p in mảnh:
        if cur and len(cur) + len(p) + 2 > toi_da:
            canh.append(cur); cur = p
        else:
            cur = (cur + "\n\n" + p) if cur else p
    if cur:
        canh.append(cur)
    return canh


def doc_cach_doc(path):
    quy = []
    if path and Path(path).exists():
        for n, d in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
            d = d.strip()
            if not d or d.startswith("#"):
                continue
            if "=>" not in d:
                sys.exit(f"[LOI] {path} dong {n}: can dang `tu => cach doc`")
            a, b = (x.strip() for x in d.split("=>", 1))
            if a:
                quy.append((re.compile(r"(?<!\w)" + re.escape(a) + r"(?!\w)"), b))
    return quy


def ap_cach_doc(s, quy):
    for rx, b in quy:
        s = rx.sub(b, s)
    return s


def cho_chua_chac(van):
    """Gom cho de nham khi doc: chu Han, viet tat in hoa, chu-so lan lon, chu Latin la."""
    c = Counter()
    for m in re.finditer(r"[一-鿿]+", van):
        c[f"chu Han: {m.group()}"] += 1
    for m in re.finditer(r"\b[A-Z]{2,}\d*\b", van):
        c[f"viet tat/in hoa: {m.group()}"] += 1
    for m in re.finditer(r"\b(?=\w*\d)(?=\w*[^\W\d_])\w+\b", van):
        c[f"chu lan so: {m.group()}"] += 1
    for m in re.finditer(r"\b[a-zA-Z]*[fjwzFJWZ][a-zA-Z]*\b", van):    # f, j, w, z it gap trong tieng Viet
        c[f"chu Latin la: {m.group()}"] += 1
    return c


def slug(s):
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:48] or "chuong"


def chon_khoang(spec, so):
    if not spec:
        return True
    ok = False
    for part in spec.split(","):
        a, _, b = part.partition("-")
        lo, hi = int(a), int(b or a)
        ok = ok or lo <= so <= hi
    return ok


def cmd_tach(a):
    nguon, du_an = Path(a.nguon), Path(a.du_an)
    if not nguon.exists():
        sys.exit(f"[LOI] khong thay {nguon}")
    du_an.mkdir(parents=True, exist_ok=True)
    bao = Counter()
    dong = lam_sach(trich(nguon), bao)
    (du_an / "van-ban-sach.txt").write_text("\n".join(dong), encoding="utf-8")
    quy = doc_cach_doc(a.cach_doc or (du_an / "cach-doc.txt"))
    chuong = tach_chuong(dong)
    log(f"Tim thay {len(chuong)} chuong.")
    muc, chua_chac = [], Counter()
    for k, (so, tieu_de, than) in enumerate(chuong, 1):
        idx = int(so) if so.isdigit() else k
        if not chon_khoang(a.chuong, idx):
            continue
        ten = f"Chương {so}. {tieu_de}." if so != "0" else "Toàn văn."
        doan = dung_doan(than)
        van = "\n\n".join(doan)
        chua_chac.update(cho_chua_chac(van))
        canh = gom_canh(doan, a.toi_da)
        scenes = [{"id": "s0000", "narration": ap_cach_doc(ten, quy)}]
        for i, c in enumerate(canh, 1):
            sc = {"id": f"s{i:04d}", "narration": ap_cach_doc(c, quy)}
            if i == 1:
                sc["pause_before"] = 0.8       # nghi sau tieu de chuong
            scenes.append(sc)
        d = du_an / f"chuong-{idx:04d}"
        d.mkdir(exist_ok=True)
        (d / "van-ban.txt").write_text(van, encoding="utf-8")
        (d / "scenes.json").write_text(json.dumps(
            {"voice": a.giong, "speed": a.toc, "scenes": scenes}, ensure_ascii=False, indent=1), encoding="utf-8")
        muc.append({"so": idx, "tieu_de": ten, "thu_muc": d.name, "ky_tu": len(van), "canh": len(scenes)})
    (du_an / "muc-luc.json").write_text(json.dumps(muc, ensure_ascii=False, indent=1), encoding="utf-8")
    # bao cao
    rows = ["# Báo cáo cách đọc", "", f"Nguồn: {nguon.name}. {len(muc)} chương được tách.", "",
            "## Đã bỏ khi làm sạch", ""]
    rows += [f"- {k} (x{v})" for k, v in bao.most_common(40)] or ["- không có"]
    rows += ["", "## Chỗ chưa chắc cách đọc", "",
             "Mỗi dòng: loại, chữ, số lần. Muốn đổi cách đọc thì thêm `chữ => cách đọc` vào `cach-doc.txt`, "
             "chạy lại `tach` rồi `doc`.", ""]
    rows += [f"- {k} (x{v})" for k, v in chua_chac.most_common(80)] or ["- không có"]
    (du_an / "cach-doc.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    tong = sum(m["ky_tu"] for m in muc)
    log(f"Da tach {len(muc)} chuong, {tong} ky tu. Bao cao: {du_an / 'cach-doc.md'}")


def cat_srt_cau(narr):
    cau = [c.strip() for c in re.split(r"(?<=[.!?…])\s+|\n\n", narr) if c.strip()]
    return cau


def ts(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def ghi_srt(timeline, out):
    cues, n = [], 0
    for sc in timeline["scenes"]:
        cau = cat_srt_cau(sc["narration"])
        tong = sum(len(c) for c in cau) or 1
        t = sc["start"]
        for c in cau:
            d = sc["duration"] * len(c) / tong
            n += 1
            cues.append(f"{n}\n{ts(t)} --> {ts(t + d)}\n{c}\n")
            t += d
    out.write_text("\n".join(cues), encoding="utf-8")


def cmd_doc(a):
    du_an = Path(a.du_an)
    mp = du_an / "muc-luc.json"
    if not mp.exists():
        sys.exit("[LOI] chua co muc-luc.json: chay `tach` truoc")
    muc = json.loads(mp.read_text(encoding="utf-8"))
    ra = du_an / "ra"
    ra.mkdir(exist_ok=True)
    ds = []
    for m in muc:
        if not chon_khoang(a.chuong, m["so"]):
            continue
        d = du_an / m["thu_muc"]
        log(f"== {m['tieu_de']}")
        r = subprocess.run([sys.executable, str(HERE / "tts.py"), str(d / "scenes.json"), str(d)])
        if r.returncode:
            sys.exit(f"[LOI] tts.py that bai o {m['thu_muc']}")
        mp3 = ra / f"{m['so']:04d}-{slug(m['tieu_de'])}.mp3"
        wav = d / "voiceover.wav"
        if not mp3.exists() or mp3.stat().st_mtime < wav.stat().st_mtime:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-ac", "1",
                            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "libmp3lame", "-b:a", "96k",
                            "-metadata", f"title={m['tieu_de']}", "-metadata", f"track={m['so']}",
                            str(mp3)], check=True)
        if a.srt:
            ghi_srt(json.loads((d / "timeline.json").read_text(encoding="utf-8")), mp3.with_suffix(".srt"))
        ds.append(mp3.name)
    allm3u = sorted(p.name for p in ra.glob("*.mp3"))
    (ra / "danh-sach.m3u").write_text("#EXTM3U\n" + "\n".join(allm3u) + "\n", encoding="utf-8")
    log(f"Xong {len(ds)} chuong, thu muc {ra}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="lenh", required=True)
    t = sp.add_parser("tach")
    t.add_argument("nguon")
    t.add_argument("du_an")
    t.add_argument("--chuong", help="vd 1-3 hoac 1,5,9-12; bo trong = tat ca")
    t.add_argument("--giong", default=DEFAULT_VOICE)
    t.add_argument("--toc", type=float, default=1.0, help="toc do doc 0.85 den 1.15")
    t.add_argument("--cach-doc", help="file `tu => cach doc`; mac dinh DU_AN/cach-doc.txt")
    t.add_argument("--toi-da", type=int, default=700, help="so ky tu toi da moi canh")
    d = sp.add_parser("doc")
    d.add_argument("du_an")
    d.add_argument("--chuong")
    d.add_argument("--srt", action="store_true")
    a = ap.parse_args()
    {"tach": cmd_tach, "doc": cmd_doc}[a.lenh](a)


if __name__ == "__main__":
    main()
