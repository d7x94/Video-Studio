#!/usr/bin/env python3
"""Lam mo bang khung dat tay theo moc thoi gian (phieu giao hang bi boc nghieng, tay che, rach manh).

Dung khi lam_mo_vung_trang.py bo sot: phieu nghieng, bi tay che mot phan hoac rach thanh manh nho
nen nguong "vung trang" khong bat duoc.

Dung:
  python3 lam_mo_tay.py IN.mp4 OUT.mp4 --khung khung.json [--crf 14]

khung.json: danh sach moc [giay, x0, y0, x1, y1], toa do theo khung hinh goc (diem anh, khong phai ti le).
Khung duoc noi suy tuyen tinh giua hai moc lien nhau; chi lam mo tu moc dau den moc cuoi, ngoai
khoang do giu nguyen. Vi du:
  [[2.3, 210, 500, 370, 690], [2.5, 190, 480, 360, 650], [3.1, 190, 420, 380, 520]]

Cach lay toa do: xuat khung moi 0,1 giay trong khoang co phieu, doc x, y cua phieu (va manh giay rach,
phan phieu lo ra duoi ban tay), dat khung rong hon phieu khoang 20 den 40 diem moi canh. Dat moc day
(0,1 den 0,2 giay) khi tay dang xoay nhanh. Sau khi chay, xuat lai cac khung o tung moc de kiem tra
bang mat: khong con chu, ma vach, ma QR nao doc duoc.

Co the chay sau lam_mo_vung_trang.py (cho khoang dau phieu nam yen), dua ra cua script do vao day.
Chi xuat hinh (khong tieng). Yeu cau: ffmpeg, ffprobe, python3 co numpy va opencv-python.
"""
import argparse
import json
import subprocess
import sys

import cv2
import numpy as np


def probe(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate", "-of", "json", path])
    s = json.loads(out)["streams"][0]
    a, b = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(a) / float(b)


def khung_tai(moc, t):
    if t < moc[0][0] or t > moc[-1][0]:
        return None
    for a, b in zip(moc, moc[1:]):
        if a[0] <= t <= b[0]:
            r = 0.0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
            return [int(round(a[i] + (b[i] - a[i]) * r)) for i in range(1, 5)]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vao")
    ap.add_argument("ra")
    ap.add_argument("--khung", required=True, help="file JSON cac moc [giay,x0,y0,x1,y1]")
    ap.add_argument("--crf", type=int, default=14)
    a = ap.parse_args()

    moc = json.load(open(a.khung, encoding="utf-8"))
    if len(moc) < 2 or any(len(m) != 5 for m in moc):
        sys.exit("[LOI] --khung can it nhat 2 moc, moi moc [giay,x0,y0,x1,y1]")
    moc.sort(key=lambda m: m[0])
    w, h, fps = probe(a.vao)

    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.vao, "-an", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-pix_fmt", "yuv420p", a.ra],
        stdin=subprocess.PIPE)
    i = dem = 0
    while True:
        b = dec.stdout.read(w * h * 3)
        if len(b) < w * h * 3:
            break
        fr = np.frombuffer(b, np.uint8).reshape(h, w, 3).copy()
        bx = khung_tai(moc, i / fps)
        if bx:
            x0, y0, x1, y1 = max(0, bx[0]), max(0, bx[1]), min(w, bx[2]), min(h, bx[3])
            if x1 > x0 and y1 > y0:
                c = fr[y0:y1, x0:x1]
                sm = cv2.resize(c, (max(1, c.shape[1] // 14), max(1, c.shape[0] // 14)), interpolation=cv2.INTER_AREA)
                fr[y0:y1, x0:x1] = cv2.GaussianBlur(cv2.resize(sm, (c.shape[1], c.shape[0])), (0, 0), 12)
                dem += 1
        enc.stdin.write(fr.tobytes())
        i += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"[OK] {a.ra}: lam mo {dem} khung hinh ({moc[0][0]} den {moc[-1][0]} giay)")


if __name__ == "__main__":
    main()
