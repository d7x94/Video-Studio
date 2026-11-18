#!/usr/bin/env python3
"""Tai mo hinh nhan dang giong noi Whisper (faster-whisper, CTranslate2) ban small hoac medium.

Dung:
  python3 lay_whisper.py small            # tai (neu chua co) va in duong dan thu muc mo hinh
  python3 lay_whisper.py medium
  python3 lay_whisper.py small --kiem     # chi kiem file da tai co dung kich thuoc va sha256 khong (thoat 1 neu thieu)

Dong cuoi in ra la duong dan thu muc mo hinh, dua thang cho faster_whisper.WhisperModel(duong_dan).
Mo hinh nam o $STUDIO_HOME/.tools/whisper/<ban> (mac dinh ~/studio/.tools/whisper/<ban>), khong dua vao git hay zip skill.

Danh muc: assets/whisper-models.json (ten file, kich thuoc, sha256, revision HuggingFace da ghim).
Tai tu GitHub Release cua repo truoc, khong duoc thi tu HuggingFace dung revision da ghim;
file nao cung phai khop kich thuoc va sha256 moi dung.

Chon ban: small (khoang 484 MB) cho viec kiem so va loi lech ro; medium (khoang 1,5 GB) khi can doc dung hon,
cham hon khoang 2,7 lan (do ngay 2026-11-18 tren 2 loi CPU, 10 cau giong Hai Dang). Chi tai ban can dung.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

STUDIO_HOME = Path(os.environ.get("STUDIO_HOME", Path.home() / "studio"))
ROOT = STUDIO_HOME / ".tools" / "whisper"
MANIFEST = json.loads((Path(__file__).resolve().parent.parent / "assets/whisper-models.json")
                      .read_text(encoding="utf-8"))
BANS = sorted({s["dir"] for s in MANIFEST["sources"].values()})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def curl(url: str, out: Path) -> bool:
    r = subprocess.run(["curl", "-fsSL", "--retry", "2", "-m", "900", "-o", str(out), url],
                       capture_output=True, text=True)
    return r.returncode == 0 and out.exists()


def da_dung(dest: Path, f: dict) -> bool:
    """File da co dung kich thuoc; sha256 da kiem thi ghi dau <file>.sha256 de lan sau khoi bam lai file lon."""
    if not (dest.exists() and dest.stat().st_size == f["size"]):
        return False
    mark = dest.with_name(dest.name + ".sha256")
    if mark.exists() and mark.read_text().strip() == f["sha256"]:
        return True
    if sha256(dest) == f["sha256"]:
        mark.write_text(f["sha256"] + "\n")
        return True
    print(f"[CANH BAO] {f['path']}: sai sha256, se tai lai", file=sys.stderr)
    dest.unlink()
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ban", choices=BANS)
    ap.add_argument("--kiem", action="store_true", help="chi kiem, khong tai")
    a = ap.parse_args()

    need = [f for f in MANIFEST["files"] if f["path"].startswith(a.ban + "/")]
    if a.kiem:
        thieu = [f["path"] for f in need if not da_dung(ROOT / f["path"], f)]
        if thieu:
            print("[THIEU] " + ", ".join(thieu), file=sys.stderr)
            sys.exit(1)
        print(ROOT / a.ban)
        return

    for f in need:
        dest = ROOT / f["path"]
        if da_dung(dest, f):
            continue
        dest.with_name(dest.name + ".sha256").unlink(missing_ok=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        rev = MANIFEST["sources"][f["repo"]]["revision"]
        urls = [("GitHub Release", MANIFEST["release_url"].format(tag=MANIFEST["release_tag"], asset=f["asset"])),
                ("HuggingFace", f"https://huggingface.co/{f['repo']}/resolve/{rev}/{f['hf_path']}")]
        for name, url in urls:
            if curl(url, tmp) and tmp.stat().st_size == f["size"] and sha256(tmp) == f["sha256"]:
                tmp.rename(dest)
                dest.with_name(dest.name + ".sha256").write_text(f["sha256"] + "\n")
                print(f"[OK] {f['path']} ({name})", file=sys.stderr)
                break
            tmp.unlink(missing_ok=True)
        else:
            sys.exit(f"[LOI] Khong tai duoc {f['path']} tu GitHub Release lan HuggingFace (hoac sai sha256).\n"
                     "Kiem tra mang toi github.com hoac huggingface.co.")
    print(ROOT / a.ban)


if __name__ == "__main__":
    main()
