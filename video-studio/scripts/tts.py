#!/usr/bin/env python3
"""Long tieng tieng Viet bang VieNeu-TTS v3 Turbo (ONNX/CPU).

Dung:
  python3 tts.py --warmup                         # tai mo hinh, doc thu mot cau
  python3 tts.py --list-voices                    # liet ke giong co san
  python3 tts.py PROJECT/scenes.json PROJECT      # long tieng tung canh
  python3 tts.py PROJECT/scenes.json PROJECT --retime   # chi tinh lai moc (doi pause_before)

Dau ra trong PROJECT:
  audio/<scene_id>.wav   tieng doc tung canh (48 kHz)
  voiceover.wav          ghep ca bai (de nghe duyet)
  timeline.json          moc thoi gian tung canh, dung cho dung hinh va phu de

Mo hinh: danh muc assets/voice-models.json (ten file, kich thuoc, sha256).
Tai tu GitHub Release cua repo truoc, khong duoc thi tu HuggingFace dung revision
da ghim; file nao cung phai khop sha256 moi dung. Tai xong thi chay offline
(HF_HUB_OFFLINE=1), vieneu khong goi HuggingFace nua.

Vi sao co doan "va" ben duoi: onnxruntime >= 1.29 tu choi nap file .data ngoai
khi chung nam o thu muc blobs khac nhau trong bo nho dem HuggingFace (symlink).
Ta dat mo hinh vao thu muc thuong (~/studio/.tools/models) de tranh loi do.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

STUDIO_HOME = Path(os.environ.get("STUDIO_HOME", Path.home() / "studio"))
MODEL_ROOT = STUDIO_HOME / ".tools" / "models"
MANIFEST = json.loads((Path(__file__).resolve().parent.parent / "assets/voice-models.json")
                      .read_text(encoding="utf-8"))
DEFAULT_VOICE = "Mai Anh"

LEAD_IN = 0.4      # giay im lang dau video
SCENE_GAP = 0.35   # giay nghi giua hai canh
TAIL = 1.0         # giay giu hinh cuoi
PAUSE_MAX = 1.5    # tran cho "pause_before" cua mot canh
SPEED_MIN, SPEED_MAX = 0.85, 1.15   # ngoai khoang nay giong bi meo


def cpu_has_vnni() -> bool:
    try:
        flags = Path("/proc/cpuinfo").read_text()
    except OSError:
        return False
    return "avx512_vnni" in flags or "avx_vnni" in flags


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


def ensure_models(sub: str):
    """Tai cac file can cho ban `sub` (onnx_int8 hoac onnx_update) va bo giai ma."""
    vieneu_dir = MANIFEST["sources"]["pnnbao-ump/VieNeu-TTS-v3-Turbo"]["dir"]
    need = [f for f in MANIFEST["files"]
            if not f["path"].startswith(vieneu_dir + "/") or f["path"].startswith(f"{vieneu_dir}/{sub}/")]
    for f in need:
        dest = MODEL_ROOT / f["path"]
        if dest.exists() and dest.stat().st_size == f["size"]:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        rev = MANIFEST["sources"][f["repo"]]["revision"]
        urls = [("GitHub Release", MANIFEST["release_url"].format(tag=MANIFEST["release_tag"], asset=f["asset"])),
                ("HuggingFace", f"https://huggingface.co/{f['repo']}/resolve/{rev}/{f['hf_path']}")]
        for name, url in urls:
            if curl(url, tmp) and tmp.stat().st_size == f["size"] and sha256(tmp) == f["sha256"]:
                tmp.rename(dest)
                print(f"[OK] {f['path']} ({name})", file=sys.stderr)
                break
            tmp.unlink(missing_ok=True)
        else:
            sys.exit(f"[LOI] Khong tai duoc {f['path']} tu GitHub Release lan HuggingFace (hoac sai sha256).\n"
                     "Kiem tra mang toi github.com, hoac gui kem file thu am loi doc.")


def load_tts():
    from vieneu._v3_turbo_engine import onnx_runtime_lite as lite

    def _fetch(repo, files, subfolder):
        # Khong tai: moi file da co san nho ensure_models. Thieu nghia la vieneu doi danh sach file.
        d = MODEL_ROOT / repo.replace("/", "__") / (subfolder or "")
        missing = [fn for fn in files if not (d / fn).exists() and not fn.endswith(".json")]
        if missing:
            sys.exit(f"[LOI] vieneu doi hoi file chua co trong assets/voice-models.json: {repo} {missing}")
        return d

    lite.OnnxV3LiteEngine._fetch = staticmethod(_fetch)

    precision = "int8" if cpu_has_vnni() else "fp32"
    sub = "onnx_int8" if precision == "int8" else "onnx_update"
    ensure_models(sub)

    from vieneu import Vieneu
    return Vieneu(precision=precision, onnx_dir=str(MODEL_ROOT / "vieneu" / sub))


def wav_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def synth(tts, text, voice, out_path: Path, speed: float):
    import numpy as np
    import soundfile as sf
    audio = np.asarray(tts.infer(text, voice=voice), dtype=np.float32)
    if abs(speed - 1.0) < 1e-3:
        sf.write(out_path, audio, tts.sample_rate)
        return
    tmp = out_path.with_suffix(".raw.wav")
    sf.write(tmp, audio, tts.sample_rate)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-filter:a", f"atempo={speed}",
                    str(out_path)], check=True)
    tmp.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes", nargs="?")
    ap.add_argument("project", nargs="?")
    ap.add_argument("--voice", help="Ghi de giong trong scenes.json")
    ap.add_argument("--speed", type=float, help="0.85 den 1.15; ghi de scenes.json")
    ap.add_argument("--only", help="Chi long tieng lai cac canh nay, vd: s02,s05")
    ap.add_argument("--retime", action="store_true",
                    help="Khong doc lai canh da co file; chi tinh lai timeline va ban ghep (sau khi doi pause_before)")
    ap.add_argument("--warmup", action="store_true")
    ap.add_argument("--list-voices", action="store_true")
    a = ap.parse_args()

    tts = load_tts()

    if a.list_voices:
        for label, vid in tts.list_preset_voices():
            print(f"{vid}\t{label}")
        return
    if a.warmup:
        MODEL_ROOT.mkdir(parents=True, exist_ok=True)
        synth(tts, "Xin chào.", DEFAULT_VOICE, MODEL_ROOT / "warmup.wav", 1.0)
        return
    if not (a.scenes and a.project):
        ap.error("can scenes.json va thu muc du an")

    project = Path(a.project)
    data = json.loads(Path(a.scenes).read_text(encoding="utf-8"))
    voice = a.voice or data.get("voice") or DEFAULT_VOICE
    speed = a.speed or float(data.get("speed", 1.0))
    if not SPEED_MIN <= speed <= SPEED_MAX:
        sys.exit("speed phai trong khoang 0.85 den 1.15 de giong khong bi meo")
    only = set(a.only.split(",")) if a.only else (set() if a.retime else None)

    audio_dir = project / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Chi dao giong theo canh: "pause_before" (giay nghi truoc canh, thay khoang nghi mac dinh;
    # dung truoc cau dao y hay ket luan) va "speed" rieng cua canh (--speed ghi de tat ca).
    # Doi pause_before khong can doc lai; doi speed cua canh thi phai --only canh do.
    t = 0.0
    scenes_out = []
    for i, sc in enumerate(data["scenes"]):
        sid, text = sc["id"], sc["narration"].strip()
        gap = float(sc.get("pause_before", LEAD_IN if i == 0 else SCENE_GAP))
        if not 0 <= gap <= PAUSE_MAX:
            sys.exit(f"{sid}: pause_before phai trong khoang 0 den {PAUSE_MAX} giay")
        sc_speed = a.speed or float(sc.get("speed", speed))
        if not SPEED_MIN <= sc_speed <= SPEED_MAX:
            sys.exit(f"{sid}: speed phai trong khoang 0.85 den 1.15 de giong khong bi meo")
        t += gap
        wav = audio_dir / f"{sid}.wav"
        sc_voice = a.voice or sc.get("voice") or voice   # canh co the co giong rieng (ke chuyen)
        if only is None or sid in only or not wav.exists():
            synth(tts, text, sc_voice, wav, sc_speed)
            print(f"{sid}: {wav_duration(wav):.2f}s", flush=True)
        dur = wav_duration(wav)
        scenes_out.append({"id": sid, "start": round(t, 3), "duration": round(dur, 3),
                           "audio": f"audio/{sid}.wav", "narration": text, "voice": sc_voice,
                           "speed": sc_speed, "pause_before": gap})
        t += dur
    total = round(t + TAIL, 3)

    # Hinh: canh dau hien tu giay 0 (phu ca khoang LEAD_IN), moi canh keo den luc canh sau
    # bat dau, canh cuoi giu them TAIL. Tieng: "start"/"duration". Hinh: "visual_*".
    for i, sc in enumerate(scenes_out):
        sc["visual_start"] = 0.0 if i == 0 else sc["start"]
        end = scenes_out[i + 1]["start"] if i + 1 < len(scenes_out) else total
        sc["visual_duration"] = round(end - sc["visual_start"], 3)

    # "voices": moi giong da dung (canh co the co giong rieng), de ghi credits.md cho du
    voices = list(dict.fromkeys(sc["voice"] for sc in scenes_out))
    timeline = {"voice": voice, "voices": voices, "speed": speed, "lead_in": scenes_out[0]["pause_before"], "total": total,
                "scenes": scenes_out}
    (project / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2),
                                          encoding="utf-8")

    # Ban ghep de nghe duyet (khoang lang dung bang pause_before de khop moc timeline)
    # Canh co pause_before = 0 thi bo doan lang (aevalsrc d=0 cho luong rong).
    parts, inputs, chain = [], [], []
    for i, sc in enumerate(scenes_out):
        inputs += ["-i", str(project / sc["audio"])]
        if sc["pause_before"] > 0:
            parts.append(f"aevalsrc=0:d={sc['pause_before']}:s=48000[g{i}]")
            chain.append(f"[g{i}]")
        chain.append(f"[{i}:a]")
    fc = "".join(p + ";" for p in parts) + "".join(chain) + f"concat=n={len(chain)}:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[out]",
                    str(project / "voiceover.wav")], check=True)
    print(f"Tong thoi luong: {total:.1f}s, giong: {', '.join(voices)}")


if __name__ == "__main__":
    main()
