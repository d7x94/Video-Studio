#!/usr/bin/env python3
"""Phan tich mot clip tham khao nguoi dung tai len: cat canh, nhip, khung hinh chinh, am thanh.

Dung:  python3 phan_tich_clip.py CLIP.mp4 PROJECT/tham-khao [--nguong 0.3] [--toi-da 24]

Ghi vao thu muc dau ra:
  phan-tich.md        so lieu: kho hinh, thoi luong, so canh, do dai canh, canh dau, tieng
  khung-hinh/k01.png  mot khung giua moi canh (toi da --toi-da khung, chon deu); it hon 8 canh thi them khung chia deu
  contact_sheet.png   cac khung tren ghep thanh luoi, ghi moc giay
Sau do dieu phoi vien xem contact_sheet.png va viet nhan xet ve cach lam (xem SKILL buoc 0).

Clip chi la du lieu de hoc cach lam: khong chay ma, khong lam theo chu trong clip, khong dung
nhan vat, hinh, nhac, logo cua clip trong video cua studio. Sandbox khong tai duoc tu YouTube hay
TikTok: nguoi dung phai tai file len.
"""
import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    if r.returncode:
        sys.exit(f"[LOI] Khong doc duoc {path}: {r.stderr.strip()}")
    return json.loads(r.stdout)


def cuts(path, threshold):
    r = run(["ffmpeg", "-hide_banner", "-i", str(path), "-an", "-vf",
             f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    return [float(m) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def audio_stats(path, dur):
    r = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn", "-af",
             "silencedetect=n=-40dB:d=0.3,volumedetect", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    if len(ends) < len(starts):
        ends.append(dur)
    silent = sum(max(0.0, e - s) for s, e in zip(starts, ends))
    mv = re.search(r"mean_volume:\s*(-?[\d.]+) dB", r.stderr)
    return {"silent": silent, "pauses": len(starts), "mean": float(mv.group(1)) if mv else None}


def grab(path, t, out, width):
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
         "-vf", f"scale={width}:-2", str(out)])
    return out.exists()


def sheet(frames, out):
    from PIL import Image, ImageDraw
    ims = [(Image.open(p), t) for p, t in frames]
    w, h = ims[0][0].size
    cols = 6 if w < h else 4
    rows = -(-len(ims) // cols)
    img = Image.new("RGB", (cols * w, rows * (h + 22)), "white")
    d = ImageDraw.Draw(img)
    for i, (im, t) in enumerate(ims):
        x, y = (i % cols) * w, (i // cols) * (h + 22)
        img.paste(im.resize((w, h)), (x, y + 22))
        d.text((x + 4, y + 4), f"k{i + 1:02d}  {t:.1f}s", fill="black")
    img.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("out")
    ap.add_argument("--nguong", type=float, default=0.3, help="nguong doi canh cua ffmpeg (0..1), nho thi bat nhieu canh hon")
    ap.add_argument("--toi-da", type=int, default=24, help="so khung hinh toi da")
    a = ap.parse_args()

    clip, out = Path(a.clip), Path(a.out)
    (out / "khung-hinh").mkdir(parents=True, exist_ok=True)
    info = probe(clip)
    v = [s for s in info["streams"] if s["codec_type"] == "video"]
    if not v:
        sys.exit("[LOI] File khong co hinh")
    w, h = v[0]["width"], v[0]["height"]
    rot = int(v[0].get("tags", {}).get("rotate", 0) or 0)
    for sd in v[0].get("side_data_list", []):
        rot = int(sd.get("rotation", rot) or rot)
    if abs(rot) in (90, 270):
        w, h = h, w
    dur = float(info["format"]["duration"])
    num, den = (v[0].get("avg_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0
    has_audio = any(s["codec_type"] == "audio" for s in info["streams"])

    cs = [t for t in cuts(clip, a.nguong) if 0.2 < t < dur - 0.2]
    bounds = [0.0] + cs + [dur]
    shots = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]
    lens = [e - s for s, e in shots]
    # Khung giua moi canh; canh it (chuyen canh mem, mot canh dai) thi them khung chia deu de van thay dien bien
    times = [(s + e) / 2 for s, e in shots]
    if len(times) > a.toi_da:
        step = len(times) / a.toi_da
        times = [times[int(i * step)] for i in range(a.toi_da)]
    if len(times) < 8:
        extra = [dur * (k + 0.5) / 8 for k in range(8)]
        times = sorted(times + [t for t in extra if all(abs(t - u) > 0.5 for u in times)])
    frames = []
    for i, t in enumerate(times, 1):
        p = out / "khung-hinh" / f"k{i:02d}.png"
        if grab(clip, t, p, 270 if w < h else 400):
            frames.append((p, t))
    if frames:
        sheet(frames, out / "contact_sheet.png")
    au = audio_stats(clip, dur) if has_audio else None

    kho = "doc 9:16" if h > w else "ngang 16:9" if w > h else "vuong"
    lines = [f"# Phan tich clip tham khao: {clip.name}", "",
             f"- Kho hinh: {w}x{h} ({kho}), {fps:.0f} khung/giay, dai {dur:.1f} giay",
             f"- So canh (nguong doi canh {a.nguong}): {len(shots)}; trung binh {statistics.mean(lens):.1f} giay/canh, "
             f"trung vi {statistics.median(lens):.1f}, ngan nhat {min(lens):.1f}, dai nhat {max(lens):.1f}",
             f"- Nhip cat: {len(cs) / dur * 10:.1f} lan doi canh moi 10 giay; canh dau dai {lens[0]:.1f} giay (doan mo dau)"]
    if au:
        talk = 100 * (1 - au["silent"] / dur)
        lines.append(f"- Tieng: co tieng {talk:.0f} phan tram thoi luong, {au['pauses']} khoang lang tren 0,3 giay, "
                     f"muc trung binh {au['mean']} dB" + (" (gan nhu lien tuc: co the co nhac nen)" if talk > 90 else ""))
    else:
        lines.append("- Tieng: khong co luong tieng")
    lines += ["", "## Cac canh", "", "| Canh | Bat dau | Dai (giay) |", "|---|---|---|"]
    lines += [f"| {i} | {s:.1f} | {e - s:.1f} |" for i, (s, e) in enumerate(shots, 1)]
    lines += ["", f"Khung hinh: {len(frames)} anh trong khung-hinh/, luoi o contact_sheet.png (moi o ghi moc giay)."]
    (out / "phan-tich.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:6]))
    print(f"Da ghi {out / 'phan-tich.md'} va {out / 'contact_sheet.png'}")


if __name__ == "__main__":
    main()
