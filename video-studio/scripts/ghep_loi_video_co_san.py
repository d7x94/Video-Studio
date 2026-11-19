#!/usr/bin/env python3
"""Ghep loi doc (tts.py) vao mot video co san, dung theo moc thoi gian cua video do.

Dung:
  python3 ghep_loi_video_co_san.py PROJECT CAU_HINH.json [--ra PROJECT/output/video.mp4]

PROJECT co scenes.json va audio/<id>.wav (chay: python3 tts.py PROJECT/scenes.json PROJECT).
tts.py ghep loi lien tuc nen khong khop hinh co san; script nay dat tung loi vao dung giay.

CAU_HINH.json:
{
  "video": "video_nomau.mp4",             # hinh (da lam mo neu can), duong dan tuong doi PROJECT
  "cue": {"s01": 0.3, "s02": 4.3},        # giay bat dau loi tren video GOC (cac canh khong nam trong giu_hinh); script tu cong phan keo dai
                                          # cua cac lan giu hinh nam truoc cue do (dong_bang <= cue) de loi van khop hinh
  "giu_hinh": [                           # tuy chon: keo dai anh tinh bang cach giu khung hinh
    {"id": "s11", "dong_bang": 78.64, "hien_ro": 76.13}
  ],
  "khoang_truoc": 0.15, "khoang_sau": 0.35  # tuy chon, giay
}
Voi moi muc giu_hinh (theo thu tu thoi gian): loi bat dau sau luc anh hien ro "hien_ro" mot
khoang_truoc; neu loi doc dai hon thoi gian anh nam yen thi khung hinh o "dong_bang" (giay
tren video goc, ngay truoc luc chuyen sang anh ke tiep) duoc nhan ra du lau de loi doc xong
cach luc chuyen anh khoang_sau. Cac moc sau do (ca giu_hinh lan cue) tu dich theo. Dung freezedetect hoac so sanh
khung hinh de tim moc, khong doan.

Ra: video mp4 (hinh libx264 crf 17, tieng AAC 192k), PROJECT/timeline_ghep.json va
PROJECT/phu-de.srt (lay truong "subtitle" cua canh, khong co thi "narration").
Gioi han: video co dinh khung hinh/giay; tieng 48 kHz (dung tts.py); khong phat hien loi chong lan
ngoai viec in canh bao. Loi doc ket thuc sau cuoi video (sau khi giu hinh) thi dung va bao [LOI] ghi ro so giay vuot,
khong cat loi: rut loi, doi cue som hon hoac them giu_hinh.
Yeu cau: ffmpeg, ffprobe, python3 co numpy va soundfile.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000


def probe(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate", "-of", "json", path])
    s = json.loads(out)["streams"][0]
    a, b = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(a) / float(b)


def srt_time(x):
    h = int(x // 3600)
    m = int(x % 3600 // 60)
    s = x % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def kiem_het_video(start, dur, total, dung_sai):
    """Dung neu co loi ket thuc sau cuoi video (mix tieng khong the dai hon hinh)."""
    qua = [(k, start[k] + dur[k] - total) for k in start if start[k] + dur[k] - total > dung_sai]
    if qua:
        ct = ", ".join(f"{k} vuot {v:.2f}s" for k, v in sorted(qua, key=lambda x: -x[1])[:4])
        sys.exit(f"[LOI] loi doc ket thuc sau cuoi video ({total:.2f}s): {ct}. Rut loi, doi cue som hon hoac them giu_hinh")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("cau_hinh")
    ap.add_argument("--ra")
    a = ap.parse_args()

    proj = Path(a.project)
    cfg = json.loads(Path(a.cau_hinh).read_text(encoding="utf-8"))
    scenes = {s["id"]: s for s in json.loads((proj / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    video = str(proj / cfg["video"])
    w, h, fps = probe(video)
    gap_truoc = cfg.get("khoang_truoc", 0.15)
    gap_sau = cfg.get("khoang_sau", 0.35)

    dur = {}
    for sid in scenes:
        wav = proj / "audio" / f"{sid}.wav"
        if not wav.exists():
            sys.exit(f"[LOI] thieu {wav}: chay tts.py truoc")
        x, sr = sf.read(str(wav))
        if sr != SR:
            sys.exit(f"[LOI] {wav} la {sr} Hz, can {SR} Hz")
        dur[sid] = len(x) / sr

    cue_goc = {k: float(v) for k, v in cfg.get("cue", {}).items()}   # moc tren video goc
    start = dict(cue_goc)
    freeze = []   # (so khung hinh goc, so khung hinh them)
    moc_giu = []  # (dong_bang tren video goc, giay them) de dich cac cue nam sau
    shift = 0.0
    for g in cfg.get("giu_hinh", []):
        sid = g["id"]
        vis = g["hien_ro"] + shift
        s = vis + gap_truoc
        start[sid] = s
        need = s + dur[sid] + gap_sau
        cur = g["dong_bang"] + shift
        ext = max(0.0, need - cur)
        freeze.append((int(round(g["dong_bang"] * fps)), int(round(ext * fps))))
        moc_giu.append((float(g["dong_bang"]), int(round(ext * fps)) / fps))
        shift += ext
    # cue tinh tren video goc: cong phan keo dai cua cac lan giu hinh da xay ra truoc moc do
    for sid, c in cue_goc.items():
        start[sid] = c + sum(e for db, e in moc_giu if db <= c)
    thieu = [k for k in scenes if k not in start]
    if thieu:
        sys.exit(f"[LOI] canh chua co moc thoi gian: {', '.join(thieu)}")

    # loi khong duoc vuot cuoi video: chan som (uoc theo thoi luong video) truoc khi ma hoa lau
    dv = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", video],
                        capture_output=True, text=True).stdout.strip()
    try:
        uoc = float(dv) + sum(e for _, e in moc_giu)
    except ValueError:
        uoc = None
    if uoc is not None:
        kiem_het_video(start, dur, uoc, 0.1)

    # video: nhan khung hinh o cac moc dong bang
    tmp_video = proj / "video_giu_hinh.mp4"
    fz = dict(freeze)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-an", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         stdout=subprocess.PIPE)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", str(tmp_video)],
        stdin=subprocess.PIPE)
    n = 0
    i = 0
    while True:
        b = p.stdout.read(w * h * 3)
        if len(b) < w * h * 3:
            break
        enc.stdin.write(b)
        n += 1
        for _ in range(fz.get(i, 0)):
            enc.stdin.write(b)
            n += 1
        i += 1
    enc.stdin.close()
    enc.wait()
    p.wait()
    total = n / fps
    kiem_het_video(start, dur, total, 0.0)

    # tieng
    mix = np.zeros(int((total + 1) * SR), np.float32)
    for sid, s in start.items():
        x, _ = sf.read(str(proj / "audio" / f"{sid}.wav"))
        if x.ndim > 1:
            x = x.mean(1)
        k = int(s * SR)
        mix[k:k + len(x)] += x.astype(np.float32)
    wav_out = proj / "loi_doc_ghep.wav"
    sf.write(str(wav_out), mix[:int(total * SR)], SR)

    ra = Path(a.ra) if a.ra else proj / "output" / "video.mp4"
    ra.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", str(tmp_video), "-i", str(wav_out),
                           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(ra)])

    order = sorted(start.items(), key=lambda kv: kv[1])
    for (k1, s1), (k2, s2) in zip(order, order[1:]):
        if s1 + dur[k1] > s2:
            print(f"[CANH BAO] loi {k1} (den {s1 + dur[k1]:.2f}s) chong len loi {k2} (bat dau {s2:.2f}s)", file=sys.stderr)
    rows = []
    for idx, (k, s) in enumerate(order, 1):
        sc = scenes[k]
        rows.append(f"{idx}\n{srt_time(s)} --> {srt_time(s + dur[k])}\n{sc.get('subtitle') or sc['narration']}\n")
    (proj / "phu-de.srt").write_text("\n".join(rows), encoding="utf-8")
    (proj / "timeline_ghep.json").write_text(
        json.dumps({"start": start, "giu_hinh": freeze, "dur": dur, "tong_giay": total}, indent=1), encoding="utf-8")
    print(f"[OK] {ra}: {total:.1f} giay, {len(start)} canh")


if __name__ == "__main__":
    main()
