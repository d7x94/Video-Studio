#!/usr/bin/env python3
"""Kiem tra ky thuat mot video da render, xuat anh khung hinh cho QA.

Dung:  python3 check_output.py PROJECT/timeline.json VIDEO.mp4 [--frames DIR] [--srt FILE]

Kiem tra:
  - co luong hinh H.264 va luong tieng
  - do phan giai dung khung doc (1080x1920) hoac ngang (1920x1080)
  - thoi luong khop timeline (lech <= 0.5s)
  - tieng khong bi cam: muc am trung binh > -45 dB
  - file .srt (neu co): so thu tu lien tuc, moc thoi gian tang dan, khong vuot thoi luong video
Voi --frames: xuat 1 anh giua moi canh (de agent QA nhin) va 1 anh contact sheet.
Tra ma thoat 1 neu co loi.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def mean_volume(path):
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-af", "volumedetect", "-vn", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", r.stderr)
    return float(m.group(1)) if m else None


def parse_srt_time(s):
    h, m, rest = s.split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("video")
    ap.add_argument("--frames")
    ap.add_argument("--srt")
    a = ap.parse_args()

    tl = json.loads(Path(a.timeline).read_text(encoding="utf-8"))
    info = probe(a.video)
    errors, notes = [], []

    v = [s for s in info["streams"] if s["codec_type"] == "video"]
    au = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if not v:
        errors.append("Khong co luong hinh")
    else:
        w, h = v[0]["width"], v[0]["height"]
        notes.append(f"Hinh: {v[0]['codec_name']} {w}x{h}")
        if v[0]["codec_name"] != "h264":
            errors.append(f"Codec hinh la {v[0]['codec_name']}, can h264")
        if (w, h) not in [(1080, 1920), (1920, 1080)]:
            errors.append(f"Do phan giai la {w}x{h}, can 1080x1920 hoac 1920x1080")
    if not au:
        errors.append("Khong co luong tieng")

    dur = float(info["format"]["duration"])
    notes.append(f"Thoi luong: {dur:.2f}s (timeline {tl['total']:.2f}s)")
    if abs(dur - tl["total"]) > 0.5:
        errors.append(f"Thoi luong lech timeline {dur - tl['total']:+.2f}s")

    if au:
        mv = mean_volume(a.video)
        notes.append(f"Muc am trung binh: {mv} dB")
        if mv is None or mv < -45:
            errors.append("Tieng qua nho hoac cam")

    if a.srt:
        txt = Path(a.srt).read_text(encoding="utf-8").strip()
        blocks = [b.splitlines() for b in re.split(r"\n\s*\n", txt) if b.strip()]
        prev_end = 0.0
        for i, b in enumerate(blocks, 1):
            if len(b) < 3 or b[0].strip() != str(i) or "-->" not in b[1]:
                errors.append(f"SRT khoi {i} sai dinh dang")
                break
            s, e = [parse_srt_time(x.strip()) for x in b[1].split("-->")]
            if s < prev_end - 0.001 or e <= s:
                errors.append(f"SRT khoi {i} moc thoi gian khong tang dan")
            prev_end = e
        if prev_end > dur + 0.05:
            errors.append(f"SRT ket thuc ({prev_end:.2f}s) sau khi video het")
        notes.append(f"SRT: {len(blocks)} dong")

    if a.frames:
        fd = Path(a.frames)
        fd.mkdir(parents=True, exist_ok=True)
        shots = []
        for sc in tl["scenes"]:
            t = sc["visual_start"] + min(sc["visual_duration"] * 0.6, sc["visual_duration"] - 0.2)
            out = fd / f"{sc['id']}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", a.video, "-frames:v", "1", str(out)],
                           check=True)
            shots.append(str(out))
        cols = 4 if v and v[0]["width"] < v[0]["height"] else 3
        inputs = sum([["-i", s] for s in shots], [])
        scale = "scale=360:-1" if cols == 4 else "scale=480:-1"
        pads = "".join(f"[{i}:v]{scale}[f{i}];" for i in range(len(shots)))
        # xstack layout "x_y": cot thu k nam o w0+w0+..., hang thu r o h0+h0+...
        layout = "|".join(("0" if i % cols == 0 else "+".join(["w0"] * (i % cols))) + "_" +
                          ("0" if i // cols == 0 else "+".join(["h0"] * (i // cols))) for i in range(len(shots)))
        chain = "".join(f"[f{i}]" for i in range(len(shots)))
        if len(shots) == 1:
            fc = pads + "[f0]null[out]"
        else:
            fc = pads + f"{chain}xstack=inputs={len(shots)}:layout={layout}:fill=black[out]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[out]",
                        "-frames:v", "1", str(fd / "contact_sheet.png")], check=True)
        notes.append(f"Anh khung hinh: {fd} ({len(shots)} canh + contact_sheet.png)")

    for n in notes:
        print("[INFO]", n)
    for e in errors:
        print("[LOI] ", e)
    print("KET QUA:", "DAT" if not errors else f"{len(errors)} LOI")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
