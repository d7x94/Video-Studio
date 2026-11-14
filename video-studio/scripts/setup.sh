#!/usr/bin/env bash
# Dung moi truong studio trong workspace. Chay lai an toan (bo qua buoc da xong).
# Dung:  bash setup.sh            (cai dat day du)
#        bash setup.sh --check    (chi kiem tra, khong cai)
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STUDIO_HOME="${STUDIO_HOME:-$HOME/studio}"
TOOLS="$STUDIO_HOME/.tools"
ENV_FILE="$STUDIO_HOME/studio.env"

# Phien ban da kiem chung cung nhau (2026-11-12). Doi pin thi chay lai buoc test dau cuoi.
HF_VER="0.9.38"
GSAP_VER="3.15.0"
FONT_VER="5.3.0"
VIENEU_VER="3.8.4"
ONNX_VER="1.29.0"
THREE_VER="0.184.0"

ok()   { echo "[OK]   $*"; }
warn() { echo "[CANH BAO] $*"; }
fail() { echo "[LOI]  $*"; exit 1; }

mkdir -p "$TOOLS"

# 1. Cong cu nen
command -v node >/dev/null   || fail "Thieu Node.js"
command -v ffmpeg >/dev/null || fail "Thieu ffmpeg"
command -v ffprobe >/dev/null || fail "Thieu ffprobe"
CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
[ -n "$CHROME" ] || fail "Khong tim thay Chrome/Chromium. HyperFrames can trinh duyet de render."
ok "node $(node -v), ffmpeg, Chrome tai $CHROME"

# 2. Mang: mo hinh giong doc tai tu GitHub Release cua repo, HuggingFace la du phong
VOICE_NET=0
MODELS_TAG="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['release_tag'])" "$SKILL_DIR/assets/voice-models.json")"
if curl -s -o /dev/null -m 15 -L -w "%{http_code}" "https://github.com/d7x94/video-studio/releases/download/$MODELS_TAG/SHA256SUMS" | grep -q "^2"; then
  VOICE_NET=1; ok "Tai duoc mo hinh giong doc tu GitHub Release ($MODELS_TAG)"
elif curl -s -o /dev/null -m 15 -w "%{http_code}" https://huggingface.co | grep -q "^[23]"; then
  VOICE_NET=1; warn "Khong tai duoc tu GitHub Release $MODELS_TAG; dung du phong huggingface.co"
else
  warn "Khong tai duoc mo hinh giong doc (GitHub Release va huggingface.co deu khong duoc)"
fi
# Nhan vat 3D (tuy chon): tai tu GitHub Release (cung ten mien github.com voi mo hinh giong); Drive cua tac gia chi du phong
if curl -s -o /dev/null -m 15 -w "%{http_code}" https://drive.usercontent.google.com | grep -q "^[2345]"; then
  ok "Truy cap duoc Google Drive (du phong tai nhan vat 3D)"
else
  warn "Khong truy cap duoc drive.usercontent.google.com: khong co nguon du phong cho nhan vat 3D (nguon chinh la github.com; video 2D van lam binh thuong)"
fi

if [ "${1:-}" = "--check" ]; then
  [ -f "$TOOLS/.voice_done" ] && ok "Giong doc VieNeu da tai" || warn "Chua co giong doc VieNeu"
  [ -f "$TOOLS/.ready" ] && [ -f "$TOOLS/.voice_done" ] && ok "Moi truong da san sang" || warn "Moi truong chua dung xong, chay: bash $0"
  exit 0
fi

# 3. Goi Node: HyperFrames, GSAP (cai cuc bo vi CDN bi chan), font Be Vietnam Pro
# .node_done ghi cac ban da ghim: doi pin o tren thi cai lai thay vi bo qua
NODE_PINS="hyperframes@$HF_VER gsap@$GSAP_VER be-vietnam-pro@$FONT_VER three@$THREE_VER"
if [ "$(cat "$TOOLS/.node_done" 2>/dev/null)" != "$NODE_PINS" ] || [ ! -d "$TOOLS/node_modules/three" ]; then
  [ -f "$TOOLS/package.json" ] || echo '{ "name": "studio-tools", "private": true }' > "$TOOLS/package.json"
  ( cd "$TOOLS" && npm i --no-audit --no-fund "hyperframes@$HF_VER" "gsap@$GSAP_VER" "@fontsource/be-vietnam-pro@$FONT_VER" "three@$THREE_VER" >/dev/null 2>&1 ) \
    || fail "npm install that bai"
  echo "$NODE_PINS" > "$TOOLS/.node_done"
fi
ok "hyperframes $HF_VER, gsap $GSAP_VER, be-vietnam-pro $FONT_VER, three $THREE_VER"

# 4. Giong doc VieNeu (ONNX/CPU, khong can PyTorch)
pyver() { python3 -c "import importlib.metadata as m; print(m.version('$1'))" 2>/dev/null || true; }
if [ "$(pyver vieneu)" != "$VIENEU_VER" ] || [ "$(pyver onnxruntime)" != "$ONNX_VER" ]; then
  pip install --break-system-packages -q "vieneu==$VIENEU_VER" "onnxruntime==$ONNX_VER" >/dev/null 2>&1 \
    || fail "pip install vieneu/onnxruntime that bai"
fi
ok "vieneu $(pyver vieneu), onnxruntime $(pyver onnxruntime)"

# 5. File moi truong cho cac script khac
cat > "$ENV_FILE" <<EOF
export STUDIO_HOME="$STUDIO_HOME"
export STUDIO_TOOLS="$TOOLS"
export STUDIO_SKILL="$SKILL_DIR"
export HYPERFRAMES_BROWSER_PATH="$CHROME"
export HYPERFRAMES_SKIP_SKILLS=1
export PATH="$TOOLS/node_modules/.bin:\$PATH"
EOF
ok "Ghi $ENV_FILE"

# 6. Tai san mo hinh giong doc va thu mot cau
if [ "$VOICE_NET" = 1 ]; then
  python3 "$SKILL_DIR/scripts/tts.py" --warmup || fail "Khoi dong VieNeu that bai"
  touch "$TOOLS/.voice_done"
  ok "Giong doc VieNeu san sang"
fi

touch "$TOOLS/.ready"
if [ -f "$TOOLS/.voice_done" ]; then
  echo "XONG. Cac script khac tu doc $ENV_FILE"
else
  warn "Chua tai duoc giong doc (khong toi duoc GitHub Release lan huggingface.co). Dung hinh van lam duoc; long tieng thi chua."
  echo "XONG MOT PHAN. Kiem tra mang toi github.com roi chay lai: bash $0"
fi
