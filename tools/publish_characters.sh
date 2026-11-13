#!/usr/bin/env bash
# Dang nhan vat 3D (Quaternius, CC0) len GitHub Release theo video-studio/assets/sim3d/characters.json.
# Tai tung file tu Google Drive cua tac gia, kiem kich thuoc va sha256, roi tao release
# (neu chua co) va tai len nhung file con thieu. Khong ghi de file da co.
# Chay trong GitHub Actions (workflow characters.yml), can GH_TOKEN co quyen contents:write.
# Dung:  bash tools/publish_characters.sh [THU_MUC_TAM]   (mac dinh: dist/characters)
#   BOOTSTRAP=1: cho phep nhan vat chua co sha256 trong danh muc (chi kiem kich thuoc). Chi dung
#   mot lan khi lap release dau tien; sau do ghi sha256 tu SHA256SUMS cua release vao danh muc.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CATALOG="$ROOT/video-studio/assets/sim3d/characters.json"
OUT="$(realpath -m "${1:-$ROOT/dist/characters}")"
mkdir -p "$OUT"

# 0. Release da co du file thi thoat som: khong dung toi Google Drive (hay het han muc), khong ghi de gi
TAG="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['release_tag'])" "$CATALOG")"
if gh release view "$TAG" >/dev/null 2>&1; then
  WANT="$(python3 -c "import json,sys; c=json.load(open(sys.argv[1])); print('\n'.join([n+'.gltf' for n in c['characters']]+[c['license_asset'],'SHA256SUMS']))" "$CATALOG")"
  HAVE="$(gh release view "$TAG" --json assets --jq '.assets[].name')"
  if [ -z "$(comm -23 <(sort <<<"$WANT") <(sort <<<"$HAVE"))" ]; then
    echo "Release $TAG da du file: khong lam gi."; exit 0
  fi
fi

# 1. Tai va kiem tra
python3 - "$CATALOG" "$OUT" <<'PY'
import hashlib, json, os, subprocess, sys
from pathlib import Path
c = json.load(open(sys.argv[1], encoding="utf-8")); out = Path(sys.argv[2])
bootstrap = os.environ.get("BOOTSTRAP") == "1"
URL = "https://drive.usercontent.google.com/download?id={id}&export=download"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def get(file_id, dest):
    subprocess.run(["curl", "-fsSL", "--retry", "3", "-m", "300", "-o", str(dest), URL.format(id=file_id)], check=True)
    # Drive tra trang HTML (ma 200) khi het han muc hoac can xac nhan: khong phai file that
    if dest.read_bytes()[:200].lstrip().lower().startswith((b"<!doctype html", b"<html")):
        sys.exit(f"[LOI] {dest.name}: Google Drive tra ve trang HTML thay vi file (het han muc tai?)")
sums = []
for name, ch in c["characters"].items():
    dest = out / f"{name}.gltf"
    want = ch.get("sha256")
    if not want and not bootstrap:
        sys.exit(f"[LOI] {name}: danh muc chua co sha256")
    if not (dest.exists() and dest.stat().st_size == ch["size"] and (not want or sha(dest) == want)):
        get(ch["id"], dest)
    got = sha(dest)
    if dest.stat().st_size != ch["size"] or (want and got != want):
        sys.exit(f"[LOI] {name}: kich thuoc hoac sha256 khong khop danh muc")
    json.loads(dest.read_text(encoding="utf-8"))  # .gltf la JSON; hong thi dung o day
    sums.append((got, dest.name))
    print(f"[OK] {dest.name} {got}")
lic = out / c["license_asset"]
want = c.get("license_sha256")
if not want and not bootstrap:
    sys.exit("[LOI] danh muc chua co license_sha256")
get(c["license_file_id"], lic)
got = sha(lic)
if want and got != want:
    sys.exit("[LOI] file giay phep khong khop sha256 trong danh muc")
sums.append((got, lic.name))
print(f"[OK] {lic.name} {got}\n----- noi dung giay phep -----\n{lic.read_text(encoding='utf-8', errors='replace')[:1500]}\n-----")
(out / "SHA256SUMS").write_text("".join(f"{h}  {n}\n" for h, n in sums))
PY

# 2. Dang release
if ! gh release view "$TAG" >/dev/null 2>&1; then
  NOTES="Nhan vat 3D cho skill video-studio: Quaternius, Ultimate Animated Character Pack (CC0 1.0), chep nguyen ban (khong sua) tu Google Drive cua tac gia de tai nhanh va khong phu thuoc han muc Drive.

Nguon: https://quaternius.com/packs/ultimatedanimatedcharacter.html
Giay phep: LICENSE_Quaternius.txt. Ma kiem tra trong SHA256SUMS, khop video-studio/assets/sim3d/characters.json.
Khong xoa hay tao lai release nay: get_characters.py tro thang vao ten tag."
  gh release create "$TAG" --title "Nhan vat 3D Quaternius ($TAG)" --notes "$NOTES" --latest=false --target main
fi
HAVE="$(gh release view "$TAG" --json assets --jq '.assets[].name')"
for f in "$OUT"/*; do
  n="$(basename "$f")"
  if grep -qxF "$n" <<<"$HAVE"; then echo "[CO SAN] $n"; else gh release upload "$TAG" "$f"; echo "[TAI LEN] $n"; fi
done
echo "Xong: release $TAG"
