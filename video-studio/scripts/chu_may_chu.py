#!/usr/bin/env python3
"""Tao chu ghi tren video hien ra tung chu nhu may danh chu (file .ass), va ghi vao video neu can.

Dung:
  python3 chu_may_chu.py DONG.json OUT.ass [--vao IN.mp4 --ra OUT.mp4] [tuy chon]

DONG.json: danh sach [bat_dau_giay, ket_thuc_giay, "chu chinh", "dong nguon hoac rong"], vi du:
  [[42.6, 46.0, "Belkin: thuong hieu My, lap nam 1983", "Nguon: EEPower, 27/03/2018"],
   [10.6, 15.6, "Hop nguyen ven, khong co tui khi", ""]]
Chu chinh go ra tung chu trong khoang 0,05 giay moi chu (toi da 60% thoi gian dong), roi dung yen va mo dan
0,15 giay cuoi. Dong nguon (nho, o duoi) hien sau khi go xong, mo vao 0,2 giay. Ca hai co nen toi mo de doc
duoc tren nen sang; phan chu chua go duoc giu cho (an, khong lam chu nhay dong khi xuong dong).

Quy tac noi dung (hieu rieng tung ho so, xem profiles/unbox.md): chu ngan, khong chep ca cau loi doc; thong
tin ngoai co dong nguon, thong tin lay tu tem hoac hinh tren hop ghi "Theo ...". Dat chu o dai nen mo phia
tren khung quay (mac dinh y 366 cho video 720x1280 co khung quay giua), khong de len tem va chu tren bao bi.
Anh tinh toan khung (cap can canh, mat hop) co the bi chu de len mot phan: xuat khung kiem tra bang mat.

Tuy chon: --font (mac dinh Inter), --fontsdir (thu muc chua font de ffmpeg tim; mac dinh thu muc font Inter cua he thong
neu co), --rong/--cao (mac dinh 720 1280), --y-chinh/--y-nguon, --co-chinh/--co-nguon (co chu, mac dinh 44 va 26),
--tren-giay (giay moi chu, mac dinh 0.05).
Neu co --vao va --ra: ghi chu vao hinh bang bo loc ass cua ffmpeg (ma hoa lai hinh libx264 crf 16, giu nguyen tieng).
Can ffmpeg co libass va font ho tro tieng Viet (Inter, Be Vietnam Pro ban .ttf/.otf; font .woff khong dung duoc).
"""
import argparse
import json
import os
import subprocess
import sys

STYLE_FMT = ("Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,"
             "Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,"
             "MarginV,Encoding")


def thoi(x):
    h = int(x // 3600)
    m = int(x % 3600 // 60)
    s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dong")
    ap.add_argument("ra_ass")
    ap.add_argument("--vao")
    ap.add_argument("--ra")
    ap.add_argument("--font", default="Inter")
    ap.add_argument("--fontsdir", default="/usr/share/fonts/opentype/inter")
    ap.add_argument("--rong", type=int, default=720)
    ap.add_argument("--cao", type=int, default=1280)
    ap.add_argument("--y-chinh", type=int, default=366)
    ap.add_argument("--y-nguon", type=int, default=392)
    ap.add_argument("--co-chinh", type=int, default=44)
    ap.add_argument("--co-nguon", type=int, default=26)
    ap.add_argument("--tren-giay", type=float, default=0.05)
    a = ap.parse_args()

    dong = json.load(open(a.dong, encoding="utf-8"))
    cx = a.rong // 2
    hdr = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {a.rong}\nPlayResY: {a.cao}\nWrapStyle: 0\n"
           "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\n" + STYLE_FMT + "\n"
           f"Style: Chu,{a.font},{a.co_chinh},&H00FFFFFF,&H00FFFFFF,&H66000000,&H00000000,-1,0,0,0,100,100,0,0,3,12,0,2,50,50,0,1\n"
           f"Style: Nguon,{a.font},{a.co_nguon},&H00F0F0F0,&H00F0F0F0,&H66000000,&H00000000,0,0,0,0,100,100,0,0,3,9,0,8,50,50,0,1\n\n"
           "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    ev = []
    for d in dong:
        s, e, txt = float(d[0]), float(d[1]), d[2]
        src = d[3] if len(d) > 3 else ""
        if e <= s or not txt:
            sys.exit(f"[LOI] dong khong hop le: {d}")
        n = len(txt)
        step = min(a.tren_giay, 0.6 * (e - s) / n)
        xong = s + n * step
        for k in range(1, n):
            ev.append(f"Dialogue: 1,{thoi(s + (k - 1) * step)},{thoi(s + k * step)},Chu,,0,0,0,,"
                      f"{{\\pos({cx},{a.y_chinh})}}{txt[:k]}{{\\alpha&HFF&}}{txt[k:]}")
        ev.append(f"Dialogue: 1,{thoi(s + (n - 1) * step)},{thoi(e)},Chu,,0,0,0,,"
                  f"{{\\pos({cx},{a.y_chinh})\\fad(0,150)}}{txt}")
        if src:
            ev.append(f"Dialogue: 0,{thoi(xong)},{thoi(e)},Nguon,,0,0,0,,"
                      f"{{\\pos({cx},{a.y_nguon})\\fad(200,150)}}{src}")
    open(a.ra_ass, "w", encoding="utf-8").write(hdr + "\n".join(ev) + "\n")
    print(f"[OK] {a.ra_ass}: {len(dong)} dong, {len(ev)} su kien")

    if a.vao or a.ra:
        if not (a.vao and a.ra):
            sys.exit("[LOI] --vao va --ra di cung nhau")
        fd = f":fontsdir={a.fontsdir}" if a.fontsdir and os.path.isdir(a.fontsdir) else ""
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", a.vao, "-vf", f"ass={a.ra_ass}{fd}",
                               "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
                               "-c:a", "copy", "-movflags", "+faststart", a.ra])
        print(f"[OK] {a.ra}")


if __name__ == "__main__":
    main()
