#!/usr/bin/env python3
"""Ap cac dong phu de nguoi dung da sua (dang .srt) vao scenes.json va dong bo so khang dinh (video co san).

Dung:
  python3 ap_sua_srt.py PROJECT SUA.srt            # xem truoc: liet ke canh se doi, khong ghi gi
  python3 ap_sua_srt.py PROJECT SUA.srt --ap       # ghi scenes.json (giu ban sao scenes.truoc-sua.json) va khang-dinh.json

SUA.srt: cac khoi "so thu tu / dong thoi gian / chu", co the chi gom vai khoi nguoi dung sua (dan tu phu-de.srt). Khoi so N
ung voi canh thu N trong scenes.json (cung thu tu voi phu-de.srt do ghep_loi_video_co_san.py ghi). Khi co timeline_ghep.json,
moc bat dau trong khoi phai lech canh do khong qua 0,15 giay; lech hon thi bo qua khoi va bao [CANH BAO] (srt cu hay lech thu tu).
Cach doi voi tung canh:
  - canh khong co subtitle rieng: narration = chu moi (bo subtitle neu co)
  - canh co subtitle khac narration (narration ghi cach doc cho giong, vd "hat de em ai"): chi sua subtitle, narration giu nguyen
    va in [CAN XEM] de nguoi duyet tu sua cach doc cho khop
Khang-dinh.json: cau trong canh doi duoc tach lai theo dau . ! ? ; (so_khang_dinh.py). Neu so cau khong doi, giu truong cu va
dat lai viec can duyet: quan-sat -> xac_nhan "chua"; nhan va nguon-ngoai -> "chua-phan-loai" (chu doi thi can cu phai xem lai);
khong-khang-dinh giu nguyen. Neu so cau doi, cac muc cua canh thanh "chua-phan-loai" moi.
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

    doi, cb, xem = {}, [], []
    for so, bd, chu in khoi:
        if not 1 <= so <= len(canh):
            cb.append(f"khoi {so}: ngoai pham vi 1..{len(canh)}, bo qua")
            continue
        sc = canh[so - 1]
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
        out, da = [], set()
        for e in ds:
            sid = e["canh"]
            if sid not in doi:
                out.append(e)
                continue
            if sid in da:
                continue
            da.add(sid)
            cau_moi = tach_cau(doi[sid][1])
            cu = theo_canh[sid]
            if len(cu) == len(cau_moi):
                for e2, c in zip(cu, cau_moi):
                    e2 = dict(e2)
                    e2["cau"] = c
                    if e2.get("loai") == "quan-sat":
                        e2["xac_nhan"] = "chua"
                    elif e2.get("loai") in ("nhan", "nguon-ngoai"):
                        e2["loai"] = "chua-phan-loai"
                    out.append(e2)
            else:
                out += [{"canh": sid, "cau": c, "loai": "chua-phan-loai"} for c in cau_moi]
        kd_path.write_text(json.dumps({"khang_dinh": out}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[OK] khang-dinh.json: dong bo {len(doi)} canh; muc quan-sat/nhan/nguon-ngoai cua canh doi can duyet lai")
    else:
        print("[CANH BAO] chua co khang-dinh.json (chay so_khang_dinh.py khoi)", file=sys.stderr)
    print(f"[OK] scenes.json: {len(doi)} canh (ban sao: scenes.truoc-sua.json)")
    for sid in xem:
        print(f"[CAN XEM] {sid}: canh co narration ghi cach doc rieng, chi sua subtitle; kiem narration con khop chua")


if __name__ == "__main__":
    main()
