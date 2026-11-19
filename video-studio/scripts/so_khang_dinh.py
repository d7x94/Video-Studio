#!/usr/bin/env python3
"""So khang dinh: moi cau trong loi doc phai thuoc mot loai va co can cu; chan cau chua xac nhan (video co san).

Dung:
  python3 so_khang_dinh.py khoi PROJECT     # tao PROJECT/khang-dinh.json mau tu scenes.json (moi cau mot muc, loai "chua-phan-loai")
  python3 so_khang_dinh.py dong-bo PROJECT  # sau khi sua scenes.json: giu muc cu cua cau khong doi chu, cau moi/doi chu ve "chua-phan-loai"
  python3 so_khang_dinh.py kiem PROJECT     # kiem so khang dinh; thoat ma 1 neu con loi chan
  python3 so_khang_dinh.py ghi PROJECT      # kiem roi ghi PROJECT/kiem-chung.md (bang) tu so khang dinh

khang-dinh.json:
{"khang_dinh": [
  {"canh": "s03", "cau": "Mat sau dan nhan phu tieng Viet.", "loai": "nhan", "moc_giay": 17.2,
   "nhan_doc": "Nha nhap khau: ...", "ghi_chu": ""},
  {"canh": "s05", "cau": "Thung khong bi mop.", "loai": "quan-sat", "moc_giay": 1.4,
   "xac_nhan": "co", "ghi_chu": "khung 1.4s do phan giai goc, 4 mat thung"},
  {"canh": "s16", "cau": "OBgE la thuong hieu my pham nam cua Han Quoc.", "loai": "nguon-ngoai",
   "nguon": {"don_vi": "...", "url": "https://...", "ngay": "dd/mm/yyyy"}, "ket_qua": "dung"},
  {"canh": "s01", "cau": "Kien hang nho.", "loai": "khong-khang-dinh"}]}

Loai:
  nhan              chu doc duoc tren nhan, bao bi, tem. Can moc_giay (khung hinh co chu) va nhan_doc (chu da doc).
  quan-sat          dieu nhin thay (thung khong mop, vo khong tray, bo phan thao roi duoc). Can moc_giay va xac_nhan:
                    "co" (khung do phan giai goc cho thay ro), "khong" (khong thay ro: phai xoa cau), "chua" (cho nguoi
                    quay xac nhan). Cau "chua" la loi chan; "khong" la loi chan; cau nhay cam (xem NHAY_CAM) can xac_nhan "co".
  nguon-ngoai       thong tin tu ben ngoai video. Can nguon.don_vi, nguon.url (https, tro thang toi bai), nguon.ngay va
                    ket_qua "dung" (agent da mo va doc trang); "khong-mo-duoc", "khac-nhau", "sai" la loi chan.
                    Trang ban le, Wikipedia, blog, mang xa hoi khong dung lam can cu (quy tac chung cua SKILL.md).
  khong-khang-dinh  cau chuyen y, thao tac don thuan ("Cat bang keo, mo thung ra.") khong can can cu.
Moi cau chu chuan cua canh (subtitle neu co, khong thi narration; narration ghi cach doc thi khong xet) trong scenes.json
phai duoc mot muc phu (so khop khong dau, khong phan biet hoa thuong).
Nguon cung hang 1 hay hang 2 la viec cua agent kiem chung: script chi bat loi thieu truong va ten mien khong cho phep.
Gioi han: tach cau theo dau . ! ? ; khong hieu ngu nghia, nen viec phan loai dung hay sai van la cua nguoi duyet.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

LOAI = ("nhan", "quan-sat", "nguon-ngoai", "khong-khang-dinh")

# cau quan-sat chua cac cum nay phai co xac_nhan = "co" (viet khong dau)
NHAY_CAM = ("thao roi", "thao ra duoc", "thao duoc", "tach roi", "khong mop", "khong me", "khong hu", "khong tray",
            "khong xuoc", "nguyen ven", "con nguyen", "khong rach", "con moi", "chua mo", "chua qua su dung",
            "hang chinh hang", "hang that", "chinh hang")

# ten mien khong dung lam can cu (SKILL.md, quy tac chung: Nguon)
MIEN_CAM = ("wikipedia.org", "facebook.com", "tiktok.com", "youtube.com", "youtu.be", "medium.com", "blogspot.com",
            "wordpress.com", "shopee.vn", "lazada.vn", "tiki.vn", "sendo.vn", "tiktokshop", "reddit.com", "quora.com")


def bo_dau(s):
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "d"))
    return re.sub(r"[^a-z0-9 ]+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip()


def chuan(s):
    return re.sub(r"\s+", " ", bo_dau(s))


def tach_cau(s):
    return [c.strip() for c in re.split(r"(?<=[.!?;])\s+", s.strip()) if c.strip()]


def doc_canh(proj):
    d = json.loads((proj / "scenes.json").read_text(encoding="utf-8"))
    return d["scenes"]


def khoi(proj):
    out = []
    for sc in doc_canh(proj):
        chu = sc.get("subtitle") or sc["narration"]
        for c in tach_cau(chu):
            out.append({"canh": sc["id"], "cau": c, "loai": "chua-phan-loai"})
    p = proj / "khang-dinh.json"
    if p.exists():
        sys.exit(f"[LOI] {p} da co; xoa hoac doi ten neu muon tao lai")
    p.write_text(json.dumps({"khang_dinh": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[OK] {p}: {len(out)} cau, dien loai cho tung cau roi chay: so_khang_dinh.py kiem {proj}")


def tai(proj):
    p = proj / "khang-dinh.json"
    if not p.exists():
        sys.exit(f"[LOI] chua co {p}: chay so_khang_dinh.py khoi {proj}")
    return json.loads(p.read_text(encoding="utf-8"))["khang_dinh"]


def dong_bo(proj):
    """Dong bo khang-dinh.json voi scenes.json sau khi sua loi: cau trung chu (cung canh, so khop khong dau) giu nguyen muc cu
    (loai, moc_giay, xac_nhan, nguon...); cau moi hoac doi chu ve "chua-phan-loai" (loai cu ghi o "loai_cu" neu cung canh con muc
    chua duoc dung); muc khong con cau nao tuong ung bi bo. Giu ban sao khang-dinh.truoc-dong-bo.json."""
    cu = tai(proj)
    (proj / "khang-dinh.truoc-dong-bo.json").write_text(json.dumps({"khang_dinh": cu}, ensure_ascii=False, indent=1), encoding="utf-8")
    con = {}
    for e in cu:
        con.setdefault((e["canh"], chuan(e["cau"])), []).append(e)
    moi, giu, them, doi = [], 0, [], []
    for sc in doc_canh(proj):
        chu = sc.get("subtitle") or sc["narration"]
        for c in tach_cau(chu):
            ds = con.get((sc["id"], chuan(c)))
            if ds:
                e = dict(ds.pop(0)); e["cau"] = c
                moi.append(e); giu += 1
            else:
                moi.append({"canh": sc["id"], "cau": c, "loai": "chua-phan-loai"})
                them.append(f"{sc['id']}: {c}")
    # muc cu khong con cau tuong ung: ghi loai cu vao cau moi chua phan loai cung canh (goi y), roi bo
    bo = [e for ds in con.values() for e in ds]
    for e in bo:
        for m in moi:
            if m["canh"] == e["canh"] and m["loai"] == "chua-phan-loai" and "loai_cu" not in m:
                if e.get("loai") and e["loai"] != "chua-phan-loai":
                    m["loai_cu"] = e["loai"]
                doi.append(e)
                break
    (proj / "khang-dinh.json").write_text(json.dumps({"khang_dinh": moi}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[OK] khang-dinh.json: giu {giu} muc cu, {len(them)} cau moi hoac doi chu ve chua-phan-loai, bo {len(bo)} muc khong con cau")
    for x in them:
        print(f"[CAN PHAN LOAI] {x}")
    for e in bo:
        print(f"[DA BO] {e['canh']}: {e['cau']} ({e.get('loai')})")


def kiem_tra(proj):
    """Tra ve (loi_chan, canh_bao)."""
    loi, cb = [], []
    mucs = tai(proj)
    scenes = doc_canh(proj)
    ids = {s["id"] for s in scenes}
    for i, m in enumerate(mucs, 1):
        t = f"muc {i} ({m.get('canh', '?')})"
        if m.get("canh") not in ids:
            loi.append(f"{t}: canh khong co trong scenes.json")
            continue
        if not m.get("cau"):
            loi.append(f"{t}: thieu truong cau")
            continue
        loai = m.get("loai")
        if loai == "chua-phan-loai":
            loi.append(f"{t}: chua phan loai: \"{m['cau'][:50]}\"")
            continue
        if loai not in LOAI:
            loi.append(f"{t}: loai khong hop le: {loai!r} (chon: {', '.join(LOAI)})")
            continue
        if loai == "nhan":
            if not isinstance(m.get("moc_giay"), (int, float)):
                loi.append(f"{t}: loai nhan can moc_giay")
            if not m.get("nhan_doc"):
                loi.append(f"{t}: loai nhan can nhan_doc (chu da doc tren hinh)")
        elif loai == "quan-sat":
            if not isinstance(m.get("moc_giay"), (int, float)):
                loi.append(f"{t}: loai quan-sat can moc_giay (khung hinh thay ro dieu do)")
            xn = m.get("xac_nhan")
            if xn not in ("co", "khong", "chua"):
                loi.append(f"{t}: quan-sat can xac_nhan = co | khong | chua")
            elif xn == "khong":
                loi.append(f"{t}: khong thay ro tren hinh, phai xoa cau: \"{m['cau'][:50]}\"")
            elif xn == "chua":
                loi.append(f"{t}: cho nguoi quay xac nhan: \"{m['cau'][:50]}\"")
            n = chuan(m["cau"])
            if xn != "co" and any(k in n for k in NHAY_CAM):
                loi.append(f"{t}: cau nhay cam can xac_nhan = co: \"{m['cau'][:50]}\"")
        elif loai == "nguon-ngoai":
            ng = m.get("nguon") or {}
            for k in ("don_vi", "url", "ngay"):
                if not ng.get(k):
                    loi.append(f"{t}: nguon-ngoai can nguon.{k}")
            url = ng.get("url", "")
            if url:
                if not url.startswith("https://"):
                    loi.append(f"{t}: url phai bat dau bang https://")
                if re.fullmatch(r"https://[^/]+/?", url):
                    loi.append(f"{t}: url la trang chu, can link thang toi bai hoac van ban")
                if any(d in url.lower() for d in MIEN_CAM):
                    loi.append(f"{t}: ten mien khong dung lam can cu: {url}")
            kq = m.get("ket_qua")
            if kq != "dung":
                loi.append(f"{t}: ket_qua phai la dung (da mo va doc trang); hien la {kq!r}")
        if loai != "quan-sat" and any(k in chuan(m["cau"]) for k in NHAY_CAM[:6]):
            cb.append(f"{t}: cau co cum nhay cam nhung xep loai {loai}: \"{m['cau'][:50]}\"")
    # phu het cau
    for sc in scenes:
        mc = [chuan(m["cau"]) for m in mucs if m.get("canh") == sc["id"] and m.get("cau")]
        chu = sc.get("subtitle") or sc.get("narration") or ""
        for c in tach_cau(chu):
            n = chuan(c)
            if n and not any(n == x or n in x or x in n for x in mc if x):
                loi.append(f"canh {sc['id']}: cau chua co muc trong so: \"{c[:50]}\"")
    return loi, cb


def ghi(proj):
    mucs = tai(proj)
    rows = ["# Kiem chung", "", "| Canh | Cau | Loai | Moc (giay) | Can cu | Ket qua |", "|---|---|---|---|---|---|"]
    for m in mucs:
        loai = m.get("loai", "")
        mc = m.get("moc_giay", "")
        if loai == "nhan":
            cc, kq = f"nhan: {m.get('nhan_doc', '')}", "doc tu hinh"
        elif loai == "quan-sat":
            cc, kq = m.get("ghi_chu", ""), {"co": "da xac nhan", "khong": "khong thay ro", "chua": "cho xac nhan"}.get(m.get("xac_nhan"), "")
        elif loai == "nguon-ngoai":
            ng = m.get("nguon") or {}
            cc = f"{ng.get('don_vi', '')}, {ng.get('ngay', '')}, {ng.get('url', '')}"
            kq = m.get("ket_qua", "")
        else:
            cc, kq = "", "khong khang dinh"
        c = lambda x: str(x).replace("|", "/")
        rows.append(f"| {m.get('canh', '')} | {c(m.get('cau', ''))} | {loai} | {mc} | {c(cc)} | {kq} |")
    (proj / "kiem-chung.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"[OK] {proj / 'kiem-chung.md'}: {len(mucs)} muc")


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("khoi", "dong-bo", "kiem", "ghi"):
        sys.exit(__doc__)
    cmd, proj = sys.argv[1], Path(sys.argv[2])
    if cmd == "khoi":
        return khoi(proj)
    if cmd == "dong-bo":
        return dong_bo(proj)
    loi, cb = kiem_tra(proj)
    for x in cb:
        print(f"[CANH BAO] {x}", file=sys.stderr)
    if loi:
        for x in loi:
            print(f"[LOI] {x}", file=sys.stderr)
        sys.exit(f"[CHAN] {len(loi)} loi trong so khang dinh: sua truoc khi long tieng")
    print("[OK] so khang dinh hop le")
    if cmd == "ghi":
        ghi(proj)


if __name__ == "__main__":
    main()
