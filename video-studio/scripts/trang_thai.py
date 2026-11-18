#!/usr/bin/env python3
"""Trang thai du an: ghi buoc nao da xong, de tiep tuc dung cho khi cuoc chat dai va ngu canh bi nen.

Dung:
  python3 trang_thai.py ghi PROJECT BUOC TRANG_THAI [--ghi-chu "..."] [--tep file1 file2 ...]
  python3 trang_thai.py xem PROJECT [--json]

BUOC: 0a 0 1 2 3 3b 3c 4 5 6 7 8
TRANG_THAI: dang-lam | xong | cho-nguoi-dung | loi | bo-qua

Ghi vao PROJECT/trang-thai.json (moi buoc: trang thai, luc ghi, ghi chu, cac tep dau ra kem kich thuoc).
`xem` in bang cac buoc, kiem cac tep da ghi con ton tai khong, va chi ra buoc tiep theo
(buoc dau tien chua xong va khong bi bo qua; 0a, 3b, 3c la buoc tuy chon, chi tinh khi da ghi dang-lam).
Dung ngay dau cuoc chat va moi khi nghi ngo minh dang o buoc nao.

Gioi han: file nam trong workspace nen khong sang duoc cuoc chat khac (xem muc Thu muc du an cua SKILL.md);
script chi giup trong mot cuoc chat. `xem` khong biet tep co dung noi dung hay khong, chi biet con hay mat.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

FILE = "trang-thai.json"
BUOC = ["0a", "0", "1", "2", "3", "3b", "3c", "4", "5", "6", "7", "8"]
TUY_CHON = {"0a", "3b", "3c"}
TEN = {"0a": "tim y tuong", "0": "nhan viec", "1": "dung moi truong", "2": "kich ban va kiem chung",
       "3": "cong duyet 1", "3b": "casting", "3c": "tranh (ve-tay)", "4": "long tieng", "5": "dung hinh",
       "6": "cong duyet 2", "7": "hoan thien va QA", "8": "giao goi"}
TRANG_THAI = ["dang-lam", "xong", "cho-nguoi-dung", "loi", "bo-qua"]


def bay_gio():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def doc(project: Path) -> dict:
    p = project / FILE
    if not p.exists():
        return {"ver": 1, "buoc": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        sys.exit(f"[LOI] {FILE} hong; xoa file de ghi lai")


def cmd_ghi(project: Path, a):
    if a.buoc not in BUOC:
        sys.exit(f"[LOI] Buoc '{a.buoc}' khong co. Cac buoc: {' '.join(BUOC)}")
    project.mkdir(parents=True, exist_ok=True)
    d = doc(project)
    tep = []
    for t in a.tep or []:
        f = project / t
        if not f.exists():
            sys.exit(f"[LOI] Tep {t} khong co trong {project}; chi ghi tep da ton tai")
        tep.append({"tep": t, "kich_thuoc": f.stat().st_size})
    d["buoc"][a.buoc] = {"trang_thai": a.trang_thai, "luc": bay_gio(), "ghi_chu": a.ghi_chu or "", "tep": tep}
    (project / FILE).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Buoc {a.buoc} ({TEN[a.buoc]}): {a.trang_thai}")


def buoc_tiep(d: dict):
    for b in BUOC:
        st = d["buoc"].get(b, {}).get("trang_thai")
        if st in ("xong", "bo-qua"):
            continue
        if b in TUY_CHON and st is None:
            continue
        return b
    return None


def cmd_xem(project: Path, a):
    d = doc(project)
    mat = []
    ra = []
    for b in BUOC:
        x = d["buoc"].get(b)
        if not x:
            ra.append({"buoc": b, "ten": TEN[b], "trang_thai": None})
            continue
        thieu = []
        for t in x.get("tep", []):
            f = project / t["tep"]
            if not f.exists():
                thieu.append(t["tep"])
        mat += [f"{b}: {t}" for t in thieu]
        ra.append({"buoc": b, "ten": TEN[b], **{k: x[k] for k in ("trang_thai", "luc", "ghi_chu")}, "tep_mat": thieu})
    tiep = buoc_tiep(d)
    if a.json:
        print(json.dumps({"ok": not mat, "buoc_tiep": tiep, "buoc": ra, "tep_mat": mat}, ensure_ascii=False))
        return
    for r in ra:
        if r["trang_thai"] is None:
            if r["buoc"] in TUY_CHON:
                continue
            print(f"  {r['buoc']:>2}  {r['ten']:<26} chua lam")
        else:
            print(f"  {r['buoc']:>2}  {r['ten']:<26} {r['trang_thai']:<16} {r['luc']}"
                  + (f"  [{r['ghi_chu']}]" if r["ghi_chu"] else ""))
    for m in mat:
        print(f"[MAT] tep da ghi khong con: {m}")
    print("Buoc tiep theo: " + (f"{tiep} ({TEN[tiep]})" if tiep else "het (da giao goi)"))
    if mat:
        print("Tep mat: lam lai buoc tao ra chung (workspace co the da duoc dat lai).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="lenh", required=True)
    g = sub.add_parser("ghi")
    g.add_argument("project")
    g.add_argument("buoc")
    g.add_argument("trang_thai", choices=TRANG_THAI)
    g.add_argument("--ghi-chu")
    g.add_argument("--tep", nargs="*")
    x = sub.add_parser("xem")
    x.add_argument("project")
    x.add_argument("--json", action="store_true", help="in mot dong JSON {ok, buoc_tiep, buoc, tep_mat}")
    a = ap.parse_args()
    {"ghi": cmd_ghi, "xem": cmd_xem}[a.lenh](Path(a.project), a)


if __name__ == "__main__":
    main()
