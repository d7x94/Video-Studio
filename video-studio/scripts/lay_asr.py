#!/usr/bin/env python3
"""Tai mo hinh nhan dang giong noi bo sung: Whisper large-v3 (CTranslate2), FireRedASR2-AED int8 (ONNX)
hoac FireRedLID (nhan dang ngon ngu, PyTorch).

Dung:
  python3 lay_asr.py large-v3            # tai (neu chua co) va in duong dan thu muc mo hinh
  python3 lay_asr.py firered2
  python3 lay_asr.py lid
  python3 lay_asr.py firered2 --kiem     # chi kiem file da tai co dung kich thuoc va sha256 khong (thoat 1 neu thieu)

Dong cuoi in ra la duong dan thu muc mo hinh.
Mo hinh nam o $STUDIO_HOME/.tools/asr/<ban> (mac dinh ~/studio/.tools/asr/<ban>), khong dua vao git hay zip skill.

Danh muc: assets/asr-models.json (large-v3, firered2) va assets/lid-models.json (lid): ten file, kich thuoc,
sha256, revision HuggingFace da ghim; moi danh muc mot release rieng.
Tai tu GitHub Release cua repo truoc, khong duoc thi tu HuggingFace dung revision da ghim; file nao cung phai
khop kich thuoc va sha256 moi dung. File lon hon 2 GiB (model.bin cua large-v3, model.pth.tar cua lid) tren release
nam o dang parts:
tai tung phan, kiem sha256 tung phan, ghep lai, kiem sha256 file day du.

Dung cho: large-v3 -> chep_loi_goc.py --ban large-v3 (khoang 3,1 GB); firered2 ->
chep_loi_firered.py (khoang 1,2 GB); lid -> chep_loi_goc.py --lid (khoang 3,6 GB). Chi tai ban can dung.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

STUDIO_HOME = Path(os.environ.get("STUDIO_HOME", Path.home() / "studio"))
ROOT = STUDIO_HOME / ".tools" / "asr"
ASSETS = Path(__file__).resolve().parent.parent / "assets"
MANIFESTS = [json.loads((ASSETS / ten).read_text(encoding="utf-8")) for ten in ("asr-models.json", "lid-models.json")]
BANS = sorted({s["dir"] for m in MANIFESTS for s in m["sources"].values()})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def curl(url: str, out: Path) -> bool:
    r = subprocess.run(["curl", "-fsSL", "--retry", "2", "-m", "1800", "-o", str(out), url],
                       capture_output=True, text=True)
    return r.returncode == 0 and out.exists()


def danh_muc(ban: str) -> dict:
    return next(m for m in MANIFESTS if any(s["dir"] == ban for s in m["sources"].values()))


def release_url(m: dict, asset: str) -> str:
    return m["release_url"].format(tag=m["release_tag"], asset=asset)


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


def tai_tu_release(m: dict, f: dict, tmp: Path) -> bool:
    """Tai file tu release. Co parts thi tai tung phan, kiem tung phan roi noi vao tmp. Kiem file day du o noi goi."""
    if not f.get("parts"):
        return curl(release_url(m, f["asset"]), tmp) and tmp.stat().st_size == f["size"] and sha256(tmp) == f["sha256"]
    tmp.unlink(missing_ok=True)
    phan = tmp.with_name(tmp.name + ".phan")
    with open(tmp, "wb") as out:
        for p in f["parts"]:
            phan.unlink(missing_ok=True)
            if not (curl(release_url(m, p["asset"]), phan) and phan.stat().st_size == p["size"]
                    and sha256(phan) == p["sha256"]):
                phan.unlink(missing_ok=True)
                return False
            with open(phan, "rb") as src:
                for block in iter(lambda: src.read(1 << 20), b""):
                    out.write(block)
            phan.unlink()
    return tmp.stat().st_size == f["size"] and sha256(tmp) == f["sha256"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ban", choices=BANS)
    ap.add_argument("--kiem", action="store_true", help="chi kiem, khong tai")
    a = ap.parse_args()

    m = danh_muc(a.ban)
    need = [f for f in m["files"] if f["path"].startswith(a.ban + "/")]
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
        rev = m["sources"][f["repo"]]["revision"]
        hf_url = f"https://huggingface.co/{f['repo']}/resolve/{rev}/{f['hf_path']}"
        nguon = [("GitHub Release", lambda: tai_tu_release(m, f, tmp)),
                 ("HuggingFace", lambda: curl(hf_url, tmp) and tmp.stat().st_size == f["size"]
                  and sha256(tmp) == f["sha256"])]
        for name, chay in nguon:
            if chay():
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
