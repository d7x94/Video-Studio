#!/usr/bin/env python3
"""Dong goi thanh pham cho che do long tieng video co san (khong co thumbnail, khong doi hoi 1080p).

Dung:  python3 giao_co_san.py PROJECT [--ra giao]

Sau khi job.py dung (va so_khang_dinh.py ghi) xong, gom vao PROJECT/giao/:
  <ten>_khong-phu-de.mp4          tu output/<ten>.mp4
  <ten>_phu-de-tung-tu.mp4        tu output/<ten>-phu-de-tung-tu.mp4 (neu co)
  <ten>_chu.mp4, <ten>_chu-phu-de-tung-tu.mp4   tu output/<ten>-chu*.mp4 (neu co)
  phu-de.srt, loi-doc.md          tu output/
  kiem-chung.md                   tu PROJECT (bat buoc, so khang dinh da ghi)
  metadata.md                     tu PROJECT/metadata.md (viet theo ho so the loai; chua co thi canh bao, khong tu bia)
  credits.md                      tu sinh tu job.json va file da tao: giong, nhac nen (neu co), font phu de, lam mo (neu co)
In danh sach file de goi SendUserFile tung file. ten lay tu job.json ("ten", mac dinh video).
Thoat ma 1 neu thieu video chinh hoac kiem-chung.md. Khong ghi de PROJECT/metadata.md va PROJECT/credits.md.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path


def font_phu_de(proj):
    f = proj / "phu-de-tung-tu.ass"
    if not f.exists():
        return None
    for dong in f.read_text(encoding="utf-8").splitlines():
        if dong.startswith("Style:"):
            return dong.split(":", 1)[1].split(",")[1].strip()
    return None


def credits(proj, job):
    d = ["# Credits", "- Hinh: canh quay do nguoi dung cung cap."]
    if job.get("lam_mo"):
        d[-1] += " Chi lam mo vung nhay cam da khai bao trong job.json."
    d.append(f"- Giong doc: {job.get('giong') or 'chua ghi'} (VieNeu, co watermark am thanh mac dinh).")
    nhac = (job.get("nhac") or {}).get("kieu", "khong")
    if nhac != "khong":
        d.append(f"- Nhac nen: do studio tu sang tac bang code (kieu {nhac}), khong dung nhac ben thu ba.")
    ft = font_phu_de(proj)
    if (proj / "phu-de-tung-tu.ass").exists():
        d.append("- Phu de tung tu: do hoa tu tao cua studio" + (f" (font {ft})." if ft else "."))
    if (job.get("chu") or []):
        d.append("- Chu ghi tren hinh: do hoa tu tao cua studio.")
    return "\n".join(d) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--ra", default="giao")
    a = ap.parse_args()
    proj = Path(a.project)
    out = proj / a.ra
    jp = proj / "job.json"
    job = json.loads(jp.read_text(encoding="utf-8")) if jp.exists() else {}
    ten = job.get("ten") or "video"
    od = proj / "output"
    loi, cb, made = [], [], []
    out.mkdir(exist_ok=True)

    def chep(src, dst):
        if src.exists() and src.stat().st_size > 0:
            shutil.copy2(src, out / dst)
            made.append(out / dst)
            return True
        return False

    if not chep(od / f"{ten}.mp4", f"{ten}_khong-phu-de.mp4"):
        loi.append(f"chua co {od / (ten + '.mp4')}: chay job.py dung truoc")
    for hau, dst in (("-phu-de-tung-tu", "phu-de-tung-tu"), ("-chu", "chu"), ("-chu-phu-de-tung-tu", "chu-phu-de-tung-tu")):
        chep(od / f"{ten}{hau}.mp4", f"{ten}_{dst}.mp4")
    for f in ("phu-de.srt", "loi-doc.md"):
        if not chep(od / f, f):
            cb.append(f"thieu output/{f}")
    if not chep(proj / "kiem-chung.md", "kiem-chung.md"):
        loi.append("chua co kiem-chung.md: chay so_khang_dinh.py ghi")
    if not chep(proj / "metadata.md", "metadata.md"):
        cb.append("chua co metadata.md: viet theo ho so the loai (khong tu bia noi dung), roi chay lai")
    cp = proj / "credits.md"
    (out / "credits.md").write_text(cp.read_text(encoding="utf-8") if cp.exists() else credits(proj, job), encoding="utf-8")
    made.append(out / "credits.md")

    for x in cb:
        print(f"[CANH BAO] {x}")
    for x in loi:
        print(f"[LOI] {x}")
    print("File giao (gui tung file bang SendUserFile):")
    for f in made:
        print(f"  {f}")
    sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()
