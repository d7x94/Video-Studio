#!/usr/bin/env python3
"""Tai nhan vat 3D (Quaternius, CC0) vao bo nho dem va chep vao composition.

Dung:
  python3 get_characters.py --list
  python3 get_characters.py BUILD_DIR Doctor_Female_Young Casual_Female ...

Tai tu GitHub Release cua repo truoc (ten tag trong assets/sim3d/characters.json), khong
duoc thi tu Google Drive cong khai cua tac gia. Drive can hai ten mien drive.google.com va
drive.usercontent.google.com (claude.ai > Settings > Capabilities) va co the bao het han muc.
File da tai nam o ~/studio/.tools/characters/; file nao cung phai khop kich thuoc va sha256
trong danh muc (neu danh muc da ghi) moi dung.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CATALOG = json.loads((SKILL / "assets/sim3d/characters.json").read_text(encoding="utf-8"))
CACHE = Path(os.environ.get("STUDIO_HOME", Path.home() / "studio")) / ".tools" / "characters"
DRIVE = "https://drive.usercontent.google.com/download?id={id}&export=download"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def valid(path: Path, size=None, sha=None):
    """Tra ve None neu file dung, khong thi ly do sai."""
    if not path.exists():
        return "khong co file"
    # Drive tra trang HTML voi ma 200 khi het han muc hoac can xac nhan
    if path.read_bytes()[:200].lstrip().lower().startswith((b"<!doctype html", b"<html")):
        return "may chu tra ve trang HTML thay vi file (Google Drive het han muc tai?)"
    if size and path.stat().st_size != size:
        return f"{path.stat().st_size} byte, danh muc ghi {size}"
    if sha and sha256(path) != sha:
        return "sai sha256"
    return None


def fetch(asset, file_id, dest: Path, size=None, sha=None):
    """Tai `asset` tu GitHub Release, khong duoc thi tu Google Drive; kiem tra roi moi nhan."""
    tmp = dest.with_suffix(dest.suffix + ".part")
    urls = []
    if CATALOG.get("release_tag"):
        urls.append(("GitHub Release", CATALOG["release_url"].format(tag=CATALOG["release_tag"], asset=asset)))
    urls.append(("Google Drive", DRIVE.format(id=file_id)))
    why = []
    for name, url in urls:
        r = subprocess.run(["curl", "-fsSL", "-m", "180", "-o", str(tmp), url], capture_output=True, text=True)
        bad = r.stderr.strip()[:200] or "curl loi" if r.returncode != 0 else valid(tmp, size, sha)
        if not bad:
            tmp.rename(dest)
            return name
        why.append(f"{name}: {bad}")
        tmp.unlink(missing_ok=True)
    sys.exit(f"[LOI] Khong tai duoc {dest.name}.\n  " + "\n  ".join(why) +
             "\nKiem tra mang toi github.com; Google Drive het han muc thi thu lai sau (co khi mat 24 gio).")


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
    lic = CACHE / CATALOG["license_asset"]
    if valid(lic, sha=CATALOG.get("license_sha256")):
        fetch(lic.name, CATALOG["license_file_id"], lic, sha=CATALOG.get("license_sha256"))
    (build / "assets").mkdir(parents=True, exist_ok=True)
    for n in names:
        dest = CACHE / f"{n}.gltf"
        src = "bo nho dem"
        if valid(dest, chars[n]["size"], chars[n].get("sha256")):
            src = fetch(dest.name, chars[n]["id"], dest, chars[n]["size"], chars[n].get("sha256"))
        shutil.copy2(dest, build / "assets" / dest.name)
        print(f"[OK] {n} ({src})")
    shutil.copy2(lic, build / "assets" / lic.name)


if __name__ == "__main__":
    main()
