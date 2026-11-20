#!/usr/bin/env bash
# Dung moi truong studio trong workspace. Chay lai an toan (bo qua buoc da xong).
# Dung:  bash setup.sh            (cai dat day du)
#        bash setup.sh --check    (chi kiem tra, khong cai)
#        bash setup.sh --dich     (cai dat day du, them faster-whisper va sherpa-onnx, opencc cho che do dich video:
#                                  chep loi bang Whisper, kiem cheo bang FireRedASR2 voi tieng Trung, tieng Anh)
#        bash setup.sh --firered  (giong --dich, giu lai cho tuong thich)
#        bash setup.sh --lid      (nhu --dich, them torch, kaldiio, kaldi_native_fbank cho FireRedLID, chep_loi_goc.py --lid)
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
OPENCV_VER="5.0.0.93"   # che do video co san (lam mo, kiem khung); kiem chung 2026-11-17
FWHISPER_VER="1.2.1"    # che do dich (setup.sh --dich): chep loi goc bang Whisper; kiem chung 2026-11-18
CT2_VER="4.9.0"         # ctranslate2: ban da do toc do Whisper (CHANGELOG 1.13.0)
SHERPA_VER="2.0.2"      # sherpa-onnx: chay FireRedASR2 (ONNX) cho chep_loi_firered.py; kiem chung 2026-11-19 (from_fire_red_asr, 2 loi CPU)
OPENCC_VER="1.4.2"      # opencc: doi phon the sang gian the khi so Whisper voi FireRed (chep_loi_firered.py); kiem chung 2026-11-19 (t2s, Python 3.13)
TORCH_VER="2.15.0"      # torch cho FireRedLID (setup.sh --lid); ban pypi kem goi CUDA (khoang 4 GB) vi download.pytorch.org bi chan; kiem chung 2026-11-20 (CPU, Python 3.13)
KALDIIO_VER="2.18.1"    # kaldiio: doc cmvn.ark cua FireRedLID; kiem chung 2026-11-20
KNF_VER="1.23.3"        # kaldi_native_fbank: dac trung fbank cua FireRedLID; kiem chung 2026-11-20
AV_VER="17.0.0"         # PyAV: ban moi nhat (19.0.2) lam faster_whisper.decode_audio loi metadata_errors; 15.1.0, 16.1.0, 17.0.0 chay duoc (thu 2026-11-18)

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
  FW="$(python3 -c "import importlib.metadata as m; print(m.version('faster-whisper'))" 2>/dev/null || true)"
  if [ "$FW" = "$FWHISPER_VER" ]; then ok "faster-whisper $FW (che do dich)"
  else warn "Chua co faster-whisper $FWHISPER_VER (chi can cho che do dich, chay: bash $0 --dich)"; fi
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

# 4b. OpenCV cho cac script lam mo va kiem khung (che do video co san); chap nhan ban opencv-python da co dung pin
cv_ver() { for p in opencv-python-headless opencv-python opencv-contrib-python-headless opencv-contrib-python; do v="$(pyver $p)"; [ -n "$v" ] && { echo "$v"; return; }; done; }
if [ "$(cv_ver)" != "$OPENCV_VER" ]; then
  pip install --break-system-packages -q "opencv-python-headless==$OPENCV_VER" >/dev/null 2>&1 \
    || fail "pip install opencv-python-headless that bai"
fi
ok "opencv $(cv_ver)"

# 4c. faster-whisper cho che do dich (khi --dich hoac --firered: chep_loi_firered.py can chep-goc.json cua Whisper);
#     mo hinh tai luc chay bang scripts/lay_whisper.py
if [ "${1:-}" = "--dich" ] || [ "${1:-}" = "--firered" ] || [ "${1:-}" = "--lid" ]; then
  if [ "$(pyver faster-whisper)" != "$FWHISPER_VER" ] || [ "$(pyver ctranslate2)" != "$CT2_VER" ] || [ "$(pyver av)" != "$AV_VER" ]; then
    PIPLOG="$(mktemp)"
    pip install --break-system-packages -q "faster-whisper==$FWHISPER_VER" "ctranslate2==$CT2_VER" "av==$AV_VER" >"$PIPLOG" 2>&1 \
      || { tail -n 15 "$PIPLOG"; rm -f "$PIPLOG"; fail "pip install faster-whisper that bai"; }
    rm -f "$PIPLOG"
  fi
  ok "faster-whisper $(pyver faster-whisper), ctranslate2 $(pyver ctranslate2), av $(pyver av) (che do dich)"
fi

# 4d. sherpa-onnx, opencc cho kiem cheo bang FireRedASR2 (chep_loi_firered.py, mac dinh voi tieng Trung, tieng Anh tu
#     1.21.0); cai cung --dich, --firered, --lid. Mo hinh tai luc chay bang scripts/lay_asr.py firered2
if [ "${1:-}" = "--dich" ] || [ "${1:-}" = "--firered" ] || [ "${1:-}" = "--lid" ]; then
  if [ "$(pyver sherpa-onnx)" != "$SHERPA_VER" ] || [ "$(pyver opencc)" != "$OPENCC_VER" ]; then
    PIPLOG="$(mktemp)"
    pip install --break-system-packages -q "sherpa-onnx==$SHERPA_VER" "opencc==$OPENCC_VER" >"$PIPLOG" 2>&1 \
      || { tail -n 15 "$PIPLOG"; rm -f "$PIPLOG"; fail "pip install sherpa-onnx, opencc that bai"; }
    rm -f "$PIPLOG"
  fi
  ok "sherpa-onnx $(pyver sherpa-onnx), opencc $(pyver opencc) (chep loi FireRedASR2)"
fi

# 4e. torch, kaldiio, kaldi_native_fbank cho FireRedLID (chi khi --lid); mo hinh tai luc chay bang scripts/lay_asr.py lid,
#     ma suy luan o scripts/vendor/fireredlid
if [ "${1:-}" = "--lid" ]; then
  if [ "$(pyver torch)" != "$TORCH_VER" ] || [ "$(pyver kaldiio)" != "$KALDIIO_VER" ] || [ "$(pyver kaldi_native_fbank)" != "$KNF_VER" ]; then
    PIPLOG="$(mktemp)"
    pip install --break-system-packages -q "torch==$TORCH_VER" "kaldiio==$KALDIIO_VER" "kaldi_native_fbank==$KNF_VER" >"$PIPLOG" 2>&1 \
      || { tail -n 15 "$PIPLOG"; rm -f "$PIPLOG"; fail "pip install torch, kaldiio, kaldi_native_fbank that bai"; }
    rm -f "$PIPLOG"
  fi
  ok "torch $(pyver torch), kaldiio $(pyver kaldiio), kaldi_native_fbank $(pyver kaldi_native_fbank) (FireRedLID)"
fi

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
# .voice_done ghi ban vieneu, onnxruntime va tag mo hinh da thu: khop thi bo qua (chay lai setup nhanh)
VOICE_PINS="vieneu@$VIENEU_VER onnxruntime@$ONNX_VER models@$MODELS_TAG"
if [ "$(cat "$TOOLS/.voice_done" 2>/dev/null)" = "$VOICE_PINS" ]; then
  ok "Giong doc VieNeu san sang (da thu truoc do)"
elif [ "$VOICE_NET" = 1 ]; then
  python3 "$SKILL_DIR/scripts/tts.py" --warmup || fail "Khoi dong VieNeu that bai"
  echo "$VOICE_PINS" > "$TOOLS/.voice_done"
  ok "Giong doc VieNeu san sang"
fi

touch "$TOOLS/.ready"
if [ "$(cat "$TOOLS/.voice_done" 2>/dev/null)" = "$VOICE_PINS" ]; then
  echo "XONG. Cac script khac tu doc $ENV_FILE"
else
  warn "Chua tai duoc giong doc (khong toi duoc GitHub Release lan huggingface.co). Dung hinh van lam duoc; long tieng thi chua."
  echo "XONG MOT PHAN. Kiem tra mang toi github.com roi chay lai: bash $0"
fi
