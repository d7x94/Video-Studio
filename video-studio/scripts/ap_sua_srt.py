#!/usr/bin/env python3
"""Ap cac dong phu de nguoi dung da sua (dang .srt) vao scenes.json va dong bo so khang dinh (video co san).

Dung:
  python3 ap_sua_srt.py PROJECT SUA.srt            # xem truoc: liet ke canh se doi, khong ghi gi
  python3 ap_sua_srt.py PROJECT SUA.srt --ap       # ghi scenes.json (giu ban sao scenes.truoc-sua.json) va khang-dinh.json

SUA.srt: cac khoi "so thu tu / dong thoi gian / chu", co the chi gom vai khoi nguoi dung sua (dan tu phu-de.srt).
ghep_loi_video_co_san.py danh so phu-de.srt theo moc bat dau tang dan, nen khoi so N ung voi canh thu N khi xep canh theo
moc trong timeline_ghep.json (khong phai thu tu trong scenes.json). Moc bat dau trong khoi phai lech canh do khong qua
0,15 giay; lech hon thi bo qua khoi va bao [CANH BAO] (srt cu). Chua co timeline_ghep.json day du thi dung thu tu scenes.json
va bao [CANH BAO] (khong kiem duoc moc).
Cach doi voi tung canh:
  - canh khong co subtitle rieng: narration = chu moi (bo subtitle neu co)
  - canh co subtitle khac narration (narration ghi cach doc cho giong, vd "hat de em ai"): chi sua subtitle, narration giu nguyen
    va in [CAN XEM] de nguoi duyet tu sua cach doc cho khop
Khang-dinh.json: cau trong canh doi duoc tach lai theo dau . ! ? ; (so_khang_dinh.py). Cau giu nguyen chu giu muc cu.
Cau doi chu ve "chua-phan-loai" bat ke loai cu, ke ca khong-khang-dinh (cau moi co the them so lieu), ghi loai cu o
"loai_cu" va bo xac_nhan, ket_qua; neu so cau khong doi thi giu goi y cung vi tri (moc_giay, nhan_doc, nguon).
Canh doi chua co muc nao trong so thi them muc "chua-phan-loai" cho tung cau moi.
Sau khi ap: python3 tts.py scenes.json . (chi doc lai canh doi), job.py dung, so_khang_dinh.py kiem va ghi, moc_tu.py,
phu_de_tung_tu.py. Script chi sua chu, khong tinh lai moc thoi gian va khong quyet dinh dung sai cua cau moi.
Yeu cau: python3.
"""
import argparse
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from so_khang_dinh import tach_cau  # noqa: E402

THOI = re.compile(r"^(\d+):(\d+):(\d+)[,.](\d+)\s*-->")


def giay(m):
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4).ljust(3, "0")[:3]) / 1000


def doc_srt(text):
    """Tra ve [(so, giay_bat_dau, chu)]; khoi bat dau bang dong chi co so ngay truoc dong thoi gian."""
    dong = text.replace("﻿", "").splitlines()
    kq, i = [], 0
    while i < len(dong):
        if dong[i].strip().isdigit() and i + 1 < len(dong) and THOI.match(dong[i + 1].strip()):
            so = int(dong[i].strip())
            bd = giay(THOI.match(dong[i + 1].strip()))
            j = i + 2
            chu = []
            while j < len(dong) and not (dong[j].strip().isdigit() and j + 1 < len(dong) and THOI.match(dong[j + 1].strip())):
                if dong[j].strip():
                    chu.append(dong[j].strip())
                j += 1
            kq.append((so, bd, unicodedata.normalize("NFC", " ".join(chu))))
            i = j
        else:
            i += 1
    return kq


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("srt")
    ap.add_argument("--ap", action="store_true")
    a = ap.parse_args()
    proj = Path(a.project)
    sc_path = proj / "scenes.json"
    data = json.loads(sc_path.read_text(encoding="utf-8"))
    canh = data["scenes"]
    moc = {}
    tg = proj / "timeline_ghep.json"
    if tg.exists():
        moc = json.loads(tg.read_text(encoding="utf-8")).get("start", {})
    khoi = doc_srt(Path(a.srt).read_text(encoding="utf-8"))
    if not khoi:
        sys.exit("[LOI] khong doc duoc khoi srt nao (can dong so thu tu ngay truoc dong thoi gian)")

    # phu-de.srt (ghep_loi_video_co_san.py) danh so theo moc bat dau tang dan, khong theo thu tu trong scenes.json
    cb, xem = [], []
    if moc and all(sc["id"] in moc for sc in canh):
        thu_tu = sorted(canh, key=lambda sc: float(moc[sc["id"]]))
    else:
        thu_tu = canh
        cb.append("chua co timeline_ghep.json day du: khoi N ung voi canh thu N trong scenes.json, khong kiem duoc moc; "
                  "chay job.py dung truoc de ghep dung canh")
    doi = {}
    for so, bd, chu in khoi:
        if not 1 <= so <= len(thu_tu):
            cb.append(f"khoi {so}: ngoai pham vi 1..{len(thu_tu)}, bo qua")
            continue
        sc = thu_tu[so - 1]
        sid = sc["id"]
        if sid in moc and abs(float(moc[sid]) - bd) > 0.15:
            cb.append(f"khoi {so} ({bd:.2f}s) lech moc canh {sid} ({float(moc[sid]):.2f}s): srt khong khop thu tu canh, bo qua")
            continue
        cu = sc.get("subtitle") or sc["narration"]
        if chu == cu:
            continue
        doi[sid] = (cu, chu)
    for x in cb:
        print(f"[CANH BAO] {x}", file=sys.stderr)
    if not doi:
        print("[OK] khong co canh nao doi")
        return
    for sid, (cu, moi) in doi.items():
        print(f"{sid}: {cu}\n    -> {moi}")
    if not a.ap:
        print(f"[OK] {len(doi)} canh se doi; chay lai voi --ap de ghi")
        return

    shutil.copyfile(sc_path, proj / "scenes.truoc-sua.json")
    for sc in canh:
        if sc["id"] not in doi:
            continue
        moi = doi[sc["id"]][1]
        if sc.get("subtitle") and sc["subtitle"] != sc["narration"]:
            sc["subtitle"] = moi
            xem.append(sc["id"])
        else:
            sc["narration"] = moi
            sc.pop("subtitle", None)
    sc_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    kd_path = proj / "khang-dinh.json"
    if kd_path.exists():
        shutil.copyfile(kd_path, proj / "khang-dinh.truoc-sua.json")
        ds = json.loads(kd_path.read_text(encoding="utf-8"))["khang_dinh"]
        theo_canh = {}
        for e in ds:
            theo_canh.setdefault(e["canh"], []).append(e)
        def muc_moi(sid, cu):
            """Muc cua canh doi: cau giu nguyen chu thi giu muc cu; cau doi chu (ke ca khong-khang-dinh) ve chua-phan-loai."""
            cau_moi = tach_cau(doi[sid][1])
            con = list(cu)
            kq = []
            for i, c in enumerate(cau_moi):
                giu = next((e for e in con if e.get("cau") == c), None)
                if giu is not None:
                    con.remove(giu)
                    kq.append(giu)
                    continue
                # so cau khong doi thi giu goi y cung vi tri (moc_giay, nhan_doc, nguon) cho nguoi duyet; bo ket qua duyet cu
                goc = dict(cu[i]) if len(cu) == len(cau_moi) else {}
                if goc.get("loai") and goc["loai"] != "chua-phan-loai":
                    goc["loai_cu"] = goc["loai"]
                goc.pop("xac_nhan", None)
                goc.pop("ket_qua", None)
                goc.update({"canh": sid, "cau": c, "loai": "chua-phan-loai"})
                kq.append(goc)
            return kq

        out, da = [], set()
        for e in ds:
            sid = e["canh"]
            if sid not in doi:
                out.append(e)
                continue
            if sid in da:
                continue
            da.add(sid)
            out += muc_moi(sid, theo_canh[sid])
        for sid in doi:
            if sid not in da:   # canh chua co muc nao trong so: them muc moi, khong de cau moi lot qua kiem
                out += muc_moi(sid, [])
        so_duyet = sum(1 for e in out if e.get("canh") in doi and e.get("loai") == "chua-phan-loai")
        kd_path.write_text(json.dumps({"khang_dinh": out}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[OK] khang-dinh.json: dong bo {len(doi)} canh; {so_duyet} cau doi chu ve chua-phan-loai, can phan loai va duyet lai")
    else:
        print("[CANH BAO] chua co khang-dinh.json (chay so_khang_dinh.py khoi)", file=sys.stderr)
    print(f"[OK] scenes.json: {len(doi)} canh (ban sao: scenes.truoc-sua.json)")
    for sid in xem:
        print(f"[CAN XEM] {sid}: canh co narration ghi cach doc rieng, chi sua subtitle; kiem narration con khop chua")


if __name__ == "__main__":
    main()
