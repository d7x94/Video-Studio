#!/usr/bin/env python3
"""Kiem tra ky thuat mot video da render, xuat anh khung hinh cho QA.

Dung:  python3 check_output.py PROJECT/timeline.json VIDEO.mp4 [--frames DIR] [--srt FILE] [--chuan-am] [--dung-hinh GIAY]

Kiem tra:
  - co luong hinh H.264 va luong tieng
  - do phan giai dung khung doc (1080x1920) hoac ngang (1920x1080); --co-san: chi canh bao (video co san khong phong to)
  - thoi luong khop timeline (lech <= 0.5s)
  - tieng khong bi cam: muc am trung binh > -45 dB
  - do on tich hop (LUFS) va true peak: luon in ra; voi --chuan-am thi ngoai -15..-13 LUFS hoac dinh > -1 dBTP la loi
  - file .srt (neu co): so thu tu lien tuc, moc thoi gian tang dan, khong vuot thoi luong video
  - chu tieng Viet: .srt, scenes.json va build/*/index.html phai o dang NFC (dau dung san); con dau to hop
    roi (NFD) hay ky tu ma cu TCVN3 (vd "¸", "Æ" giua chu) la loi vi dau de lech hoac roi khoi chu khi render
  - hinh den: doan den gan hoan toan (blackdetect, do sang < 2%) dai tu 0,5 giay la loi (thuong la canh khong len hinh)
  - hinh dung yen: doan hinh gan nhu khong doi (freezedetect, -60 dB) dai tu --dung-hinh giay (mac dinh 4) la CANH BAO,
    khong phai loi: dung hinh co chu y truoc y chinh la hop le, canh chi co chu tinh cung vay; script chi chi ra canh nao
Doan hinh den hay dung yen duoc gan vao ma canh theo moc visual_start va visual_duration trong timeline.json.
Voi --frames: xuat 1 anh giua moi canh (de agent QA nhin) va 1 anh contact sheet.
Tra ma thoat 1 neu co loi.
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
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


def loudness(path):
    """Tra ve (LUFS tich hop, true peak dBTP) hoac (None, None) neu khong do duoc."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    tail = r.stderr.split("Summary:")[-1]
    i = re.search(r"\bI:\s+(-?[\d.]+) LUFS", tail)
    p = re.search(r"\bPeak:\s+(-?[\d.]+) dBFS", tail)
    return (float(i.group(1)) if i else None, float(p.group(1)) if p else None)


def scene_of(tl, t0, t1):
    """Ma cac canh co khung hinh giao voi doan [t0, t1]."""
    ids = [sc["id"] for sc in tl["scenes"]
           if min(t1, sc["visual_start"] + sc["visual_duration"]) - max(t0, sc["visual_start"]) > 0.05]
    return ", ".join(ids) if ids else "ngoai cac canh"


def quet_hinh(path, dung_min):
    """Tra ve (doan den [(bat dau, ket thuc)], doan dung yen [(bat dau, ket thuc)]) bang mot lan giai ma."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-an", "-vf",
                        f"blackdetect=d=0.5:pic_th=0.98:pix_th=0.02,freezedetect=n=-60dB:d={dung_min}",
                        "-f", "null", "-"], capture_output=True, text=True)
    den = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
    bat_dau = [float(x) for x in re.findall(r"freeze_start:\s*([\d.]+)", r.stderr)]
    ket = [float(x) for x in re.findall(r"freeze_end:\s*([\d.]+)", r.stderr)]
    dung = [(b, ket[i] if i < len(ket) else None) for i, b in enumerate(bat_dau)]   # None: dung den het video
    return den, dung


# Ky tu hay gap khi chu tieng Viet go bang ma cu TCVN3 (ABC) roi doc nhu Unicode
MA_CU = re.compile(r"[^\W\d_][¸¹µ¶·¨ª«¬\xad¯´½¾ÆÇË]+[^\W\d_]")   # chi giua hai chu cai: tranh 37°C, 5µg


def kiem_chu_viet(path, errors, notes):
    """Bao loi neu file con chu khong o dang NFC hoac nghi la ma cu. Tra ve so dong loi."""
    try:
        txt = Path(path).read_text(encoding="utf-8")
        if Path(path).suffix == ".json":   # chuoi \uXXXX trong JSON: giai ra truoc khi soat
            txt = json.dumps(json.loads(txt), ensure_ascii=False, indent=1)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        errors.append(f"Khong doc duoc {path} dang UTF-8: {e}")
        return 1
    bad = 0
    for n, line in enumerate(txt.splitlines(), 1):
        if unicodedata.normalize("NFC", line) != line:
            errors.append(f"{path}:{n} chu chua chuan NFC (dau to hop roi): {line.strip()[:60]!r}; "
                          + ("sua scenes.json ve NFC roi long tieng lai canh do" if Path(path).suffix == ".json"
                           else "chay lai inject.py (tu chuan hoa NFC)"))
            bad += 1
        elif MA_CU.search(line):
            errors.append(f"{path}:{n} nghi chu go bang ma cu TCVN3: {line.strip()[:60]!r}")
            bad += 1
        if bad >= 5:
            errors.append(f"{path}: dung sau 5 dong loi chu, con the con nua")
            break
    return bad


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
    ap.add_argument("--dung-hinh", type=float, default=4.0,
                    help="giay: doan hinh dung yen dai tu day tro len thi canh bao (mac dinh 4)")
    ap.add_argument("--co-san", action="store_true",
                    help="video co san (che do long tieng cho video quay san): do phan giai khac 1080x1920 / 1920x1080 chi canh bao, khong phai loi (khong phong to de khong them chi tiet gia)")
    ap.add_argument("--chuan-am", action="store_true", help="bat buoc -14 LUFS (+-1) va dinh <= -1 dBTP (sau chuan_am.sh)")
    a = ap.parse_args()

    tl = json.loads(Path(a.timeline).read_text(encoding="utf-8"))
    info = probe(a.video)
    errors, notes, warns, warns_khac = [], [], [], []

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
            msg = f"Do phan giai la {w}x{h}, can 1080x1920 hoac 1920x1080"
            if a.co_san:
                warns_khac.append(msg + " (video co san, giu nguyen do phan giai goc)")
            else:
                errors.append(msg)
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
        lufs, peak = loudness(a.video)
        notes.append(f"Do on tich hop: {lufs} LUFS, true peak: {peak} dBTP")
        if a.chuan_am and (lufs is None or peak is None or lufs < -15 or lufs > -13 or peak > -1):
            errors.append("Am luong chua chuan (can -14 LUFS +-1, dinh <= -1 dBTP): chay chuan_am.sh")

    if v:
        den, dung = quet_hinh(a.video, a.dung_hinh)
        for b0, b1 in den:
            errors.append(f"Hinh den {b0:.1f}s den {b1:.1f}s ({b1 - b0:.1f}s), canh {scene_of(tl, b0, b1)}: canh khong len hinh?")
        for f0, f1 in dung:
            f1 = dur if f1 is None else f1
            if f1 - f0 >= a.dung_hinh and not any(b0 <= f0 + 0.1 and b1 >= f1 - 0.1 for b0, b1 in den):
                warns.append(f"Hinh dung yen {f0:.1f}s den {f1:.1f}s ({f1 - f0:.1f}s), canh {scene_of(tl, f0, f1)}")
        notes.append(f"Hinh den: {len(den)} doan; hinh dung yen tu {a.dung_hinh:g}s: {len(dung)} doan")

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

    proj = Path(a.timeline).resolve().parent
    files = [Path(a.srt)] if a.srt else []
    files += [f for f in [proj / "scenes.json", *sorted(proj.glob("build/*/index.html"))] if f.exists()]
    loi_chu = sum(kiem_chu_viet(f, errors, notes) for f in files)
    notes.append(f"Chu tieng Viet (NFC, ma cu): {len(files)} file, {loi_chu} dong loi")

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
    for w in warns:
        print("[CANH BAO]", w, "(dung hinh co chu y thi bo qua)")
    for w in warns_khac:
        print("[CANH BAO]", w)
    for e in errors:
        print("[LOI] ", e)
    print("KET QUA:", "DAT" if not errors else f"{len(errors)} LOI")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
