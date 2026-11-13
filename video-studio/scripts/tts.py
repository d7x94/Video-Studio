#!/usr/bin/env python3
"""Long tieng tieng Viet bang VieNeu-TTS v3 Turbo (ONNX/CPU).

Dung:
  python3 tts.py --warmup                         # tai mo hinh, doc thu mot cau
  python3 tts.py --list-voices                    # liet ke giong co san
  python3 tts.py PROJECT/scenes.json PROJECT      # long tieng tung canh

Dau ra trong PROJECT:
  audio/<scene_id>.wav   tieng doc tung canh (48 kHz)
  voiceover.wav          ghep ca bai (de nghe duyet)
  timeline.json          moc thoi gian tung canh, dung cho dung hinh va phu de

Vi sao co doan "va" ben duoi: onnxruntime >= 1.29 tu choi nap file .data ngoai
khi chung nam o thu muc blobs khac nhau trong bo nho dem HuggingFace (symlink).
Ta tai mo hinh vao thu muc thuong (local_dir) de tranh loi do.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

STUDIO_HOME = Path(os.environ.get("STUDIO_HOME", Path.home() / "studio"))
MODEL_ROOT = STUDIO_HOME / ".tools" / "models"
REPO = "pnnbao-ump/VieNeu-TTS-v3-Turbo"
DEFAULT_VOICE = "Mai Anh"

LEAD_IN = 0.4      # giay im lang dau video
SCENE_GAP = 0.35   # giay nghi giua hai canh
TAIL = 1.0         # giay giu hinh cuoi


def cpu_has_vnni() -> bool:
    try:
        flags = Path("/proc/cpuinfo").read_text()
    except OSError:
        return False
    return "avx512_vnni" in flags or "avx_vnni" in flags


def load_tts():
    from huggingface_hub import hf_hub_download, snapshot_download
    from vieneu._v3_turbo_engine import onnx_runtime_lite as lite

    def _fetch(repo, files, subfolder):
        dest = MODEL_ROOT / repo.replace("/", "__")
        last = None
        for fn in files:
            try:
                last = hf_hub_download(repo, fn, subfolder=subfolder or None, local_dir=dest)
            except Exception:
                if fn.endswith(".json"):
                    continue
                raise
        return Path(last).parent

    lite.OnnxV3LiteEngine._fetch = staticmethod(_fetch)

    precision = "int8" if cpu_has_vnni() else "fp32"
    sub = "onnx_int8" if precision == "int8" else "onnx_update"
    local = MODEL_ROOT / "vieneu"
    if not (local / sub / "config.json").exists():
        snapshot_download(REPO, allow_patterns=[f"{sub}/*"], local_dir=local)

    from vieneu import Vieneu
    return Vieneu(precision=precision, onnx_dir=str(local / sub))


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
    if not 0.85 <= speed <= 1.15:
        sys.exit("speed phai trong khoang 0.85 den 1.15 de giong khong bi meo")
    only = set(a.only.split(",")) if a.only else None

    audio_dir = project / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    t = LEAD_IN
    scenes_out = []
    for sc in data["scenes"]:
        sid, text = sc["id"], sc["narration"].strip()
        wav = audio_dir / f"{sid}.wav"
        sc_voice = a.voice or sc.get("voice") or voice   # canh co the co giong rieng (ke chuyen)
        if only is None or sid in only or not wav.exists():
            synth(tts, text, sc_voice, wav, speed)
            print(f"{sid}: {wav_duration(wav):.2f}s", flush=True)
        dur = wav_duration(wav)
        scenes_out.append({"id": sid, "start": round(t, 3), "duration": round(dur, 3),
                           "audio": f"audio/{sid}.wav", "narration": text, "voice": sc_voice})
        t += dur + SCENE_GAP
    total = round(t - SCENE_GAP + TAIL, 3)

    # Hinh: canh dau hien tu giay 0 (phu ca khoang LEAD_IN), moi canh keo den luc canh sau
    # bat dau, canh cuoi giu them TAIL. Tieng: "start"/"duration". Hinh: "visual_*".
    for i, sc in enumerate(scenes_out):
        sc["visual_start"] = 0.0 if i == 0 else sc["start"]
        end = scenes_out[i + 1]["start"] if i + 1 < len(scenes_out) else total
        sc["visual_duration"] = round(end - sc["visual_start"], 3)

    # "voices": moi giong da dung (canh co the co giong rieng), de ghi credits.md cho du
    voices = list(dict.fromkeys(sc["voice"] for sc in scenes_out))
    timeline = {"voice": voice, "voices": voices, "speed": speed, "lead_in": LEAD_IN, "total": total,
                "scenes": scenes_out}
    (project / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2),
                                          encoding="utf-8")

    # Ban ghep de nghe duyet
    parts = []
    for i, sc in enumerate(scenes_out):
        gap = LEAD_IN if i == 0 else SCENE_GAP
        parts.append(f"aevalsrc=0:d={gap}:s=48000[g{i}]")
    inputs, chain = [], []
    for i, sc in enumerate(scenes_out):
        inputs += ["-i", str(project / sc["audio"])]
        chain.append(f"[g{i}][{i}:a]")
    fc = ";".join(parts) + ";" + "".join(chain) + f"concat=n={2 * len(scenes_out)}:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[out]",
                    str(project / "voiceover.wav")], check=True)
    print(f"Tong thoi luong: {total:.1f}s, giong: {', '.join(voices)}")


if __name__ == "__main__":
    main()
