#!/usr/bin/env python3
"""Lam mo vung trang (phieu giao hang, nhan van don) trong mot khoang thoi gian cua video.

Dung:
  python3 lam_mo_vung_trang.py IN.mp4 OUT.mp4 --den 2.97 [--tu 0] [--vung Y0:Y1] [--le 18]

Cach lam (moi khung hinh): lay diem anh trang (V cao, S thap) trong vung, noi cac manh bang
phep dong, chi giu thanh phan lon nhat (va thanh phan >= 40% no), lay bao loi roi no ra,
gop them khung hinh ke ben de khong be sot khi tay xoay nhanh. Vung do duoc lam mo manh
(thu nho roi phong to cong Gauss) nen chu va so khong doc duoc.

Gioi han da biet (xem SKILL.md, che do video co san):
- Chi chay trong [--tu, --den]. Phai tu chon --den bang mat: ngoai moc do phieu da quay di,
  nguong trang bat nham van go va bong tay.
- Phieu boc nghieng, bi tay che mot phan hoac rach thanh manh nho thi nguong trang bo sot: dung lam_mo_tay.py (khung dat tay)
  cho doan do. Luon xuat khung moi 0,1 giay de kiem tra, bao OK cua script khong dam bao khong lo phieu.
- Nguong trang bat nham chu trang trong tem do (hang de vo) va mang sang tren tay, nen che qua long: dung lam_mo_phieu_chat.py khi can che chat.
- Ma QR in tren hop (khong nam tren phieu) khong bi lam mo neu khong co nen trang du lon.
- Khung hinh co phan nen mo (clip ngang trong khung doc) thi dat --vung la dai clip o giua
  va --le la be rong dai sang o mep, neu khong nen mo se bi bat nham.
- Chi xuat hinh (khong tieng). Ghep tieng bang ghep_loi_video_co_san.py.
Yeu cau: ffmpeg, ffprobe, python3 co numpy va opencv-python.
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


def read_frames(path, w, h, limit=None):
    p = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", path, "-an", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = 0
    try:
        while limit is None or n < limit:
            b = p.stdout.read(w * h * 3)
            if len(b) < w * h * 3:
                break
            yield np.frombuffer(b, np.uint8).reshape(h, w, 3).copy()
            n += 1
    finally:
        p.stdout.close()
        p.kill()
        p.wait()


def mask_for(crop, a):
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 2] > a.v_min) & (hsv[..., 1] < a.s_max)).astype(np.uint8) * 255
    if a.le > 0:
        m[:a.le] = 0
        m[-a.le:] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    cands = [i for i in range(1, n) if min(st[i][2], st[i][3]) >= a.canh_min]
    big = max([st[i][4] for i in cands] or [0])
    out = np.zeros(m.shape, np.uint8)
    for i in cands:
        if st[i][4] >= a.dien_tich_min and st[i][4] >= 0.4 * big:
            pts = cv2.findNonZero((lab == i).astype(np.uint8))
            cv2.fillPoly(out, [cv2.convexHull(pts)], 255)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vao")
    ap.add_argument("ra")
    ap.add_argument("--tu", type=float, default=0.0, help="giay bat dau lam mo")
    ap.add_argument("--den", type=float, required=True, help="giay ket thuc lam mo (khong gom)")
    ap.add_argument("--vung", help="Y0:Y1 dai hinh can do (mac dinh: ca khung)")
    ap.add_argument("--le", type=int, default=0, help="be rong (px) o mep tren va duoi vung bi bo qua")
    ap.add_argument("--v-min", type=int, default=185)
    ap.add_argument("--s-max", type=int, default=45)
    ap.add_argument("--dien-tich-min", type=int, default=1200)
    ap.add_argument("--canh-min", type=int, default=28)
    ap.add_argument("--no", type=int, default=17, help="no bao loi (px)")
    ap.add_argument("--crf", type=int, default=14)
    a = ap.parse_args()

    w, h, fps = probe(a.vao)
    y0, y1 = (0, h)
    if a.vung:
        y0, y1 = (int(x) for x in a.vung.split(":"))
    f0, f1 = int(round(a.tu * fps)), int(round(a.den * fps))
    if f1 <= f0:
        sys.exit("[LOI] --den phai lon hon --tu")

    masks = {}
    for i, fr in enumerate(read_frames(a.vao, w, h, limit=f1)):
        if i >= f0:
            masks[i] = mask_for(fr[y0:y1], a)
    kernel = np.ones((a.no, a.no), np.uint8)
    final = {}
    for i in masks:
        u = np.zeros_like(masks[i])
        for j in (i - 1, i, i + 1):
            if j in masks:
                u = cv2.bitwise_or(u, masks[j])
        final[i] = cv2.GaussianBlur(cv2.dilate(u, kernel), (15, 15), 0)

    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
         "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf),
         "-pix_fmt", "yuv420p", a.ra], stdin=subprocess.PIPE)
    dem = 0
    for i, fr in enumerate(read_frames(a.vao, w, h)):
        al = final.get(i)
        if al is not None and al.max() > 0:
            c = fr[y0:y1]
            sm = cv2.resize(c, (max(1, c.shape[1] // 14), max(1, c.shape[0] // 14)), interpolation=cv2.INTER_AREA)
            bl = cv2.GaussianBlur(cv2.resize(sm, (c.shape[1], c.shape[0]), interpolation=cv2.INTER_LINEAR), (0, 0), 12)
            k = (al.astype(np.float32) / 255.0)[..., None]
            fr[y0:y1] = (bl * k + c * (1 - k)).astype(np.uint8)
            dem += 1
        enc.stdin.write(fr.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f"[OK] {a.ra}: lam mo {dem} khung hinh trong {a.tu} den {a.den} giay")


if __name__ == "__main__":
    main()
