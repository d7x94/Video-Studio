#!/usr/bin/env bash
# Dang mo hinh nhan dang giong noi bo sung (Whisper large-v3, FireRedASR2-AED int8 ONNX) len GitHub Release theo
# video-studio/assets/asr-models.json, hoac theo danh muc khac cung dinh dang (vd lid-models.json cho FireRedLID). Tai tung file tu HuggingFace dung revision da ghim, kiem kich thuoc va sha256,
# cat file lon hon 2 GiB thanh parts (split -b 1500M -d -a 2) va kiem sha256 tung phan, roi tao release (neu chua co)
# va tai len nhung file con thieu. Khong ghi de file da co.
# Chay trong GitHub Actions (workflow asr-models.yml), can GH_TOKEN co quyen contents:write.
# Dung:  bash tools/publish_asr_models.sh [THU_MUC_TAM] [DANH_MUC]
#        (mac dinh: dist/asr-models, video-studio/assets/asr-models.json)
# Danh muc co "release_title", "release_notes" thi dung cho release moi; khong co thi dung loi ghi cua bo ASR.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$(realpath -m "${2:-$ROOT/video-studio/assets/asr-models.json}")"
OUT="$(realpath -m "${1:-$ROOT/dist/asr-models}")"
mkdir -p "$OUT/work" "$OUT/assets"

# 1. Tai, kiem tra, cat parts
python3 - "$MANIFEST" "$OUT" <<'PY'
import hashlib, json, subprocess, sys
from pathlib import Path
m = json.load(open(sys.argv[1])); out = Path(sys.argv[2]); work = out / "work"; assets = out / "assets"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def get(url, dest):
    subprocess.run(["curl", "-fsSL", "--retry", "3", "-o", str(dest), url], check=True)
sums = []
for f in m["files"]:
    dest = work / f["asset"]
    if not (dest.exists() and dest.stat().st_size == f["size"] and sha(dest) == f["sha256"]):
        rev = m["sources"][f["repo"]]["revision"]
        get(f"https://huggingface.co/{f['repo']}/resolve/{rev}/{f['hf_path']}", dest)
    if dest.stat().st_size != f["size"] or sha(dest) != f["sha256"]:
        sys.exit(f"[LOI] {f['path']}: kich thuoc hoac sha256 khong khop danh muc")
    print(f"[OK] {f['asset']}")
    if f.get("parts"):
        prefix = work / (f["asset"] + ".part")
        subprocess.run(["split", "-b", "1500M", "-d", "-a", "2", str(dest), str(prefix)], check=True)
        for p in f["parts"]:
            src = work / p["asset"]
            if src.stat().st_size != p["size"] or sha(src) != p["sha256"]:
                sys.exit(f"[LOI] {p['asset']}: phan cat khong khop danh muc")
            src.rename(assets / p["asset"])
            sums.append(f"{p['sha256']}  {p['asset']}\n")
            print(f"[OK] {p['asset']} (phan cat)")
        dest.unlink()   # file day du lon hon 2 GiB, khong dang len release
    else:
        dest.rename(assets / f["asset"])
        sums.append(f"{f['sha256']}  {f['asset']}\n")
# The mo hinh goc (giay phep, ghi cong) dung revision
for repo, s in m["sources"].items():
    get(f"https://huggingface.co/{repo}/resolve/{s['revision']}/README.md", assets / f"README-{repo.split('/')[1]}.md")
(assets / "SHA256SUMS").write_text("".join(sums))
PY
for lic in $(python3 -c "import json,sys; print(' '.join(sorted({s['license_file'] for s in json.load(open(sys.argv[1]))['sources'].values()})))" "$MANIFEST"); do
  cp "$ROOT/video-studio/references/$lic" "$OUT/assets/"
done

# 2. Dang release
TAG="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['release_tag'])" "$MANIFEST")"
if ! gh release view "$TAG" >/dev/null 2>&1; then
  NOTES="$(python3 - "$MANIFEST" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
if m.get("release_notes"):
    print(m["release_notes"]); sys.exit()
print("Mo hinh nhan dang giong noi bo sung cho che do dich cua skill video-studio, chep nguyen ban (khong sua) tu HuggingFace de tai nhanh va khong phu thuoc huggingface.co.\n")
for repo, s in m["sources"].items():
    print(f"- {repo} @ {s['revision']} ({s['license']})")
print("\nTen file: ban (large-v3, firered2) va ten file goc, noi bang \"--\". model.bin cua large-v3 lon hon 2 GiB (gioi han moi file cua release) nen chia thanh .part00, .part01; scripts/lay_asr.py ghep lai va kiem sha256 file day du. Ma kiem tra trong SHA256SUMS, khop video-studio/assets/asr-models.json.")
print("Giay phep: LICENSE-whisper.txt (OpenAI Whisper, MIT), LICENSE-firered.txt (FireRedASR, Apache-2.0). Thong tin goc: README-*.md (the mo hinh nguyen ban).")
print("Khong xoa hay tao lai release nay: scripts/lay_asr.py tro thang vao ten tag.")
PY
)"
  TITLE="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('release_title') or '')" "$MANIFEST")"
  [ -n "$TITLE" ] || TITLE="Mo hinh ASR bo sung: Whisper large-v3, FireRedASR2 ($TAG)"
  gh release create "$TAG" --title "$TITLE" --notes "$NOTES" --latest=false
fi
HAVE="$(gh release view "$TAG" --json assets --jq '.assets[].name')"
for f in "$OUT"/assets/*; do
  n="$(basename "$f")"
  if grep -qxF "$n" <<<"$HAVE"; then echo "[CO SAN] $n"; else gh release upload "$TAG" "$f"; echo "[TAI LEN] $n"; fi
done
echo "Xong: release $TAG"
