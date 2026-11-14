#!/usr/bin/env python3
"""Kiem tra chu tren hinh co du thoi gian de doc khong (truoc khi render).

Dung:  python3 doc_chu.py PROJECT/scenes.json PROJECT/timeline.json [--cps 15] [--pad 1.5] [--min 1.5]

Quy tac (y tuong tu readcheck.mjs cua Lemo-Opuscar, MIT, xem README muc Ghi cong):
  thoi gian can = so ky tu khong tinh khoang trang cua eyebrow + title + body / cps + pad, toi thieu --min giay.
  Thoi gian co = visual_duration cua canh trong timeline.json.
Chi dua tren chu va thoi luong canh, khong biet hieu ung vao/ra cua chu trong composition, nen la canh bao
de bien kich rut chu hoac keo dai canh, khong thay duoc mat nguoi. Cac he so mac dinh (15 ky tu/giay, 1,5 giay)
lay tu Lemo-Opuscar cho chu Latin, chua do rieng cho tieng Viet: chinh bang --cps neu thay qua chat hoac qua long.
on_screen.source chi liet ke, khong tinh gio (dong nguon la tham chieu, khong bat buoc doc het).
Ma thoat 1 khi co canh thieu thoi gian doc, 2 khi khong doc duoc dau vao.
"""
import argparse
import json
import sys
from pathlib import Path

FIELDS = ["eyebrow", "title", "body"]


def count(text):
    return sum(1 for ch in (text or "") if not ch.isspace())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes")
    ap.add_argument("timeline")
    ap.add_argument("--cps", type=float, default=15.0)
    ap.add_argument("--pad", type=float, default=1.5)
    ap.add_argument("--min", dest="minimum", type=float, default=1.5)
    a = ap.parse_args()
    if a.cps <= 0:
        print("[LOI] --cps phai lon hon 0")
        sys.exit(2)
    try:
        scenes = {s["id"]: s for s in json.loads(Path(a.scenes).read_text(encoding="utf-8"))["scenes"]}
        timeline = json.loads(Path(a.timeline).read_text(encoding="utf-8"))["scenes"]
    except (OSError, KeyError, ValueError) as e:
        print(f"[LOI] Khong doc duoc dau vao: {e}")
        sys.exit(2)

    bad = 0
    for sc in timeline:
        sid = sc["id"]
        on = (scenes.get(sid) or {}).get("on_screen") or {}
        n = sum(count(on.get(f)) for f in FIELDS)
        src = count(on.get("source"))
        if n == 0:
            print(f"--  {sid}: khong co chu chinh" + (f" (dong nguon {src} ky tu, khong tinh gio)" if src else ""))
            continue
        need = max(a.minimum, n / a.cps + a.pad)
        have = float(sc["visual_duration"])
        ok = have + 1e-6 >= need
        bad += 0 if ok else 1
        extra = f", dong nguon {src} ky tu khong tinh gio" if src else ""
        print(f"{'OK ' if ok else 'THIEU'} {sid}: {n} ky tu, can {need:.2f}s, co {have:.2f}s{extra}")
        if not ok:
            print(f"      cach sua: rut chu con khoang {max(0, int((have - a.pad) * a.cps))} ky tu, hoac keo dai canh them {need - have:.2f}s")
    print("KET QUA:", "DAT" if not bad else f"{bad} CANH THIEU THOI GIAN DOC")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
