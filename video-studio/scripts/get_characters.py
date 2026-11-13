#!/usr/bin/env python3
"""Tai nhan vat 3D (Quaternius, CC0) vao bo nho dem va chep vao composition.

Dung:
  python3 get_characters.py --list
  python3 get_characters.py BUILD_DIR Doctor_Female_Young Casual_Female ...

Tai tu Google Drive cong khai cua tac gia. Workspace phai cho phep hai ten mien
drive.google.com va drive.usercontent.google.com (claude.ai > Settings > Capabilities).
File da tai nam o ~/studio/.tools/characters/ va duoc kiem tra kich thuoc.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CATALOG = json.loads((SKILL / "assets/sim3d/characters.json").read_text(encoding="utf-8"))
CACHE = Path(os.environ.get("STUDIO_HOME", Path.home() / "studio")) / ".tools" / "characters"
URL = "https://drive.usercontent.google.com/download?id={id}&export=download"


def fetch(file_id, dest: Path, size=None):
    tmp = dest.with_suffix(dest.suffix + ".part")
    r = subprocess.run(["curl", "-sSL", "-m", "180", "-o", str(tmp), URL.format(id=file_id)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not tmp.exists():
        sys.exit(f"[LOI] Khong tai duoc {dest.name}: {r.stderr.strip()[:300]}\n"
                 "Kiem tra ten mien drive.google.com va drive.usercontent.google.com da duoc cho phep.")
    got = tmp.stat().st_size
    if size and got != size:
        head = tmp.read_bytes()[:120]
        tmp.unlink()
        sys.exit(f"[LOI] {dest.name}: tai ve {got} byte, danh muc ghi {size}. Dau file: {head!r}")
    tmp.rename(dest)


def main():
    args = sys.argv[1:]
    chars = CATALOG["characters"]
    if not args or args[0] == "--list":
        for name, c in chars.items():
            print(f"{name:22s} {c['vai']}")
        return
    build = Path(args[0])
    names = args[1:]
    unknown = [n for n in names if n not in chars]
    if unknown:
        sys.exit(f"[LOI] Khong co trong danh muc: {unknown}. Xem: python3 {sys.argv[0]} --list")
    CACHE.mkdir(parents=True, exist_ok=True)
    lic = CACHE / "LICENSE_Quaternius.txt"
    if not lic.exists():
        fetch(CATALOG["license_file_id"], lic)
    (build / "assets").mkdir(parents=True, exist_ok=True)
    for n in names:
        dest = CACHE / f"{n}.gltf"
        if not dest.exists():
            fetch(chars[n]["id"], dest, chars[n]["size"])
        shutil.copy2(dest, build / "assets" / dest.name)
        print(f"[OK] {n}")
    shutil.copy2(lic, build / "assets" / lic.name)


if __name__ == "__main__":
    main()
