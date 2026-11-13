#!/usr/bin/env bash
# Dang mo hinh giong doc len GitHub Release theo video-studio/assets/voice-models.json.
# Tai tung file tu HuggingFace dung revision da ghim, kiem kich thuoc va sha256, roi
# tao release (neu chua co) va tai len nhung file con thieu. Khong ghi de file da co.
# Chay trong GitHub Actions (workflow voice-models.yml), can GH_TOKEN co quyen contents:write.
# Dung:  bash tools/publish_voice_models.sh [THU_MUC_TAM]   (mac dinh: dist/voice-models)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/video-studio/assets/voice-models.json"
OUT="$(realpath -m "${1:-$ROOT/dist/voice-models}")"
mkdir -p "$OUT"

# 1. Tai va kiem tra
python3 - "$MANIFEST" "$OUT" <<'PY'
import hashlib, json, subprocess, sys
from pathlib import Path
m = json.load(open(sys.argv[1])); out = Path(sys.argv[2])
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def get(url, dest):
    subprocess.run(["curl", "-fsSL", "--retry", "3", "-o", str(dest), url], check=True)
for f in m["files"]:
    dest = out / f["asset"]
    if not (dest.exists() and dest.stat().st_size == f["size"] and sha(dest) == f["sha256"]):
        rev = m["sources"][f["repo"]]["revision"]
        get(f"https://huggingface.co/{f['repo']}/resolve/{rev}/{f['hf_path']}", dest)
    if dest.stat().st_size != f["size"] or sha(dest) != f["sha256"]:
        sys.exit(f"[LOI] {f['path']}: kich thuoc hoac sha256 khong khop danh muc")
    print(f"[OK] {f['asset']}")
# The mo hinh goc (giay phep, ghi cong) dung revision
for repo, s in m["sources"].items():
    get(f"https://huggingface.co/{repo}/resolve/{s['revision']}/README.md", out / f"README-{repo.split('/')[1]}.md")
(out / "SHA256SUMS").write_text("".join(f"{f['sha256']}  {f['asset']}\n" for f in m["files"]))
PY
cp "$ROOT/tools/LICENSE-Apache-2.0.txt" "$OUT/"

# 2. Dang release
TAG="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['release_tag'])" "$MANIFEST")"
if ! gh release view "$TAG" >/dev/null 2>&1; then
  NOTES="$(python3 - "$MANIFEST" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
print("Mo hinh giong doc cho skill video-studio, chep nguyen ban (khong sua) tu HuggingFace de tai nhanh va khong phu thuoc huggingface.co.\n")
for repo, s in m["sources"].items():
    print(f"- {repo} @ {s['revision']} ({m['license']})")
print("\nTen file: duong dan goc, \"/\" thay bang \"--\". Ma kiem tra trong SHA256SUMS, khop video-studio/assets/voice-models.json.")
print("Giay phep: LICENSE-Apache-2.0.txt. Ghi cong va thong tin goc: README-*.md (the mo hinh nguyen ban).")
print("Khong xoa hay tao lai release nay: tts.py tro thang vao ten tag.")
PY
)"
  gh release create "$TAG" --title "Mo hinh giong doc VieNeu ($TAG)" --notes "$NOTES" --latest=false
fi
HAVE="$(gh release view "$TAG" --json assets --jq '.assets[].name')"
for f in "$OUT"/*; do
  n="$(basename "$f")"
  if grep -qxF "$n" <<<"$HAVE"; then echo "[CO SAN] $n"; else gh release upload "$TAG" "$f"; echo "[TAI LEN] $n"; fi
done
echo "Xong: release $TAG"
