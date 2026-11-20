#!/usr/bin/env python3
"""Che do dich: ban dich theo doan, kiem ban dich, xuat phu de .srt va ghi phu de cung vao video.

Dung (theo thu tu cua quy trinh, xem references/che-do-dich.md):
  python3 phu_de_dich.py duyet-chep PROJECT           # gop chep-goc, chep-firered, chu-tren-hinh thanh mot bang
                                                      # dich/duyet-chep.md (chi cho can xem) va tao ban-dich.json neu chua co
  python3 phu_de_dich.py sua PROJECT d002 --thay "Bend=Spend"    # sua loi goc theo quyet dinh o cong duyet
  python3 phu_de_dich.py sua PROJECT d002 --goc "Spend the day at the library with me."
  python3 phu_de_dich.py them PROJECT 112.9 114.6 "Here's some ASMR typing."   # them doan Whisper bo sot
  python3 phu_de_dich.py nguoi PROJECT d001-d003=be d004-d007=me                  # gan nguoi noi theo khoang ma
  python3 phu_de_dich.py goi-y-gop PROJECT [VIDEO]    # in lenh gop cac manh cau ngan, cung nguoi noi (truoc khi dich)
  python3 phu_de_dich.py gop PROJECT d003 d004        # gop doan lien nhau vao doan dau (khong gop khac nguoi noi)
  python3 phu_de_dich.py nhap PROJECT dich.tsv        # nap ban dich: moi dong "ID<TAB>dich" (hoac "ID | dich")
  python3 phu_de_dich.py bang PROJECT [VIDEO]         # bang duyet ban dich dich/ban-dich.md (goc, dich, canh bao)
  python3 phu_de_dich.py khoi PROJECT                 # tao dich/ban-dich.json tu dich/chep-goc.json (truong "dich" de trong)
  python3 phu_de_dich.py kiem PROJECT [--cps 15]      # kiem ban dich; thoat 1 khi co loi chan
  python3 phu_de_dich.py srt PROJECT [--song-ngu]     # ghi output/phu-de-vi.srt (song ngu: them dong goc phia duoi)
  python3 phu_de_dich.py ghi PROJECT VIDEO [--ra OUT.mp4] [--song-ngu] [--font Inter]
                                                      # kiem, ghi .srt, roi ghi phu de cung vao hinh (giu nguyen tieng)

dich/ban-dich.json: {"phien_ban": 1, "ngon_ngu_goc": "en", "doan": [{"id", "start", "end", "goc", "dich",
  "nguoi_noi" (tuy chon), "bo" (tuy chon, true = khong hien phu de doan nay), "goc_whisper" (loi Whisper truoc khi
  sua), "them" (doan them tay), "gop_tu" / "gop_vao" (doan da gop)}]}
Nguoi dich (dieu phoi hoac agent) dien "dich" bang lenh nhap (hoac sua JSON); sua goc, them, gop bang cac lenh tren de
khong sua JSON tay. chep-goc.json giu nguyen (ban Whisper goc); moi sua deu nam o ban-dich.json.
Gop truoc khi dich: Whisper hay cat cau thanh manh ngan (clip Trung 27,6 giay: 19 doan, 9 doan duoi 1 giay); dich tung
manh roi moi gop thi phai dich lai. goi-y-gop goi y gop chuoi manh lien nhau (cach duoi 0,3 giay, cung nguoi noi) khi
manh duoi 1,2 giay hoac cau chua ket thuc (tieng co dau cau: khong ket bang . ? !), tong toi da 6 giay va (khi co VIDEO)
khong qua thoi gian doc het hai dong phu de (khung doc 1080 rong: khoang 3,6 giay; da gap: gop 4 manh 3,7 giay cua clip
Trung thi ban dich qua 2 dong).

Kiem (loi chan):
  - doan thieu "dich", start >= end, doan chong nhau, vuot thoi luong video
  - chu so trong loi goc (vd 10, 2024, 3.5) khong co trong ban dich: dich so phai giu nguyen hoac ghi ro (chi so chu so
    A-rap; 3.5 va 3,5 coi la mot so, 1,000 va 1.000 coi la mot nghin; so viet bang chu Han hay chu cai thi nguoi kiem dich doc lai)
  - phu de qua 2 dong sau khi ngat dong
  - chu chua o dang NFC (dau to hop roi lam lech dau khi ghi)
Doan doc nhanh hon --cps duoc keo dai thoi gian hien vao khoang trong phia sau, toi da --keo-dai giay (mac dinh 1,5),
khong cham doan sau; chi ap khi xuat, khong sua ban-dich.json.
Kiem (canh bao): toc do doc (sau khi keo dai) > --cps ky tu/giay (khong tinh khoang trang; mac dinh 15 theo doc_chu.py, chua do rieng cho
phu de tieng Viet), doan hien duoi 1 giay, doan goc co co nghi-bia hay tin-thap ma van giu.
Doan doc nhanh hoac duoi 1 giay ma sat doan sau (cach duoi 0,2 giay, khong con cho keo dai) thi canh bao kem goi y gop
vao doan sau (hoi dap nhanh kieu "不知道" 0,5 giay ngay truoc cau tiep theo).
Nguoi noi: khoi tao "nguoi_noi" rong cho moi doan. Gan cho doan nao thi phai gan cho moi doan hien (canh bao khi thieu);
khong gan doan nao thi in mot dong nhac (video mot nguoi noi thi bo qua), vi xung ho trong ban dich phu thuoc ai noi voi ai.

Video goc da co phu de cung (vd song ngu Trung Anh): xem dich/qa-phu-de.png sau lenh ghi; neu chu chong nhau thi
--vi-tri tren, hoac --che-day 0.2 (lam mo dai day khung cao 20% roi ghi phu de dich len do).
Phu de cung: file .ass cung kich thuoc video, chu trang vien den, dat giua duoi; co chu = 4,5% chieu cao khung (khung doc
3,5%), ngat dong theo chieu rong. Ma hoa lai hinh libx264 crf 18, chep nguyen luong tieng.
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path


def nap(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def ghi_json(p: Path, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def cach_doc_so(tok):
    """Cac cach hieu mot so: dau cham va dau phay co the la phan thap phan hoac ngan cach hang nghin tuy ngon ngu
    (3.5 va 3,5 la cung mot so; 1,000 va 1.000 la mot nghin). Tra ve tap dang chuan (dau cham thap phan)."""
    seps = re.findall(r"[.,]", tok)
    if not seps:
        return {tok}
    if "." in seps and "," in seps:   # dau cuoi la thap phan, dau con lai la ngan cach nghin
        cuoi = max(tok.rfind("."), tok.rfind(","))
        return {re.sub(r"[.,]", "", tok[:cuoi]) + "." + tok[cuoi + 1:]}
    if len(seps) > 1:   # lap lai cung mot dau: ngan cach nghin (1.000.000)
        return {re.sub(r"[.,]", "", tok)}
    a, b = re.split(r"[.,]", tok)
    cach = {a + "." + b}
    if len(b) == 3:   # 1,000 hay 1.000 co the la mot nghin
        cach.add(a + b)
    return cach


def so(text):
    """Cac so trong text: danh sach (so goc, tap cach hieu)."""
    return [(m, cach_doc_so(m)) for m in re.findall(r"\d+(?:[.,]\d+)*", text or "")]


def so_thieu(goc, dich):
    co = set()
    for _, c in so(dich):
        co |= c
    return sorted({m for m, c in so(goc) if not (c & co)})


def so_ky_tu(text):
    return sum(1 for c in text if not c.isspace())


def ngat_dong(text, toi_da):
    words, dong, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > toi_da:
            dong.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        dong.append(cur)
    if len(dong) == 2:   # can bang hai dong cho de doc
        allw = text.split()
        best = min(range(1, len(allw)), key=lambda i: abs(len(" ".join(allw[:i])) - len(" ".join(allw[i:]))))
        a, b = " ".join(allw[:best]), " ".join(allw[best:])
        if len(a) <= toi_da and len(b) <= toi_da:
            dong = [a, b]
    return dong


def kich_thuoc(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", str(video)],
                         capture_output=True, text=True, check=True)
    d = json.loads(out.stdout)
    st = d["streams"][0]
    return st["width"], st["height"], float(d["format"]["duration"])


def bo_cuc(w, h):
    co = round(h * (0.035 if h > w else 0.045))
    toi_da = max(16, int(w * 0.88 / (co * 0.52)))   # 0,52 em: be rong trung binh chu Latin co dau o phong sans
    return co, toi_da


def doan_hien(proj, cps, keo, dur=None):
    """Doan se hien, theo thu tu; doan doc nhanh qua cps duoc keo dai vao khoang trong phia sau (toi da keo giay,
    cach doan sau 0,1 giay, khong qua thoi luong video). Khong ghi lai ban-dich.json."""
    bd = nap(proj / "dich" / "ban-dich.json")
    doan = [dict(d) for d in bd["doan"] if not d.get("bo")]
    for i, d in enumerate(doan):
        dich = (d.get("dich") or "").strip()
        if not dich or keo <= 0:
            continue
        can = so_ky_tu(dich) / cps - (d["end"] - d["start"])
        if can <= 0:
            continue
        tran = doan[i + 1]["start"] - 0.1 if i + 1 < len(doan) else (dur if dur else d["end"] + keo)
        moi = min(d["end"] + min(can, keo), tran)
        if moi > d["end"]:
            d["keo_tu"] = d["end"]
            d["end"] = round(moi, 2)
    return bd, doan


def kiem(proj, cps, toi_da=None, dur=None, keo=1.5):
    bd, doan = doan_hien(proj, cps, keo, dur)
    loi, canh = [], []
    toi_da = toi_da or 42
    prev_end = 0.0
    for k, d in enumerate(doan):
        i, dich, goc = d["id"], (d.get("dich") or "").strip(), d.get("goc", "")
        if not dich:
            loi.append(f"{i}: thieu ban dich")
            continue
        if unicodedata.normalize("NFC", dich) != dich:
            loi.append(f"{i}: chu chua o dang NFC")
        if d["start"] >= d["end"]:
            loi.append(f"{i}: start >= end")
        if d["start"] < prev_end - 0.01:
            loi.append(f"{i}: chong voi doan truoc ({d['start']} < {prev_end})")
        prev_end = max(prev_end, d["end"])
        if dur and d["end"] > dur + 0.05:
            loi.append(f"{i}: vuot thoi luong video ({d['end']} > {dur:.2f})")
        thieu = so_thieu(goc, dich)
        if thieu:
            loi.append(f"{i}: so {sorted(thieu)} trong loi goc khong co trong ban dich")
        if len(ngat_dong(dich, toi_da)) > 2:
            loi.append(f"{i}: qua 2 dong (toi da {toi_da} ky tu moi dong), rut gon hoac tach doan")
        t = d["end"] - d["start"]
        if t > 0 and so_ky_tu(dich) / t > cps + 0.05:
            canh.append(f"{i}: doc nhanh {so_ky_tu(dich) / t:.1f} ky tu/giay > {cps}"
                        + (f" (da keo dai tu {d['keo_tu']} den {d['end']}, van thieu)" if "keo_tu" in d else "")
                        + ": rut gon ban dich")
        if t < 1.0:
            canh.append(f"{i}: hien {t:.2f} giay < 1 giay")
        sau = doan[k + 1] if k + 1 < len(doan) else None
        if sau and sau["start"] - d["end"] < 0.2 and (t < 1.0 or (t > 0 and so_ky_tu(dich) / t > cps + 0.05)):
            if cung_nguoi(d, sau):
                canh.append(f"{i}: sat {sau['id']}, khong con cho keo dai: goi y gop: phu_de_dich.py gop PROJECT {i} {sau['id']}")
            else:
                canh.append(f"{i}: sat {sau['id']} (khac nguoi noi, khong gop): rut gon ban dich")
        if set(d.get("co", [])) & {"nghi-bia", "tin-thap"}:
            canh.append(f"{i}: doan goc co co {d['co']}, da duoc nguoi nghe lai chua?")
    co_nn = [d for d in doan if (d.get("nguoi_noi") or "").strip()]
    if co_nn and len(co_nn) < len(doan):
        thieu_nn = [d["id"] for d in doan if not (d.get("nguoi_noi") or "").strip()]
        canh.append(f"thieu nguoi_noi o {', '.join(thieu_nn)} (cac doan khac da gan)")
    bo = [d["id"] for d in bd["doan"] if d.get("bo")]
    return loi, canh, bo


def cung_nguoi(a, b):
    """Hai doan co the cung nguoi noi: cung ma, hoac mot ben chua gan (chua biet thi khong chan)."""
    x, y = (a.get("nguoi_noi") or "").strip(), (b.get("nguoi_noi") or "").strip()
    return not x or not y or x == y


def noi_loi(a, b):
    """Noi hai loi: chu Han (va dau cau Han) viet lien, con lai cach mot khoang trang."""
    a, b = (a or "").strip(), (b or "").strip()
    if not a or not b:
        return a or b
    han = re.compile(r"[\u3000-\u303f\u3400-\u9fff\uff00-\uffef]")
    return a + b if han.match(a[-1]) and han.match(b[0]) else a + " " + b


def luu(proj, bd):
    ghi_json(proj / "dich" / "ban-dich.json", bd)


def nap_bd(proj):
    p = proj / "dich" / "ban-dich.json"
    if not p.exists():
        sys.exit(f"[LOI] Chua co {p}: chay phu_de_dich.py duyet-chep (hoac khoi) truoc.")
    return nap(p)


def tim(bd, i):
    for d in bd["doan"]:
        if d["id"] == i:
            return d
    sys.exit(f"[LOI] Khong co doan {i}")


def thay_tu(goc, cu, moi):
    """Thay cu bang moi trong goc mot lan: tieng co dau cach thi theo ca tu, khong phan biet hoa thuong, giu chu hoa dau
    tu; chu Han thi thay chuoi. Tra ve goc moi hoac None khi khong tim thay."""
    if re.search(r"[\u3400-\u9fff]", cu):
        return goc.replace(cu, moi, 1) if cu in goc else None
    m = re.search(r"(?<![\w'])" + re.escape(cu) + r"(?![\w'])", goc, re.I)
    if not m:
        return None
    if m.group(0)[:1].isupper() and moi[:1].islower():
        moi = moi[:1].upper() + moi[1:]
    return goc[:m.start()] + moi + goc[m.end():]


def lenh_sua(proj, a):
    bd = nap_bd(proj)
    d = tim(bd, a.id)
    goc = d["goc"]
    if a.goc is not None:
        goc = a.goc.strip()
    for t in a.thay or []:
        if "=" not in t:
            sys.exit(f"[LOI] --thay can dang CU=MOI: {t}")
        cu, moi = t.split("=", 1)
        g = thay_tu(goc, cu.strip(), moi.strip())
        if g is None:
            sys.exit(f"[LOI] {a.id}: khong thay \"{cu.strip()}\" trong loi goc: {goc}")
        goc = g
    goc = re.sub(r"\s{2,}", " ", unicodedata.normalize("NFC", goc)).strip()
    if goc == d["goc"]:
        print(f"[OK] {a.id}: khong doi")
        return
    d.setdefault("goc_whisper", d["goc"])
    d["goc"] = goc
    luu(proj, bd)
    print(f"[OK] {a.id}: {d['goc_whisper']}  ->  {goc}")
    if (d.get("dich") or "").strip():
        print(f"[CANH BAO] {a.id} da co ban dich, xem lai cho khop loi goc moi: {d['dich']}")


def lenh_them(proj, a):
    bd = nap_bd(proj)
    if a.start >= a.end:
        sys.exit("[LOI] start phai nho hon end")
    for d in bd["doan"]:
        if not d.get("bo") and d["start"] < a.end - 0.01 and a.start < d["end"] - 0.01:
            sys.exit(f"[LOI] {a.start}-{a.end} chong voi {d['id']} ({d['start']}-{d['end']}); sua moc hoac dung lenh sua")
    so_id = [int(m.group(1)) for d in bd["doan"] for m in [re.fullmatch(r"d(\d+)", d["id"])] if m]
    i = f"d{(max(so_id) if so_id else 0) + 1:03d}"
    moi = {"id": i, "start": round(a.start, 2), "end": round(a.end, 2), "goc": unicodedata.normalize("NFC", a.goc.strip()),
           "dich": "", "nguoi_noi": a.nguoi_noi or "", "co": [], "them": True}
    bd["doan"].append(moi)
    bd["doan"].sort(key=lambda d: d["start"])
    luu(proj, bd)
    print(f"[OK] them {i} ({a.start}-{a.end}): {moi['goc']}")


def khoang_ma(bd, k):
    """"d001-d003" hoac "d004": danh sach ma theo thu tu trong ban-dich.json."""
    ids = [d["id"] for d in bd["doan"]]
    a, _, b = k.partition("-")
    b = b or a
    if a not in ids or b not in ids or ids.index(a) > ids.index(b):
        sys.exit(f"[LOI] Khoang ma khong hop le: {k}")
    return ids[ids.index(a):ids.index(b) + 1]


def lenh_nguoi(proj, a):
    bd = nap_bd(proj)
    n = 0
    for gan in a.gan:
        if "=" not in gan:
            sys.exit(f"[LOI] Can dang d001-d003=ma_nguoi_noi: {gan}")
        k, ten = gan.split("=", 1)
        for i in khoang_ma(bd, k.strip()):
            tim(bd, i)["nguoi_noi"] = ten.strip()
            n += 1
    luu(proj, bd)
    print(f"[OK] gan nguoi_noi cho {n} doan")


def gop_doan(bd, ids, khac_nguoi=False):
    """Gop cac doan lien nhau (theo thu tu, khong tinh doan bo) vao doan dau. Tra ve doan dau."""
    hien = [d for d in bd["doan"] if not d.get("bo")]
    vt = [next((k for k, d in enumerate(hien) if d["id"] == i), None) for i in ids]
    if None in vt:
        raise ValueError(f"doan khong ton tai hoac da bo: {ids}")
    if vt != list(range(vt[0], vt[0] + len(vt))):
        raise ValueError(f"doan phai lien nhau theo thu tu: {ids}")
    ds = [hien[k] for k in vt]
    if not khac_nguoi and any(not cung_nguoi(ds[0], d) for d in ds[1:]):
        raise ValueError("khac nguoi noi; gop van muon thi them --khac-nguoi-noi (phu de se lan loi hai nguoi)")
    dau = ds[0]
    for d in ds[1:]:
        dau["goc"] = noi_loi(dau["goc"], d["goc"])
        dau["dich"] = noi_loi(dau.get("dich"), d.get("dich"))
        if "goc_whisper" in d or "goc_whisper" in dau:
            dau["goc_whisper"] = noi_loi(dau.get("goc_whisper", ""), d.get("goc_whisper", d["goc"]))
        dau["co"] = sorted(set(dau.get("co", [])) | set(d.get("co", [])))
        dau["end"] = d["end"]
        d["bo"] = True
        d["gop_vao"] = dau["id"]
    dau["gop_tu"] = dau.get("gop_tu", [dau["id"]]) + [i for d in ds[1:] for i in d.get("gop_tu", [d["id"]])]
    return dau


def lenh_gop(proj, a):
    bd = nap_bd(proj)
    if len(a.ids) < 2:
        sys.exit("[LOI] Can it nhat hai ma doan")
    try:
        dau = gop_doan(bd, a.ids, a.khac_nguoi_noi)
    except ValueError as e:
        sys.exit(f"[LOI] {e}")
    luu(proj, bd)
    print(f"[OK] gop {', '.join(a.ids)} vao {dau['id']} ({dau['start']}-{dau['end']}): {dau['goc']}")


KET_CAU = re.compile(r"[.?!。？！…]$")


def goi_y_gop(doan, ngan=1.2, ke=0.3, toi_da=6.0):
    """Chuoi doan nen gop truoc khi dich: lien nhau (cach duoi ke giay), cung nguoi noi, tong toi da toi_da giay; doan
    trong chuoi ngan hon ngan giay, hoac (loi co dau cau) chua ket thuc cau."""
    hien = [d for d in doan if not d.get("bo")]
    co_dau = any(re.search(r"[.?!,。？！，]", d.get("goc", "")) for d in hien)
    out, cur = [], []

    def can_noi(a):
        return (a["end"] - a["start"] < ngan) or (co_dau and not KET_CAU.search(a.get("goc", "").strip()))

    for d in hien:
        if (cur and d["start"] - cur[-1]["end"] < ke and cung_nguoi(cur[-1], d) and d["end"] - cur[0]["start"] <= toi_da
                and (can_noi(cur[-1]) or d["end"] - d["start"] < ngan)):
            cur.append(d)
            continue
        if len(cur) > 1:
            out.append([x["id"] for x in cur])
        cur = [d]
    if len(cur) > 1:
        out.append([x["id"] for x in cur])
    return out


def lenh_goi_y_gop(proj, a):
    bd = nap_bd(proj)
    # tong thoi luong toi da: 6 giay, va khong qua thoi gian doc het hai dong phu de o --cps (khung doc 1080 rong:
    # 27 ky tu moi dong, 15 ky tu/giay -> 3,6 giay; gop dai hon thi ban dich de qua 2 dong)
    toi_da = 6.0
    if a.video:
        w, h, _ = kich_thuoc(a.video)
        toi_da = min(toi_da, 2 * bo_cuc(w, h)[1] / a.cps)
    gy = goi_y_gop(bd["doan"], toi_da=toi_da)
    if not gy:
        print("[OK] Khong co manh cau nao nen gop")
        return
    if not any((d.get("nguoi_noi") or "").strip() for d in bd["doan"]):
        print("[CANH BAO] Chua gan nguoi_noi: video nhieu nguoi noi thi gan truoc (lenh nguoi), neu khong se gop lan loi hai nguoi")
    by = {d["id"]: d for d in bd["doan"]}
    for g in gy:
        loi = noi_loi("", "")
        for i in g:
            loi = noi_loi(loi, by[i]["goc"])
        print(f"python3 {Path(__file__).resolve()} gop {proj} {' '.join(g)}   # {by[g[0]]['start']}-{by[g[-1]]['end']}: {loi}")
    print(f"[OK] {len(gy)} goi y gop. Doc lai truoc khi chay: chi gop khi la cung mot cau hoac mot y")


def lenh_nhap(proj, a):
    bd = nap_bd(proj)
    by = {d["id"]: d for d in bd["doan"]}
    n = 0
    for so_dong, dong in enumerate(Path(a.tep).read_text(encoding="utf-8").splitlines(), 1):
        if not dong.strip() or dong.lstrip().startswith("#"):
            continue
        cot = [c.strip() for c in (dong.split("\t") if "\t" in dong else dong.split("|"))]
        cot = [c for c in cot if c != ""] if "|" in dong and "\t" not in dong else cot
        if len(cot) < 2:
            sys.exit(f"[LOI] dong {so_dong}: can \"ID<TAB>dich\" hoac \"ID<TAB>nguoi_noi<TAB>dich\": {dong}")
        i = cot[0]
        if i not in by:
            sys.exit(f"[LOI] dong {so_dong}: khong co doan {i}")
        if by[i].get("bo"):
            sys.exit(f"[LOI] dong {so_dong}: {i} da gop vao {by[i].get('gop_vao')} hoac bi bo, dich vao doan do")
        if len(cot) >= 3:
            by[i]["nguoi_noi"] = cot[1]
        by[i]["dich"] = unicodedata.normalize("NFC", cot[-1])
        n += 1
    luu(proj, bd)
    thieu = [d["id"] for d in bd["doan"] if not d.get("bo") and not (d.get("dich") or "").strip()]
    print(f"[OK] nap {n} dong dich" + (f"; con thieu: {', '.join(thieu)}" if thieu else "; da du"))


def o(x):
    return (x or "").replace("|", "/").replace("\n", " ")


def lenh_bang(proj, a, canh_bao):
    bd = nap_bd(proj)
    theo = {}
    for c in canh_bao:
        m = re.match(r"(d\d+\w*): (.*)", c)
        if m:
            theo.setdefault(m.group(1), []).append(m.group(2))
    lines = [f"# Bản dịch: duyệt gốc và dịch ({bd.get('ngon_ngu_goc', '')} sang tiếng Việt)", "",
             "Cột Ghi chú: lời gốc đã sửa ở cổng duyệt bản chép (kèm lời Whisper cũ), đoạn thêm tay, đoạn đã gộp, cảnh báo "
             "của lệnh kiem (đọc nhanh, hiện ngắn).", "",
             "| Mã | Giây | Người nói | Gốc | Dịch | Ghi chú |", "|---|---|---|---|---|---|"]
    for d in bd["doan"]:
        if d.get("bo"):
            continue
        gc = []
        if "goc_whisper" in d:
            gc.append(f"đã sửa gốc (Whisper: {o(d['goc_whisper'])})")
        if d.get("them"):
            gc.append("đoạn thêm tay")
        if len(d.get("gop_tu", [])) > 1:
            gc.append("gộp " + ", ".join(d["gop_tu"]))
        gc += theo.get(d["id"], [])
        lines.append(f"| {d['id']} | {d['start']:.1f}-{d['end']:.1f} | {o(d.get('nguoi_noi'))} | {o(d['goc'])} | "
                     f"{o(d.get('dich'))} | {o('; '.join(gc))} |")
    p = proj / "dich" / "ban-dich.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] {p}: gửi bảng này ở cổng duyệt bản dịch, kèm kết quả lượt kiểm dịch (dich/kiem-dich.md)")


def lenh_duyet_chep(proj):
    d0 = proj / "dich"
    goc = nap(d0 / "chep-goc.json")
    fr = nap(d0 / "chep-firered.json") if (d0 / "chep-firered.json").exists() else None
    oc = nap(d0 / "chu-tren-hinh.json") if (d0 / "chu-tren-hinh.json").exists() else None
    frd = {d["id"]: d for d in fr["doan"]} if fr else {}
    ocd = {d["id"]: d for d in oc.get("doan", [])} if oc else {}
    nn = goc["ngon_ngu"]
    lines = [f"# Duyệt bản chép gốc: {goc.get('video', '')}", "",
             f"- Ngôn ngữ: `{nn.get('chon')}`" + (" (**chưa chắc chắn, hỏi người dùng**)" if nn.get("can_hoi") else "")
             + f"; {len(goc['doan'])} đoạn Whisper `{goc.get('ban', '')}`."
             + (" Kiểm chéo FireRedASR2: có." if fr else " Kiểm chéo FireRedASR2: không chạy.")
             + (" Chữ trên hình: " + ("có chữ." if oc.get("co_chu") else "không có chữ.") if oc else " Chữ trên hình: không chạy."),
             "- Bảng chỉ có đoạn cần xem. Mỗi chỗ ghi các bên nghe khác nhau; người dùng chọn bên nào (hoặc nghe lại), "
             "điều phối áp bằng lệnh ở cột cuối. Không tự chọn.", ""]
    rows = []
    for d in goc["doan"]:
        ly, lenh = [], {}
        if d.get("co"):
            ly.append("cờ " + ", ".join(d["co"]))
        f = frd.get(d["id"])
        pa = []
        if f and f.get("khac"):
            pa += [("FireRed",) + tuple(c.partition(" / ")[::2]) for c in f.get("cho_khac", [])]
        pa += [("chữ trên hình", w, x) for w, x in (ocd.get(d["id"]) or {}).get("cho_khac", [])]
        for ben, w, x in pa:
            ly.append(f"{ben}: {w} / {x}")
            if w != "(trống)" and x != "(trống)":
                lenh.setdefault(f"--thay \"{w}={x}\"", []).append(ben)
        if ly:
            cmd = "; ".join(f"{', '.join(b)}: `sua {d['id']} {k}`" for k, b in lenh.items()) or f"`sua {d['id']} --goc \"...\"`"
            rows.append(f"| {d['id']} | {d['start']:.1f}-{d['end']:.1f} | {o(d['goc'])} | {o('; '.join(ly))} | {o(cmd)} |")
    if rows:
        lines += ["## Chỗ cần chọn", "", "Cột Khác ghi `Whisper / bên kia`. Lệnh gợi ý lấy theo bên kia; chọn giữ Whisper "
                  "thì bỏ qua. Lệnh đầy đủ: `python3 SKILL/scripts/phu_de_dich.py sua PROJECT ...`.", "",
                  "| Mã | Giây | Whisper | Khác | Lệnh áp (nếu chọn bên kia) |", "|---|---|---|---|---|"] + rows + [""]
    else:
        lines += ["Không có chỗ nào các bên nghe khác nhau, không có cờ.", ""]
    them = (fr or {}).get("khoang_trong", [])
    if them:
        lines += ["## Lời trong khoảng trống (FireRed nghe được, Whisper không có đoạn)", "",
                  "Nghe lại; có lời thật thì thêm đoạn (sửa mốc cho sát câu nếu cần):", ""]
        for k in them:
            lines.append(f"- {k['start']:.1f}-{k['end']:.1f}: {k['text']}  `them {k['start']} {k['end']} \"...\"`")
        lines.append("")
    kt = goc.get("khoang_trong", [])
    if kt:
        lines += ["## Khoảng không có lời từ 2 giây", "", "VAD có thể bỏ câu nói nhỏ trên nền nhạc: "
                  + ", ".join(f"{a:.1f}-{b:.1f}" for a, b in kt) + ".", ""]
    chu = (oc or {}).get("chu", [])
    if nn.get("chon") not in ("zh", "yue", "ja", "ko"):   # bo phu de dich san co bang chu Han khi loi goc khong phai chu Han
        chu = [c for c in chu if not re.search(r"[\u3400-\u9fff]", c["text"])]
    if chu:
        lines += [f"## Chữ khác trên hình ({len(chu)} dòng, đọc lướt để sửa tên riêng, món ăn)", "",
                  "; ".join(c["text"] for c in chu[:40]) + (" ..." if len(chu) > 40 else ""), ""]
    lines += ["## Hỏi người dùng", "",
              "- Video có mấy người nói, ai nói câu nào, ai nói với ai (gán bằng lệnh `nguoi`, ví dụ `nguoi PROJECT "
              "d001-d003=be d004-d007=me`). Một người nói thì bỏ qua.",
              "- Chọn bên nào ở từng chỗ trên; tên riêng, từ hiếm có đúng không.", ""]
    (d0 / "duyet-chep.md").write_text("\n".join(lines), encoding="utf-8")
    if not (d0 / "ban-dich.json").exists():
        khoi(proj)
    print(f"[OK] {d0 / 'duyet-chep.md'}: {len(rows)} doan can chon, {len(them)} khoang trong co loi, "
          f"{len(chu)} dong chu khac. Gui bang nay o cong duyet ban chep.")


def khoi(proj):
    cg = nap(proj / "dich" / "chep-goc.json")
    p = proj / "dich" / "ban-dich.json"
    if p.exists():
        sys.exit(f"[LOI] {p} da co; xoa tay neu muon tao lai (tranh mat ban dich)")
    ghi_json(p, {"phien_ban": 1, "ngon_ngu_goc": cg["ngon_ngu"]["chon"],
                 "doan": [{"id": d["id"], "start": d["start"], "end": d["end"], "goc": d["goc"], "dich": "",
                           "nguoi_noi": "", "co": d["co"]} for d in cg["doan"]]})
    print(f"[OK] {p}: {len(cg['doan'])} doan")


def srt_t(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def ass_t(x):
    cs = int(round(x * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ghi_srt(doan, proj, song_ngu, toi_da):
    rows = []
    for d in doan:
        txt = "\n".join(ngat_dong(d["dich"].strip(), toi_da))
        if song_ngu:
            txt += "\n" + d["goc"].strip()
        rows.append(f"{len(rows) + 1}\n{srt_t(d['start'])} --> {srt_t(d['end'])}\n{txt}\n")
    out = proj / "output"
    out.mkdir(exist_ok=True)
    p = out / "phu-de-vi.srt"
    p.write_text("\n".join(rows), encoding="utf-8")
    return p, len(rows)


def an_toan_ass(text):
    """libass doc {..} la lenh dinh dang va \\N la xuong dong: bo di de chu nguoi dich khong bi mat hay xuong dong thua."""
    return text.replace("{", "(").replace("}", ")").replace("\\", "/")


def ghi_ass(doan, proj, w, h, font, song_ngu, tren=False):
    co, toi_da = bo_cuc(w, h)
    co_goc = round(co * 0.7)
    toi_da_goc = max(16, int(w * 0.88 / (co_goc * 0.52)))
    canh = 8 if tren else 2
    le = round(h * (0.12 if h > w else 0.06))
    vien = max(2, round(co * 0.08))
    hdr = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
           "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,"
           "Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,"
           "MarginV,Encoding\n"
           f"Style: Dich,{font},{co},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{vien},1,{canh},"
           f"{round(w * 0.06)},{round(w * 0.06)},{le},1\n"
           f"Style: Goc,{font},{co_goc},&H00D0D0D0,&H00D0D0D0,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,"
           f"{max(1, vien - 1)},1,{canh},{round(w * 0.06)},{round(w * 0.06)},{le},1\n\n"
           "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    ev = []
    xuong = "\\N"
    for d in doan:
        dong = xuong.join(ngat_dong(an_toan_ass(d["dich"].strip()), toi_da))
        t0, t1 = ass_t(d["start"]), ass_t(d["end"])
        if song_ngu:   # dong goc nho nam sat mep khung, ban dich day vao phia trong; goc ngat dong nhu ban dich
            dong_goc = ngat_dong(an_toan_ass(d["goc"].strip()), toi_da_goc)
            day = le + round(len(dong_goc) * co_goc * 1.15 + co * 0.1)
            ev.append(f"Dialogue: 0,{t0},{t1},Dich,,0,0,{day},,{dong}")
            ev.append(f"Dialogue: 0,{t0},{t1},Goc,,0,0,{le},,{xuong.join(dong_goc)}")
        else:
            ev.append(f"Dialogue: 0,{t0},{t1},Dich,,0,0,0,,{dong}")
    p = proj / "dich" / "phu-de-vi.ass"
    p.write_text(hdr + "\n".join(ev) + "\n", encoding="utf-8")
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    lenh_phu = ["duyet-chep", "sua", "them", "nguoi", "goi-y-gop", "gop", "nhap", "bang"]
    if len(sys.argv) > 1 and sys.argv[1] in lenh_phu:
        return phu(sys.argv[1], sys.argv[2:])
    ap.add_argument("lenh", choices=["khoi", "kiem", "srt", "ghi"] + lenh_phu)
    ap.add_argument("project")
    ap.add_argument("video", nargs="?")
    ap.add_argument("--ra")
    ap.add_argument("--cps", type=float, default=15.0)
    ap.add_argument("--keo-dai", type=float, default=1.5,
                    help="giay toi da keo dai doan doc nhanh vao khoang trong phia sau (0 = tat)")
    ap.add_argument("--song-ngu", action="store_true")
    ap.add_argument("--font", default="Inter")
    ap.add_argument("--fontsdir", default="/usr/share/fonts/opentype/inter")
    ap.add_argument("--vi-tri", choices=["duoi", "tren"], default="duoi",
                    help="video goc da co phu de cung o duoi thi dat phu de dich len tren, hoac dung --che-day")
    ap.add_argument("--che-day", type=float, default=0.0,
                    help="ti le chieu cao dai day khung lam mo (vd 0.2) de che phu de cung san co cua video goc")
    a = ap.parse_args()
    proj = Path(a.project)

    if a.lenh == "khoi":
        khoi(proj)
        return

    w = h = dur = None
    if a.video:
        w, h, dur = kich_thuoc(a.video)
    toi_da = bo_cuc(w, h)[1] if w else 42
    loi, canh, bo = kiem(proj, a.cps, toi_da, dur, a.keo_dai)
    _, doan = doan_hien(proj, a.cps, a.keo_dai, dur)
    keo = [d["id"] for d in doan if "keo_tu" in d]
    if keo:
        print(f"Keo dai thoi gian hien (doc nhanh): {', '.join(keo)}")
    for c in canh:
        print(f"[CANH BAO] {c}")
    for l in loi:
        print(f"[LOI] {l}")
    if bo:
        print(f"Bo khong hien: {', '.join(bo)}")
    if not any((d.get("nguoi_noi") or "").strip() for d in doan):
        print("Chua gan nguoi_noi: video nhieu nguoi noi thi gan truoc khi dich (xung ho theo ai noi voi ai)")
    if loi:
        sys.exit(1)
    if a.lenh == "kiem":
        print(f"[OK] ban dich dat ({len(canh)} canh bao)")
        return

    srt, n = ghi_srt(doan, proj, a.song_ngu, toi_da)
    print(f"[OK] {srt}: {n} dong phu de")
    if a.lenh == "srt":
        return
    if not a.video:
        sys.exit("[LOI] lenh ghi can VIDEO")
    ass = ghi_ass(doan, proj, w, h, a.font, a.song_ngu, a.vi_tri == "tren")
    ra = Path(a.ra) if a.ra else proj / "output" / (Path(a.video).stem + "-phu-de-vi.mp4")
    fd = f":fontsdir={a.fontsdir}" if a.fontsdir and Path(a.fontsdir).is_dir() else ""
    if not 0 <= a.che_day < 0.5:
        sys.exit("[LOI] --che-day trong khoang 0 den 0.5")
    if a.che_day:
        r = a.che_day
        loc = (f"[0:v:0]split[g][d];[d]crop=iw:ih*{r}:0:ih*(1-{r}),boxblur=20:3[m];"
               f"[g][m]overlay=0:H*(1-{r})[c];[c]ass={ass}{fd}[v]")
    else:
        loc = f"[0:v:0]ass={ass}{fd}[v]"
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-map", "0:a?",
                           "-filter_complex", loc, "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                           "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(ra)])
    w2, h2, dur2 = kich_thuoc(ra)
    if (w2, h2) != (w, h) or abs(dur2 - dur) > 0.2:
        sys.exit(f"[LOI] video ra lech: {w2}x{h2} {dur2:.2f}s so voi {w}x{h} {dur:.2f}s")
    print(f"[OK] {ra} ({w2}x{h2}, {dur2:.1f} giay)")
    # Bang khung kiem: giua 6 dong phu de rai deu, de nguoi duyet thay chu co de len chu san co cua video khong
    chon = [doan[round(i * (len(doan) - 1) / 5)] for i in range(min(6, len(doan)))]
    anh = proj / "dich" / "qa-phu-de.png"
    vao = []
    for d in chon:
        vao += ["-ss", f"{(d['start'] + d['end']) / 2:.2f}", "-i", str(ra)]
    n = len(chon)
    cot = 3 if n > 3 else n
    loc2 = "".join(f"[{i}:v]scale=640:-2,setpts=PTS-STARTPTS[k{i}];" for i in range(n))
    vt = [("+".join(["w0"] * (i % cot)) or "0") + "_" + ("+".join(["h0"] * (i // cot)) or "0") for i in range(n)]
    loc2 += "".join(f"[k{i}]" for i in range(n)) + f"xstack=inputs={n}:layout=" + "|".join(vt) + "[o]"
    if n == 1:
        loc2 = "[0:v]scale=640:-2[o]"
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", *vao, "-filter_complex", loc2, "-map", "[o]",
                           "-frames:v", "1", str(anh)])
    print(f"[OK] {anh}: khung kiem phu de (xem chu dich co de len phu de san co, logo, mat nguoi khong)")


def phu(lenh, argv):
    """Cac lenh sua ban-dich.json va tao bang duyet (moi lenh co tham so rieng)."""
    ap = argparse.ArgumentParser(prog=f"phu_de_dich.py {lenh}")
    ap.add_argument("project")
    if lenh == "sua":
        ap.add_argument("id")
        ap.add_argument("--goc", help="thay ca loi goc")
        ap.add_argument("--thay", action="append", help="CU=MOI, thay mot tu hoac cum (lap lai duoc)")
    elif lenh == "them":
        ap.add_argument("start", type=float)
        ap.add_argument("end", type=float)
        ap.add_argument("goc")
        ap.add_argument("--nguoi-noi", default="")
    elif lenh == "nguoi":
        ap.add_argument("gan", nargs="+", help="d001-d003=ma_nguoi_noi")
    elif lenh == "gop":
        ap.add_argument("ids", nargs="+")
        ap.add_argument("--khac-nguoi-noi", action="store_true")
    elif lenh == "nhap":
        ap.add_argument("tep")
    elif lenh == "goi-y-gop":
        ap.add_argument("video", nargs="?", help="co video thi gioi han thoi luong gop theo do rong khung")
        ap.add_argument("--cps", type=float, default=15.0)
    elif lenh == "bang":
        ap.add_argument("video", nargs="?")
        ap.add_argument("--cps", type=float, default=15.0)
    a = ap.parse_args(argv)
    proj = Path(a.project)
    if lenh == "duyet-chep":
        lenh_duyet_chep(proj)
    elif lenh == "sua":
        if a.goc is None and not a.thay:
            sys.exit("[LOI] Can --goc hoac --thay")
        lenh_sua(proj, a)
    elif lenh == "them":
        lenh_them(proj, a)
    elif lenh == "nguoi":
        lenh_nguoi(proj, a)
    elif lenh == "goi-y-gop":
        lenh_goi_y_gop(proj, a)
    elif lenh == "gop":
        lenh_gop(proj, a)
    elif lenh == "nhap":
        lenh_nhap(proj, a)
    elif lenh == "bang":
        w = h = dur = None
        if a.video:
            w, h, dur = kich_thuoc(a.video)
        _, canh, _ = kiem(proj, a.cps, bo_cuc(w, h)[1] if w else 42, dur)
        lenh_bang(proj, a, canh)


if __name__ == "__main__":
    main()
