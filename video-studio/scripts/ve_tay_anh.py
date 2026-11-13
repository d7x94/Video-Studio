#!/usr/bin/env python3
"""Chuan bi tranh cho canh ve tay (kieu hinh vetay).

Dung:
  python3 ve_tay_anh.py PROJECT [--paper "#efe5d2"] [--only s03]

Doc tranh nguoi dung gui trong PROJECT/tranh/:
  <id>.jpg|png|webp        tranh ngang 16:9 (bat buoc)
  <id>-doc.jpg|png|webp    tranh doc 9:16 (khong bat buoc; khong co thi cat tu tranh ngang)
Voi moi khung da dung (PROJECT/build/portrait, build/landscape), ghi vao build/<kho>/img/:
  <id>.jpg          tranh mau, dung kich thuoc khung
  <id>-sketch.jpg   ban phac chi tren nen giay (luot ve dau tien)
Cat tranh ngang cho kho doc theo truong "focus" (0..1, vi tri ngang tam diem) cua canh trong
scenes.json; mac dinh 0.5. Mau giay phai trung --paper voi bien --paper trong index.html.
In ra canh thieu tranh va canh co tranh qua nho (canh ngan duoi 70% khung).
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

SIZES = {"landscape": (1920, 1080), "portrait": (1080, 1920)}
EXTS = (".jpg", ".jpeg", ".png", ".webp")


def find(folder: Path, stem: str):
    for e in EXTS:
        for p in (folder / (stem + e), folder / (stem + e.upper())):
            if p.exists():
                return p
    return None


def cover(img: Image.Image, size, focus=0.5):
    """Phong va cat cho phu kin khung, giu tam diem ngang o vi tri focus."""
    W, H = size
    s = max(W / img.width, H / img.height)
    w, h = round(img.width * s), round(img.height * s)
    img = img.resize((w, h), Image.LANCZOS)
    x = round(min(max(focus * w - W / 2, 0), w - W))
    y = round((h - H) / 2)
    return img.crop((x, y, x + W, y + H))


def sketch(img: Image.Image, paper):
    """Phac chi: net lay bang phep 'color dodge' (xam / (1 - xam am ban mo)), to len giay,
    them mot lop mau rat nhat de luot to mau sau chuyen tiep mem."""
    g = np.asarray(ImageOps.grayscale(img), dtype=np.float32) / 255.0
    inv = 1.0 - g
    blur = np.asarray(Image.fromarray((inv * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)),
                      dtype=np.float32) / 255.0
    lines = np.clip(g / np.maximum(1.0 - blur, 1e-3), 0, 1)
    lines = np.power(lines, 2.2)                       # net dam hon
    paper = np.array(paper, dtype=np.float32)[None, None, :] / 255.0
    col = np.asarray(img, dtype=np.float32) / 255.0
    wash = paper * 0.82 + col * 0.18                   # mau nhat
    ink = np.array([0x3b, 0x26, 0x20], dtype=np.float32)[None, None, :] / 255.0
    l = lines[..., None]
    out = wash * l + ink * (1 - l) * 0.85 + wash * (1 - l) * 0.15
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--paper", default="#efe5d2")
    ap.add_argument("--only")
    a = ap.parse_args()
    proj = Path(a.project).expanduser()
    paper = tuple(int(a.paper.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    scenes = json.loads((proj / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    src = proj / "tranh"
    formats = [f for f in SIZES if (proj / "build" / f / "index.html").exists()]
    if not formats:
        raise SystemExit("Chua co build/portrait hay build/landscape: chay new_project.sh ... vetay truoc")
    missing, small = [], []
    for sc in scenes:
        sid = sc["id"]
        if a.only and sid != a.only:
            continue
        land = find(src, sid)
        if not land:
            missing.append(sid)
            continue
        for f in formats:
            W, H = SIZES[f]
            p = find(src, sid + "-doc") if f == "portrait" else None
            img = Image.open(p or land).convert("RGB")
            if min(img.width / W, img.height / H) < 0.7 and max(img.width / W, img.height / H) < 1.0:
                small.append(f"{sid} ({f}): {img.width}x{img.height}")
            focus = 0.5 if p else float(sc.get("focus", 0.5))
            out = proj / "build" / f / "img"
            out.mkdir(parents=True, exist_ok=True)
            c = cover(img, (W, H), focus)
            c.save(out / f"{sid}.jpg", quality=90)
            sketch(c, paper).save(out / f"{sid}-sketch.jpg", quality=88)
        print(f"[OK] {sid}: {', '.join(formats)}")
    if missing:
        print("[THIEU] chua co tranh: " + ", ".join(missing) + f" (dat vao {src}/<id>.jpg)")
    if small:
        print("[CANH BAO] tranh nho, se bi mo: " + "; ".join(small))
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
