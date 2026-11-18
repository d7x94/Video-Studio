#!/usr/bin/env python3
"""Ma khang dinh: moi claim trong scenes.json co ma (k01, k02...), moi ma co dung mot dong trong kiem-chung.md.

Dung:
  python3 ma_khang_dinh.py gan PROJECT        # doi claims dang chuoi thanh {"id": "k01", "text": "..."}; chay lai khong doi gi
  python3 ma_khang_dinh.py liet-ke PROJECT    # in bang Ma | Canh | Thong tin de dua cho agent kiem chung
  python3 ma_khang_dinh.py kiem PROJECT       # doi chieu scenes.json voi kiem-chung.md; thoat 1 neu con loi chan

Bang trong kiem-chung.md co cot (theo ten cot, khong theo thu tu):
  Ma | Canh | Thong tin | Ket luan | Nguon | Trich doan | De xuat
Ket luan do agent kiem chung ghi: Dung, Can sua, Khong kiem chung duoc. Sau khi dieu phoi ap sua doi vao
scenes.json thi doi ket luan cua dong do: Da sua (claim da viet lai theo de xuat), Da bo (claim da bo khoi
scenes.json). Dong agent tim them ma bien kich bo sot ghi Ma = moi; dieu phoi them claim vao canh
(chay lai gan) roi doi Ma cua dong do thanh ma moi cap.

kiem chan (thoat 1) khi:
  THIEU        claim trong scenes.json khong co dong nao trong kiem-chung.md
  MO-COI       dong co ma khong co trong scenes.json (tru dong Da bo)
  CHUA-XU-LY   dong con Can sua hoac Khong kiem chung duoc; hoac Ma = moi
  DA-BO        dong Da bo nhung claim van con trong scenes.json
  LECH-CAU     dong Dung nhung cau claim trong scenes.json khac cau da kiem chung (claim bi sua sau khi kiem)
  THIEU-NGUON  dong Dung hoac Da sua thieu Nguon hoac Trich doan
  KHONG-HIEU   ket luan khong thuoc 5 gia tri tren
Chi canh bao (khong chan): Trich doan dai hon 25 chu; canh co chu so trong loi doc ma khong co claim nao.
Script khong biet nguon co that hay trich doan co dung khong: viec do la cua agent kiem chung va nguoi duyet.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

KIEM_CHUNG = "kiem-chung.md"
GIA_TRI = {"dung": "dung", "can sua": "can-sua", "khong kiem chung duoc": "khong-duoc",
           "da sua": "da-sua", "da bo": "da-bo"}


def bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


def chuan_cau(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().rstrip(".").strip().casefold()


def doc_scenes(project: Path):
    p = project / "scenes.json"
    if not p.exists():
        sys.exit(f"[LOI] Khong thay {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data["scenes"]
    except (ValueError, KeyError) as e:
        sys.exit(f"[LOI] scenes.json hong: {e}")
    return p, data


def tat_ca_claims(data: dict):
    """Tra ve list (scene_id, id hoac None, text)."""
    out = []
    for sc in data["scenes"]:
        for c in sc.get("claims") or []:
            if isinstance(c, dict):
                out.append((sc["id"], c.get("id"), str(c.get("text", ""))))
            else:
                out.append((sc["id"], None, str(c)))
    return out


def so_ma(i: str) -> int:
    m = re.fullmatch(r"k(\d+)", i or "")
    return int(m.group(1)) if m else 0


def cmd_gan(project: Path, a):
    p, data = doc_scenes(project)
    co = [i for _, i, _ in tat_ca_claims(data) if i]
    if len(set(co)) != len(co):
        sys.exit("[LOI] Co ma claim trung nhau trong scenes.json")
    for i in co:
        if so_ma(i) == 0:
            sys.exit(f"[LOI] Ma claim sai dang (can k01, k02...): {i}")
    nxt = max([so_ma(i) for i in co] or [0])
    moi = 0
    for sc in data["scenes"]:
        ds = []
        for c in sc.get("claims") or []:
            if isinstance(c, dict):
                ds.append(c)
                continue
            nxt += 1
            moi += 1
            ds.append({"id": f"k{nxt:02d}", "text": str(c)})
        if sc.get("claims"):
            sc["claims"] = ds
    if moi:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tong = len(tat_ca_claims(data))
    print(f"Da gan ma cho {moi} claim moi; tong {tong} claim.")


def cmd_liet_ke(project: Path, a):
    _, data = doc_scenes(project)
    cl = tat_ca_claims(data)
    if any(i is None for _, i, _ in cl):
        sys.exit("[LOI] Con claim chua co ma: chay gan truoc")
    print("| Ma | Canh | Thong tin |\n|---|---|---|")
    for sid, i, t in cl:
        print(f"| {i} | {sid} | {t.replace('|', '/')} |")


def tach_bang(text: str):
    """Tra ve (list dong dict, loi). Lay bang dau tien co cot Ma."""
    dong, cot = [], None
    for ln in text.splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            if cot and dong:
                break      # het bang
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cot is None:
            names = [bo_dau(c).replace("*", "").replace("`", "") for c in cells]
            if "ma" in names:
                cot = names
            continue
        if all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells):
            continue
        if len(cells) < len(cot):
            cells += [""] * (len(cot) - len(cells))
        dong.append({cot[i]: cells[i] for i in range(len(cot))})
    return dong, cot


def lam_sach(s: str) -> str:
    return re.sub(r"[*`]", "", s or "").strip()


def cmd_kiem(project: Path, a):
    _, data = doc_scenes(project)
    cl = tat_ca_claims(data)
    chan, canh_bao = [], []
    if any(i is None for _, i, _ in cl):
        sys.exit("[LOI] Con claim chua co ma: chay gan truoc")
    f = project / KIEM_CHUNG
    if not f.exists():
        if cl:
            chan.append(f"THIEU     chua co {KIEM_CHUNG} nhung scenes.json co {len(cl)} claim (ho so khong kiem chung thi de claims rong)")
    else:
        dong, cot = tach_bang(f.read_text(encoding="utf-8"))
        if cot is None:
            if cl:
                sys.exit(f"[LOI] {KIEM_CHUNG} khong co bang co cot Ma. Cot can: Ma | Canh | Thong tin | Ket luan | Nguon | Trich doan | De xuat")
        else:
            for c in ("ket luan", "nguon", "trich doan"):
                if c not in cot:
                    sys.exit(f"[LOI] Bang {KIEM_CHUNG} thieu cot '{c}'")
        theo_ma = {}
        for d in (dong if cot else []):
            ma = lam_sach(d.get("ma", ""))
            theo_ma.setdefault(ma, []).append(d)
        hien = {i: (sid, t) for sid, i, t in cl}
        for i, (sid, t) in hien.items():
            if i not in theo_ma:
                chan.append(f"THIEU     {i} ({sid}): {t[:70]}")
        for ma, ds in theo_ma.items():
            for d in ds:
                kl = GIA_TRI.get(bo_dau(lam_sach(d.get("ket luan", ""))))
                nguon, trich = lam_sach(d.get("nguon", "")), lam_sach(d.get("trich doan", ""))
                if bo_dau(ma) == "moi":
                    chan.append(f"CHUA-XU-LY  dong Ma=moi ({lam_sach(d.get('thong tin', ''))[:60]}): them claim vao scenes.json roi doi ma")
                    continue
                if kl is None:
                    chan.append(f"KHONG-HIEU  {ma}: ket luan '{lam_sach(d.get('ket luan', ''))}'")
                    continue
                if kl in ("can-sua", "khong-duoc"):
                    chan.append(f"CHUA-XU-LY  {ma}: con '{lam_sach(d.get('ket luan', ''))}', sua claim hoac bo roi doi ket luan thanh Da sua / Da bo")
                if kl == "da-bo":
                    if ma in hien:
                        chan.append(f"DA-BO       {ma}: dong ghi Da bo nhung claim van con trong scenes.json")
                    continue
                if ma not in hien:
                    chan.append(f"MO-COI      {ma}: dong khong co claim tuong ung trong scenes.json")
                    continue
                if kl in ("dung", "da-sua") and (not nguon or not trich):
                    chan.append(f"THIEU-NGUON {ma}: thieu " + ("Nguon" if not nguon else "Trich doan"))
                if kl == "dung" and chuan_cau(lam_sach(d.get("thong tin", ""))) != chuan_cau(hien[ma][1]):
                    chan.append(f"LECH-CAU    {ma}: claim trong scenes.json khac cau da kiem chung\n"
                                f"              da kiem: {lam_sach(d.get('thong tin', ''))[:90]}\n"
                                f"              hien tai: {hien[ma][1][:90]}")
                if len(trich.split()) > 25:
                    canh_bao.append(f"{ma}: Trich doan dai {len(trich.split())} chu (quy tac: duoi 25 chu)")
    co_claim = {sid for sid, _, _ in cl}
    for sc in data["scenes"]:
        if sc["id"] not in co_claim and re.search(r"\d", " ".join(
                [sc.get("narration") or "", json.dumps(sc.get("on_screen") or {}, ensure_ascii=False)])):
            canh_bao.append(f"{sc['id']}: co chu so trong loi doc hoac chu tren hinh nhung khong co claim (kiem lai bang mat)")
    for c in canh_bao:
        print(f"[CANH BAO] {c}")
    if chan:
        print(f"[CHAN] {len(chan)} loi giua scenes.json va {KIEM_CHUNG}:")
        for c in chan:
            print("  " + c)
        sys.exit(1)
    dem = {}
    if f.exists():
        for d in (dong if cot else []):
            k = GIA_TRI.get(bo_dau(lam_sach(d.get("ket luan", ""))))
            dem[k] = dem.get(k, 0) + 1
    tom = ", ".join(f"{n}: {dem[k]}" for k, n in
                    (("dung", "Dung"), ("da-sua", "Da sua"), ("da-bo", "Da bo")) if dem.get(k))
    print(f"Khang dinh khop kiem chung: {len(cl)} claim" + (f" ({tom})" if tom else "") + ".")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="lenh", required=True)
    for n in ("gan", "liet-ke", "kiem"):
        sub.add_parser(n).add_argument("project")
    a = ap.parse_args()
    {"gan": cmd_gan, "liet-ke": cmd_liet_ke, "kiem": cmd_kiem}[a.lenh](Path(a.project), a)


if __name__ == "__main__":
    main()
