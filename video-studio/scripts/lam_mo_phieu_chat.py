#!/usr/bin/env python3
"""Lam mo phieu giao hang CHAT: chi che phieu, khong che tem do, tay hay nen (video co san, chi hinh).

Dung:
  python3 lam_mo_phieu_chat.py IN.mp4 OUT.mp4 --tu 0 --den 3.0 --vung 0,720,430,850
  python3 lam_mo_phieu_chat.py OUT_LUOT1.mp4 OUT.mp4 --tu 3.0 --den 5.6 --vung 200,520,500,740

--vung X0,X1,Y0,Y1 (diem anh) la khung quan tam; ngoai khung khong bi dong vao.

Khac lam_mo_vung_trang.py (xem SKILL.md, che do video co san):
- Chi nhan vung trang (V>190, S<45) trong --vung, lam day them (--no, mac dinh 7 thay vi 17) nen khong lem sang tay, nen.
- Bo thanh phan trang nam trong tem do ("hang de vo"): neu hon 45% vien quanh thanh phan la mau do thi do la chu trang
  trong tem, khong phai phieu.
- Thanh phan lon (>= 1200 diem) duoc to day bang bao loi nen chu den tren phieu cung bi che; manh nho (>= 120 diem, canh
  >= 5) giu nguyen hinh, dung cho mep phieu lo ra o canh thung sau khi phieu bi up xuong (phong to co the thay vach ma vach).
- Chay hai luot: luot 1 cho doan phieu hien ro voi --vung la dai clip, luot 2 cho manh nho voi --vung hep quanh thung.
Luon xuat khung moi 0,1 giay de kiem tra (so khung goc voi khung da mo o cho co tem do va mep trang): bao OK
cua script khong dam bao khong lo phieu.
Gioi han: gia dinh phieu mau trang; chi xuat hinh (khong tieng); can ffmpeg, ffprobe, python3 co numpy va opencv-python.
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


def read_frames(path, w, h):
    p = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", path, "-an", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        while True:
            b = p.stdout.read(w * h * 3)
            if len(b) < w * h * 3:
                break
            yield np.frombuffer(b, np.uint8).reshape(h, w, 3).copy()
    finally:
        p.kill()
        p.wait()


def mask_for(crop, a):
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    red = (((hsv[..., 0] < 8) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 120) & (hsv[..., 2] > 90)).astype(np.uint8)
    m = ((hsv[..., 2] > a.v_min) & (hsv[..., 1] < a.s_max)).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    out = np.zeros_like(m)
    for i in range(1, n):
        dien_tich, canh = st[i][4], min(st[i][2], st[i][3])
        if dien_tich < a.dien_tich_min or canh < a.canh_min:
            continue
        comp = (lab == i).astype(np.uint8)
        ring = cv2.dilate(comp, np.ones((15, 15), np.uint8)) - comp
        if ring.sum() > 0 and (red * ring).sum() / ring.sum() > a.do_max:
            continue  # chu trang trong tem do
        if dien_tich >= a.lon:
            pts = cv2.findNonZero(comp)
            cv2.fillPoly(out, [cv2.convexHull(pts)], 255)
        else:
            out[lab == i] = 255
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vao")
    ap.add_argument("ra")
    ap.add_argument("--tu", type=float, default=0.0)
    ap.add_argument("--den", type=float, required=True, help="giay ket thuc (khong gom)")
    ap.add_argument("--vung", help="X0,X1,Y0,Y1 (mac dinh: ca khung)")
    ap.add_argument("--v-min", type=int, default=190)
    ap.add_argument("--s-max", type=int, default=45)
    ap.add_argument("--dien-tich-min", type=int, default=120)
    ap.add_argument("--canh-min", type=int, default=5)
    ap.add_argument("--lon", type=int, default=1200, help="thanh phan tu cau nay tro len duoc to day bang bao loi")
    ap.add_argument("--do-max", type=float, default=0.45, help="ti le vien do toi da; vuot thi bo (chu trong tem do)")
    ap.add_argument("--no", type=int, default=7, help="no bao loi (px)")
    ap.add_argument("--crf", type=int, default=14)
    a = ap.parse_args()

    w, h, fps = probe(a.vao)
    x0, x1, y0, y1 = (0, w, 0, h)
    if a.vung:
        x0, x1, y0, y1 = (int(v) for v in a.vung.split(","))
    f0, f1 = int(round(a.tu * fps)), int(round(a.den * fps))
    if f1 <= f0:
        sys.exit("[LOI] --den phai lon hon --tu")

    masks = {}
    for i, fr in enumerate(read_frames(a.vao, w, h)):
        if i >= f1:
            break
        if i >= f0:
            masks[i] = mask_for(fr[y0:y1, x0:x1], a)

    kernel = np.ones((a.no, a.no), np.uint8)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
         "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf),
         "-pix_fmt", "yuv420p", a.ra], stdin=subprocess.PIPE)
    dem = 0
    for i, fr in enumerate(read_frames(a.vao, w, h)):
        if i in masks:
            u = np.zeros_like(masks[i])
            for j in (i - 1, i, i + 1):
                if j in masks:
                    u = cv2.bitwise_or(u, masks[j])
            al = cv2.GaussianBlur(cv2.dilate(u, kernel), (9, 9), 0)
            if al.max() > 0:
                c = fr[y0:y1, x0:x1]
                sm = cv2.resize(c, (max(1, c.shape[1] // 14), max(1, c.shape[0] // 14)), interpolation=cv2.INTER_AREA)
                bl = cv2.GaussianBlur(cv2.resize(sm, (c.shape[1], c.shape[0])), (0, 0), 12)
                k = (al.astype(np.float32) / 255.0)[..., None]
                fr[y0:y1, x0:x1] = (bl * k + c * (1 - k)).astype(np.uint8)
                dem += 1
        enc.stdin.write(fr.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f"[OK] {a.ra}: lam mo {dem} khung hinh trong {a.tu} den {a.den} giay")


if __name__ == "__main__":
    main()
