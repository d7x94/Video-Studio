#!/usr/bin/env python3
"""Phan tich dau vao cho video co san bang mot lenh: thong so, tieng goc, anh tinh, bang khung moi giay, khung phong to.

Dung:
  python3 phan_tich_dau_vao.py VIDEO PROJECT [--nguong-dong-bang -50] [--dong-bang-min 0.5] [--zoom 12.5,40] [--toi-da-anh 30]

Ra PROJECT/phan-tich/:
  phan-tich.md        thong so (kho hinh, fps, thoi luong), tieng goc (co hay khong, muc am), bang anh tinh
                      (freezedetect: bat dau, ket thuc, keo dai), cac moc doi canh
  bang-NN.png         bang khung 1 khung moi giay, ghi giay len tung o (24 o moi bang)
  anh-tinh/NN_<giay>.png    khung do phan giai goc o giua moi doan anh tinh (de doc chu tren hinh)
  zoom/<giay>.png     khung do phan giai goc o cac moc --zoom (chu tren nhan, bao bi, phieu)
va tao PROJECT/job.json mau (neu chua co) voi video_goc, thong so, tieng_goc, anh_tinh da dien san: xem job.py.
Chu tren nhan, bao bi doc tu khung phong to, khong doc tu bang khung (SKILL.md, che do video co san). Script khong
nhan dang chu: viec doc chu la cua nguoi xem anh. Moc anh tinh do bang freezedetect, khong doan: --nguong-dong-bang
(dB, mac dinh -50) va --dong-bang-min (giay, mac dinh 0,5) theo lenh trong SKILL.md.
Yeu cau: ffmpeg, ffprobe, python3 co numpy va opencv-python.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    if r.returncode:
        sys.exit(f"[LOI] khong doc duoc {path}: {r.stderr.strip()}")
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    if not v:
        sys.exit("[LOI] file khong co hinh")
    au = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    a, b = v["r_frame_rate"].split("/")
    dur = float(v.get("duration") or j["format"]["duration"])
    return {"w": int(v["width"]), "h": int(v["height"]), "fps": float(a) / float(b), "dur": dur,
            "codec": v["codec_name"], "audio": au}


def freeze(path, nguong, dmin, dur):
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-map", "0:v:0", "-an", "-vf",
             f"freezedetect=n={nguong}dB:d={dmin}", "-f", "null", "-"])
    st = [float(x) for x in re.findall(r"freeze_start: (-?[\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"freeze_end: (-?[\d.]+)", r.stderr)]
    out = []
    for i, s in enumerate(st):
        e = en[i] if i < len(en) else dur
        out.append({"tu": round(max(0.0, s), 2), "den": round(e, 2)})
    return out


def doi_canh(path, nguong=0.3):
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-an", "-vf", f"select='gt(scene,{nguong})',showinfo",
             "-f", "null", "-"])
    return [round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def tieng(path, au):
    if not au:
        return {"co": False}
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"])
    mean = re.search(r"mean_volume:\s*(-?[\d.]+) dB", r.stderr)
    mx = re.search(r"max_volume:\s*(-?[\d.]+) dB", r.stderr)
    return {"co": True, "mean_db": float(mean.group(1)) if mean else None, "max_db": float(mx.group(1)) if mx else None}


def khung_goc(path, t, out):
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", str(out)])
    return out.exists()


def bang_khung(path, info, outdir, cot, hang, rong):
    h2 = int(round(info["h"] * rong / info["w"] / 2) * 2)
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-an", "-vf", f"fps=1,scale={rong}:{h2}", "-f", "rawvideo",
           "-pix_fmt", "bgr24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    ds, o = [], []
    n = 0
    try:
        while True:
            b = p.stdout.read(rong * h2 * 3)
            if len(b) < rong * h2 * 3:
                break
            fr = np.frombuffer(b, np.uint8).reshape(h2, rong, 3).copy()
            cv2.rectangle(fr, (0, 0), (74, 18), (255, 255, 255), -1)
            cv2.putText(fr, f"{n}s", (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            o.append(fr)
            n += 1
    finally:
        p.kill()
        p.wait()
    moi = cot * hang
    for k in range(0, len(o), moi):
        blk = o[k:k + moi]
        while len(blk) % cot:
            blk.append(np.full_like(blk[0], 255))
        rows = [np.hstack(blk[i:i + cot]) for i in range(0, len(blk), cot)]
        pth = outdir / f"bang-{k // moi + 1:02d}.png"
        cv2.imwrite(str(pth), np.vstack(rows))
        ds.append(pth.name)
    return ds, n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("project")
    ap.add_argument("--nguong-dong-bang", type=float, default=-50)
    ap.add_argument("--dong-bang-min", type=float, default=0.5)
    ap.add_argument("--zoom", default="", help="cac moc giay can khung phong to, cach nhau dau phay")
    ap.add_argument("--toi-da-anh", type=int, default=30)
    a = ap.parse_args()

    video = Path(a.video).resolve()
    proj = Path(a.project)
    out = proj / "phan-tich"
    for d in ("anh-tinh", "zoom"):
        (out / d).mkdir(parents=True, exist_ok=True)

    info = probe(str(video))
    fz = freeze(str(video), a.nguong_dong_bang, a.dong_bang_min, info["dur"])
    cuts = doi_canh(str(video))
    am = tieng(str(video), info["audio"])
    cot = 6 if info["w"] < info["h"] else 4
    bang, so_giay = bang_khung(str(video), info, out, cot, 4, 180 if info["w"] < info["h"] else 240)

    anh = []
    for i, f in enumerate(fz[:a.toi_da_anh], 1):
        t = (f["tu"] + f["den"]) / 2
        p = out / "anh-tinh" / f"{i:02d}_{t:.1f}.png"
        if khung_goc(str(video), t, p):
            anh.append(p.name)
    zs = []
    for tok in [x for x in a.zoom.split(",") if x.strip()]:
        t = float(tok)
        p = out / "zoom" / f"{t:.1f}.png"
        if khung_goc(str(video), t, p):
            zs.append(p.name)

    L = ["# Phan tich dau vao", "",
         f"- Tep: {video.name}",
         f"- Kho hinh: {info['w']}x{info['h']}, {info['fps']:.3f} khung/giay, {info['dur']:.2f} giay, codec {info['codec']}"]
    if am["co"]:
        L.append(f"- Tieng goc: co (muc trung binh {am['mean_db']} dB, cao nhat {am['max_db']} dB): "
                 "nghe hoac hoi nguoi dung giu hay thay")
    else:
        L.append("- Tieng goc: khong co luong tieng")
    L += ["", f"## Anh tinh (freezedetect n={a.nguong_dong_bang:g}dB, d>={a.dong_bang_min:g}s)", "",
          "| # | Tu (giay) | Den (giay) | Keo dai |", "|---|---|---|---|"]
    for i, f in enumerate(fz, 1):
        L.append(f"| {i} | {f['tu']} | {f['den']} | {f['den'] - f['tu']:.2f} |")
    if not fz:
        L.append("| - | khong co | | |")
    L += ["", f"## Moc doi canh (scene > 0,3): {', '.join(str(c) for c in cuts) if cuts else 'khong co'}", "",
          "## Tep ra", "",
          f"- Bang khung ({so_giay} giay): {', '.join(bang)}",
          f"- Khung do phan giai goc giua cac anh tinh: phan-tich/anh-tinh/ ({len(anh)} khung)",
          f"- Khung phong to: phan-tich/zoom/ ({len(zs)} khung)", "",
          "Doc chu tren nhan, bao bi tu khung phong to. Bang tren chi de lap moc, khong dung de doc chu."]
    (out / "phan-tich.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    jp = proj / "job.json"
    if jp.exists():
        print(f"[GHI CHU] {jp} da co, khong ghi de; so lieu moi nam trong phan-tich/phan-tich.md")
    else:
        job = {"phien_ban": 1, "ten": video.stem, "video_goc": str(video), "kho_hinh": [info["w"], info["h"]],
               "fps": round(info["fps"], 3), "do_dai": round(info["dur"], 2), "tieng_goc": am,
               "giong": None, "toc_do": 1.0, "anh_tinh": fz, "lam_mo": [], "canh": {}, "chu": [],
               "nhac": {"kieu": "khong", "muc": -13}, "khoang_truoc": 0.15, "khoang_sau": 0.35}
        jp.write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[OK] tao {jp}")
    print(f"[OK] {out}/phan-tich.md: {info['dur']:.1f} giay, {len(fz)} doan anh tinh, {len(cuts)} moc doi canh, "
          f"{len(bang)} bang khung")


if __name__ == "__main__":
    main()
