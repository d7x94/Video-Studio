#!/usr/bin/env python3
"""Kieu video "tien bay": o tien nhay so, the gia bay vao o tien, bien lai in ra o cuoi.

Dung:
  python3 may_tinh_tien.py PROJECT kiem                 # kiem file tien-bay.json va doan cat trong video goc
  python3 may_tinh_tien.py PROJECT khung                # xuat khung lop phu mau len khung goc: qa/tien-bay/
  python3 may_tinh_tien.py PROJECT dung [--ra FILE]     # tao tieng hieu ung + render (mac dinh renders/final_portrait.mp4)

Doc PROJECT/tien-bay.json (xem references/che-do-tien-bay.md). Ghi:
  timeline.json          (total, scenes co visual_start, visual_duration: de check_output.py doc)
  audio/hieu-ung.wav     (tieng may tinh tien, may in bien lai, the gia; nhac_nen.py tu tron khi ghep nhac)
  renders/final_portrait.mp4 (khong nhac: tieng chi la tieng im; chay nhac_nen.py sau do)

Tong tien tinh bang code tu cac dong "mon"; neu co "tong_hoa_don" thi phai khop, lech thi dung lai.
Can: ffmpeg, ffprobe, Pillow, numpy, soundfile.
"""
import functools
import json
import math
import subprocess
import sys
import unicodedata
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError as e:
    sys.exit(f"[LOI] thieu thu vien ({e}): pip install --break-system-packages Pillow numpy soundfile")

W, H, FPS = 1080, 1920, 30
SR = 48000
ARRIVE = 1.9      # giay tu luc doan anh san pham bat dau den luc the cham o tien
ROLL = 0.6        # giay so nhay len
MAU = [(230, 120, 40, 255), (60, 140, 220, 255), (150, 90, 200, 255), (40, 160, 120, 255)]
REG = (190, 120, 890, 330)     # o tien: x0,y0,x1,y1
REG_C = ((REG[0] + REG[2]) / 2, (REG[1] + REG[3]) / 2)
TAG_C = (520, 1180)
RC_X0, RC_X1, RC_Y0, RC_LH = 230, 850, REG[3] - 10, 46
PRINT0, PRINT_STEP = 0.7, 0.30
MAX_MON = 16


def vnd(n):
    return f"{int(round(n)):,}".replace(",", ".") + "đ"


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def back_out(x):
    x = clamp(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


_DA_BAO_FONT = set()


@functools.lru_cache(maxsize=None)
def tim_font(ho, kieu):
    """Tim file font qua fc-match (Inter neu co, khong thi DejaVu Sans); font phai co chu Viet co dau.

    fc-match luon tra ve mot font thay the khi khong co ho yeu cau, nen phai so ten ho tra ve voi ho yeu cau."""
    for fam in dict.fromkeys((ho, "DejaVu Sans")):
        r = subprocess.run(["fc-match", "-f", "%{family}\n%{file}", f"{fam}:style={kieu}"], capture_output=True, text=True)
        if r.returncode != 0 or "\n" not in r.stdout:
            continue
        ho_tra, file = r.stdout.split("\n", 1)
        if fam.lower() in [h.strip().lower() for h in ho_tra.split(",")] and Path(file).exists():
            if fam != ho and ho not in _DA_BAO_FONT:
                _DA_BAO_FONT.add(ho)
                print(f"[CANH BAO] khong co font '{ho}', dung {fam}", file=sys.stderr)
            return file
    sys.exit(f"[LOI] khong tim thay font '{ho}' hay DejaVu Sans (kiem bang fc-list)")


# ---------- doc va kiem cau hinh ----------
def doc_cau_hinh(proj):
    f = proj / "tien-bay.json"
    if not f.exists():
        sys.exit(f"[LOI] chua co {f} (mau: references/che-do-tien-bay.md)")
    cfg = json.loads(f.read_text(encoding="utf-8"))

    def nfc(o):
        if isinstance(o, str):
            return unicodedata.normalize("NFC", o)
        if isinstance(o, list):
            return [nfc(x) for x in o]
        if isinstance(o, dict):
            return {k: nfc(v) for k, v in o.items()}
        return o
    cfg = nfc(cfg)
    # lam tron moi 'dai' ve luoi khung (1/FPS giay): trim cat theo so khung nguyen, neu khong lam tron thi
    # moi doan du toi 1 khung va hinh nen lech dan so voi lop phu (tinh theo giay)
    doan = [cfg.get("mo_dau"), cfg.get("ket")]
    for m in cfg.get("mon", []) if isinstance(cfg.get("mon"), list) else []:
        if isinstance(m, dict):
            doan += [m.get("mo"), m.get("anh")]
    for d in doan:
        if isinstance(d, dict) and la_so(d.get("dai")):
            d["dai"] = round(d["dai"] * FPS) / FPS
    return cfg


def la_so(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def la_nguyen(x):
    return isinstance(x, int) and not isinstance(x, bool)


def do_dai(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def kiem(proj, cfg):
    loi, canh_bao = [], []
    video = proj / cfg.get("video", "")
    if not cfg.get("video") or not video.exists():
        loi.append(f"khong thay video goc: {video}")
        dai_goc = None
    else:
        dai_goc = do_dai(video)
    mon = cfg.get("mon", [])
    if not mon:
        loi.append("khong co dong nao trong 'mon'")
    if len(mon) > MAX_MON:
        loi.append(f"{len(mon)} mon, toi da {MAX_MON} (bien lai se tran khung)")
    tong = 0
    nhom_thay = []
    doan = []

    def kiem_doan(ten, d):
        if (not isinstance(d, dict) or not la_so(d.get("tu")) or not la_so(d.get("dai"))
                or d["tu"] < 0 or d["dai"] <= 0):
            loi.append(f"{ten}: can {{'tu': giay >= 0, 'dai': giay > 0}}")
            return False
        doan.append((ten, d))
        if dai_goc is not None and d["tu"] + d["dai"] > dai_goc + 0.05:
            loi.append(f"{ten}: {d['tu']}+{d['dai']} vuot do dai video goc {dai_goc:.1f} giay")
        return True

    if "mo_dau" in cfg:
        kiem_doan("mo_dau", cfg["mo_dau"])
    else:
        loi.append("thieu 'mo_dau' {tu, dai}")
    ket = cfg.get("ket", {})
    if not la_so(ket.get("nen_tu")) or not la_so(ket.get("dai")) or ket["dai"] < 8:
        loi.append("'ket' can nen_tu (giay khung lam nen) va dai >= 8 (bien lai in het moi toi cuoi)")
    elif ket["nen_tu"] < 0 or (dai_goc is not None and ket["nen_tu"] > dai_goc - 0.2):
        loi.append(f"ket.nen_tu = {ket['nen_tu']} nam ngoai video goc"
                   + (f" ({dai_goc:.1f} giay; can 0 den {max(0.0, dai_goc - 0.2):.1f})" if dai_goc is not None else ""))
    for i, m in enumerate(mon):
        ten = m.get("ten", f"mon {i + 1}")
        for k in ("ten", "so_luong", "gia", "nhom", "anh"):
            if k not in m:
                loi.append(f"{ten}: thieu '{k}'")
        if "gia" in m:
            if not la_nguyen(m["gia"]) or m["gia"] <= 0:
                loi.append(f"{ten}: 'gia' phai la so nguyen duong (thanh tien cua dong, don vi dong)")
            else:
                tong += m["gia"]
        if "so_luong" in m and (not la_nguyen(m["so_luong"]) or m["so_luong"] < 1):
            loi.append(f"{ten}: 'so_luong' phai la so nguyen >= 1")
        if "anh" in m and kiem_doan(f"{ten}.anh", m["anh"]) and m["anh"]["dai"] < ARRIVE + ROLL + 0.5:
            loi.append(f"{ten}.anh.dai = {m['anh']['dai']} qua ngan, can >= {ARRIVE + ROLL + 0.5:.1f} (the bay vao o tien roi so nhay)")
        if "mo" in m:
            kiem_doan(f"{ten}.mo", m["mo"])
        if "chia" in m:
            c = m["chia"]
            if not la_nguyen(c.get("so")) or c["so"] < 1 or not c.get("don_vi"):
                loi.append(f"{ten}.chia: can so (nguyen >= 1) va don_vi")
            elif "anh" in m and m["anh"].get("dai", 0) < 3.4:
                canh_bao.append(f"{ten}: co 'chia' nhung anh.dai < 3.4 giay, nhan 'mot {c['don_vi']}' se hien rat ngan")
        if m.get("nhom") and m["nhom"] not in nhom_thay:
            nhom_thay.append(m["nhom"])
    if len(nhom_thay) > len(MAU):
        loi.append(f"{len(nhom_thay)} nhom, toi da {len(MAU)}")
    if "tong_hoa_don" in cfg and tong != cfg["tong_hoa_don"]:
        loi.append(f"tong cac dong = {vnd(tong)} KHAC tong_hoa_don = {vnd(cfg['tong_hoa_don'])}: thieu hoac sai dong")
    elif "tong_hoa_don" not in cfg:
        canh_bao.append("khong co 'tong_hoa_don': khong doi chieu duoc tong voi hoa don that (nen chup them tam tong don)")
    if not cfg.get("ngay"):
        canh_bao.append("khong co 'ngay': mo dau khong hien nhan ngay")
    return loi, canh_bao, tong


# ---------- tinh trang thai du an ----------
class D:
    pass


def khoi_tao(proj, cfg, tong):
    d = D()
    d.proj, d.cfg = proj, cfg
    mon = list(cfg["mon"])
    if cfg.get("dat_nhat_cuoi", True):
        idx = max(range(len(mon)), key=lambda i: (mon[i]["gia"], i))
        mon.append(mon.pop(idx))
    d.mon = mon
    d.tong = tong
    d.dat_nhat = max(range(len(mon)), key=lambda i: (mon[i]["gia"], i)) if cfg.get("mon_dat_nhat", True) else -1
    d.nhom = []
    for m in mon:
        if m["nhom"] not in d.nhom:
            d.nhom.append(m["nhom"])
    d.nhom_tien = {g: sum(m["gia"] for m in mon if m["nhom"] == g) for g in d.nhom}
    d.mo_dau = cfg["mo_dau"]
    d.end_dur = cfg["ket"]["dai"]
    d.end_src = cfg["ket"]["nen_tu"]
    d.canh, t = [], d.mo_dau["dai"]
    for i, m in enumerate(mon):
        dm = m["mo"]["dai"] if "mo" in m else 0.0
        d.canh.append({"i": i, "start": t, "t0": t + dm, "dur": dm + m["anh"]["dai"]})
        t += dm + m["anh"]["dai"]
    d.end_start = t
    d.total = t + d.end_dur
    d.rlines = []
    for m in mon:
        nm = m.get("ten_bien_lai") or m["ten"]
        nm = nm if m["so_luong"] == 1 else f"{nm} x{m['so_luong']}"
        d.rlines.append((nm, vnd(m["gia"]).replace("đ", "")))
    d.t_total_line = PRINT0 + PRINT_STEP * (len(d.rlines) + 1) + 0.2
    d.t_bars = d.t_total_line + 1.0
    # font
    ho = cfg.get("font", "Inter")
    f = lambda kieu, size: ImageFont.truetype(tim_font(ho, kieu), size)
    d.f = {"L": f("Bold", 30), "num": f("Black", 92), "name": f("ExtraBold", 50), "qty": f("Bold", 40),
           "price": f("Black", 84), "badge": f("Black", 34), "plus": f("Black", 54), "rc": f("SemiBold", 32),
           "rcb": f("Black", 40), "rch": f("Black", 34), "bar": f("Bold", 34), "date": f("Black", 80),
           "note": f("Black", 60), "total": lambda s: f("Black", s)}
    d.shadow = Image.new("RGBA", (REG[2] - REG[0] + 100, REG[3] - REG[1] + 110), (0, 0, 0, 0))
    ImageDraw.Draw(d.shadow).rounded_rectangle((46, 52, REG[2] - REG[0] + 46, REG[3] - REG[1] + 52), 34, fill=(0, 0, 0, 110))
    d.shadow = d.shadow.filter(ImageFilter.GaussianBlur(14))
    d.tags = [the_gia(d, m, i == d.dat_nhat) for i, m in enumerate(mon)]
    return d


# ---------- ve ----------
def rr(dr, box, r, fill, outline=None, width=0):
    dr.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def the_gia(d, m, expensive):
    f = d.f
    w = 760
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines, cur = [], ""
    for wd in m["ten"].split():
        s = (cur + " " + wd).strip()
        if tmp.textlength(s, font=f["name"]) > w - 90 and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = s
    lines.append(cur)
    top = 70 if expensive else 34
    h = top + 62 * len(lines) + 160
    im = Image.new("RGBA", (w, h + 20), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    rr(dr, (0, 10, w, h + 10), 30, (255, 252, 240, 255),
       outline=(214, 40, 40, 255) if expensive else (255, 196, 40, 255), width=8)
    dr.ellipse((w - 70, 34, w - 42, 62), fill=(34, 40, 48, 255))
    if expensive:
        rr(dr, (30, -2, 330, 58), 16, (214, 40, 40, 255))
        dr.text((180, 28), "MÓN ĐẮT NHẤT", font=f["badge"], fill=(255, 255, 255, 255), anchor="mm")
    y = top + 10
    for ln in lines:
        dr.text((44, y), ln, font=f["name"], fill=(30, 34, 40, 255))
        y += 62
    if m["so_luong"] > 1:
        rr(dr, (44, y + 18, 44 + 96, y + 78), 14, (34, 40, 48, 255))
        dr.text((92, y + 48), f"x{m['so_luong']}", font=f["qty"], fill=(255, 196, 40, 255), anchor="mm")
    dr.text((w - 44, y + 52), vnd(m["gia"]), font=f["price"],
            fill=(214, 40, 40, 255) if expensive else (20, 120, 60, 255), anchor="rm")
    return im


def tong_tai(d, t):
    s = 0.0
    for c in d.canh:
        m = d.mon[c["i"]]
        roll = ROLL * (1.7 if c["i"] == d.dat_nhat else 1)
        k = (t - c["t0"] - ARRIVE) / roll
        if k <= 0:
            break
        s += m["gia"] * ease_out(k)
    return s


def mon_xong(d, t):
    return sum(1 for c in d.canh if t >= c["t0"] + ARRIVE)


def ve_o_tien(d, img, t, flash, shake):
    dr = ImageDraw.Draw(img)
    dx = int(round(math.sin(t * 90) * 14 * shake))
    x0, y0, x1, y1 = REG[0] + dx, REG[1], REG[2] + dx, REG[3]
    img.alpha_composite(d.shadow, (x0 - 40, y0 - 40))
    rr(dr, (x0, y0, x1, y1), 34, (34, 40, 48, 245), outline=(255, 196, 40, 255), width=6)
    dr.text((x0 + 34, y0 + 22), "TỔNG TIỀN", font=d.f["L"], fill=(255, 196, 40, 255))
    dr.text((x1 - 34, y0 + 22), f"{mon_xong(d, t)}/{len(d.mon)} món", font=d.f["L"], fill=(200, 205, 212, 255), anchor="ra")
    g = int(40 + 120 * flash)
    rr(dr, (x0 + 26, y0 + 70, x1 - 26, y1 - 22), 18, (12 + g // 3, 34 + g // 2, 20 + g // 4, 255))
    col = (124 + int(131 * flash), 255, 138 + int(117 * flash), 255)
    dr.text((x1 - 50, (y0 + 70 + y1 - 22) / 2 + 2), vnd(tong_tai(d, t)), font=d.f["num"], fill=col, anchor="rm")


def dan_anh(img, src, cx, cy, s, alpha):
    if s <= 0.01 or alpha <= 0.01:
        return
    w, h = int(src.width * s), int(src.height * s)
    if w < 2 or h < 2:
        return
    im = src.resize((w, h), Image.LANCZOS)
    if alpha < 1:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(im, (int(cx - w / 2), int(cy - h / 2)))


def hop_chu(img, xy, txt, fnt, fg, bg, pad=(26, 14), anchor="mm", alpha=1.0):
    dr = ImageDraw.Draw(img)
    l, t_, r, b = dr.textbbox(xy, txt, font=fnt, anchor=anchor)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((l - pad[0], t_ - pad[1], r + pad[0], b + pad[1]), 20, fill=bg)
    ld.text(xy, txt, font=fnt, fill=fg, anchor=anchor)
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(layer)


def ve_ket(d, img, te):
    dr = ImageDraw.Draw(img)
    f = d.f
    n = len(d.rlines)
    nprint = clamp((te - PRINT0) / PRINT_STEP, 0, n + 1)
    shown = int(nprint)
    total_shown = te >= d.t_total_line
    head = 90
    body_h = head + RC_LH * min(shown, n) + (40 if shown > n else 0) + (90 if total_shown else 0) + 24
    if te < 0.5:
        body_h = int(body_h * clamp(te / 0.5))
    y1 = RC_Y0 + max(body_h, 10)
    giay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(giay)
    gd.rectangle((RC_X0 + 8, RC_Y0 + 16, RC_X1 + 8, y1 + 16), fill=(0, 0, 0, 90))
    giay = giay.filter(ImageFilter.GaussianBlur(10))
    gd = ImageDraw.Draw(giay)
    gd.rectangle((RC_X0, RC_Y0, RC_X1, y1), fill=(251, 248, 238, 255))
    rang = [(RC_X0, y1)]
    x = RC_X0
    while x < RC_X1:
        rang += [(min(x + 12, RC_X1), y1 + 12), (min(x + 24, RC_X1), y1)]
        x += 24
    gd.polygon(rang + [(RC_X1, y1 - 1), (RC_X0, y1 - 1)], fill=(251, 248, 238, 255))
    img.alpha_composite(giay)
    ink = (40, 40, 44, 255)
    y = RC_Y0 + 34
    if body_h > 80:
        dr.text(((RC_X0 + RC_X1) / 2, y + 10), d.cfg["ket"].get("tieu_de", "HÓA ĐƠN ĐI CHỢ"), font=f["rch"], fill=ink, anchor="mm")
        dr.line((RC_X0 + 30, y + 44, RC_X1 - 30, y + 44), fill=(150, 150, 150, 255), width=2)
    y += head - 20
    for k in range(min(shown, n)):
        nm, pr = d.rlines[k]
        maxw = RC_X1 - RC_X0 - 60 - dr.textlength(pr, font=f["rc"]) - 20
        while dr.textlength(nm, font=f["rc"]) > maxw:
            nm = nm[:-2].rstrip() + "…"
        col = (214, 40, 40, 255) if k == d.dat_nhat else ink
        dr.text((RC_X0 + 30, y), nm, font=f["rc"], fill=col)
        dr.text((RC_X1 - 30, y), pr, font=f["rc"], fill=col, anchor="ra")
        y += RC_LH
    if shown > n:
        for xx in range(RC_X0 + 30, RC_X1 - 30, 18):
            dr.line((xx, y + 14, xx + 9, y + 14), fill=(120, 120, 120, 255), width=3)
        y += 40
    if total_shown:
        k = back_out((te - d.t_total_line) / 0.35)
        dr.text((RC_X0 + 30, y + 40), "TỔNG CỘNG", font=f["rcb"], fill=ink, anchor="lm")
        dr.text((RC_X1 - 30, y + 40), vnd(d.tong), font=f["total"](max(10, int(50 * (0.6 + 0.4 * k)))),
                fill=(214, 40, 40, 255), anchor="rm")
    if te >= d.t_bars and len(d.nhom) > 1:
        yb = RC_Y0 + head + RC_LH * n + 40 + 90 + 24 + 50
        for j, g in enumerate(d.nhom):
            k = ease_out((te - d.t_bars - j * 0.25) / 0.7)
            if k <= 0:
                continue
            v = d.nhom_tien[g]
            pct = v / d.tong
            y0 = yb + j * 104
            lop = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lop)
            ld.rounded_rectangle((RC_X0 - 20, y0, RC_X1 + 20, y0 + 88), 22, fill=(20, 24, 30, 215))
            ld.rounded_rectangle((RC_X0 + 4, y0 + 58, RC_X0 + 4 + (RC_X1 - RC_X0 - 8) * pct * k, y0 + 74), 8, fill=MAU[j])
            ld.text((RC_X0 + 4, y0 + 30), g, font=f["bar"], fill=(255, 255, 255, 255), anchor="lm")
            ld.text((RC_X1 - 4, y0 + 30), f"{vnd(v * k)}  ·  {round(pct * 100 * k)}%", font=f["bar"],
                    fill=(255, 255, 255, 255), anchor="rm")
            lop.putalpha(lop.getchannel("A").point(lambda a: int(a * clamp(k * 1.5))))
            img.alpha_composite(lop)


def ghi_chu_dat_nhat(m):
    c = m.get("chia")
    if not c:
        return None
    return f"≈ {vnd(round(m['gia'] / c['so'] / 100) * 100)} một {c['don_vi']}"


def khung(d, t):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    flash, shake = 0.0, 0.0
    for c in d.canh:
        dt = t - c["t0"] - ARRIVE
        if 0 <= dt < 0.35:
            flash = max(flash, 1 - dt / 0.35)
        if c["i"] == d.dat_nhat and 0 <= dt < 0.6:
            shake = 1 - dt / 0.6
    if d.end_start + d.t_total_line <= t < d.end_start + d.t_total_line + 0.35:
        flash = 1 - (t - d.end_start - d.t_total_line) / 0.35
    if t >= d.end_start:
        ve_ket(d, img, t - d.end_start)
    ngay = d.cfg.get("ngay")
    if ngay and t < d.mo_dau["dai"] and t > 0.25:
        k = back_out((t - 0.25) / 0.45)
        a = clamp((t - 0.25) / 0.2) * (1 - clamp((t - (d.mo_dau["dai"] - 0.3)) / 0.3))
        lb = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
        hop_chu(lb, (W // 2, 150), ngay, d.f["date"], (34, 40, 48, 255), (255, 196, 40, 255), pad=(38, 22))
        dan_anh(img, lb, 520, 1150, 0.7 + 0.3 * k, a)
    ve_o_tien(d, img, t, flash, shake)
    sc = next((c for c in d.canh if c["start"] <= t < c["start"] + c["dur"]), None)
    if sc is not None and t >= sc["t0"]:
        lt = t - sc["t0"]
        m = d.mon[sc["i"]]
        tag = d.tags[sc["i"]]
        if lt < 1.4:
            if lt > 0.12:
                dan_anh(img, tag, TAG_C[0], TAG_C[1], 0.55 + 0.45 * back_out((lt - 0.12) / 0.38), clamp((lt - 0.12) / 0.15))
        elif lt < ARRIVE:
            k = ease_in_out((lt - 1.4) / (ARRIVE - 1.4))
            cx = TAG_C[0] + (REG_C[0] - TAG_C[0]) * k
            cy = TAG_C[1] + (REG_C[1] - TAG_C[1]) * k - math.sin(k * math.pi) * 120
            dan_anh(img, tag, cx, cy, 1 - 0.8 * k, 1 - clamp((k - 0.75) / 0.25))
        dp = lt - ARRIVE
        if 0 <= dp < 1.1:
            hop_chu(img, (REG_C[0], REG[3] + 60 - 40 * ease_out(dp / 1.1)), "+" + vnd(m["gia"]), d.f["plus"],
                    (255, 255, 255, 255), (20, 140, 70, 230), alpha=1 - clamp((dp - 0.6) / 0.5))
        note = ghi_chu_dat_nhat(m) if sc["i"] == d.dat_nhat else None
        if note and lt >= 2.6:
            st = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
            hop_chu(st, (W // 2, 100), note, d.f["note"], (255, 255, 255, 255), (214, 40, 40, 240), pad=(34, 20))
            dan_anh(img, st, 520, 1180, 0.6 + 0.4 * back_out((lt - 2.6) / 0.4), clamp((lt - 2.6) / 0.15))
    return img


# ---------- tieng hieu ung ----------
def tao_tieng(d):
    import soundfile as sf
    n = int(d.total * SR) + SR
    buf = np.zeros(n)
    rng = np.random.default_rng(7)

    def add(t0, sig):
        i = int(t0 * SR)
        j = min(n, i + len(sig))
        if i < n:
            buf[i:j] += sig[: j - i]

    def tt(dur):
        return np.arange(int(dur * SR)) / SR

    def nhieu(dur, lo, hi):
        x = rng.standard_normal(int(dur * SR))
        X = np.fft.rfft(x)
        fr = np.fft.rfftfreq(len(x), 1 / SR)
        X[(fr < lo) | (fr > hi)] = 0
        y = np.fft.irfft(X, len(x))
        return y / (np.abs(y).max() + 1e-9)

    def chuong(dur=0.9, base=2350.0):
        x = tt(dur)
        y = sum(a * np.sin(2 * np.pi * base * mu * x) * np.exp(-r * x)
                for a, mu, r in [(1.0, 1.0, 5.5), (0.6, 2.76, 7.0), (0.35, 5.40, 9.0), (0.2, 8.93, 12.0)])
        y *= np.minimum(1, x / 0.002)
        return y / np.abs(y).max()

    def kaching(t0, g=1.0):
        add(t0, 0.55 * g * nhieu(0.035, 1500, 6000) * np.exp(-tt(0.035) * 90))
        x = tt(0.12)
        add(t0 + 0.01, 0.45 * g * np.sin(2 * np.pi * 110 * x) * np.exp(-x * 35))
        add(t0 + 0.02, 0.3 * g * nhieu(0.25, 300, 2500) * np.exp(-tt(0.25) * 18))
        add(t0 + 0.07, 0.55 * g * chuong())
        add(t0 + 0.16, 0.42 * g * chuong(base=2350 * 1.06))

    def tick(t0, g=0.18):
        add(t0, g * nhieu(0.012, 2500, 9000) * np.exp(-tt(0.012) * 300))

    def pop(t0):
        x = tt(0.09)
        add(t0, 0.22 * np.sin(2 * np.pi * np.cumsum(520 + 500 * x / 0.09) / SR) * np.sin(np.pi * x / 0.09))

    def whoosh(t0, dur=0.5):
        add(t0, 0.12 * nhieu(dur, 400, 5000) * np.sin(np.pi * tt(dur) / dur) ** 2)

    def boom(t0):
        x = tt(0.5)
        add(t0, 0.7 * np.sin(2 * np.pi * (55 + 30 * np.exp(-x * 8)) * x) * np.exp(-x * 7))

    def in_bl(t0, dur=0.22):
        x = tt(dur)
        y = nhieu(dur, 600, 4000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * x)))
        add(t0, 0.13 * y * np.minimum(1, (dur - x) / 0.02))

    if d.cfg.get("ngay"):
        pop(0.25)
    for c in d.canh:
        st = c["t0"]
        pop(st + 0.12)
        whoosh(st + 1.4, ARRIVE - 1.4 + 0.1)
        kaching(st + ARRIVE)
        roll = ROLL * (1.7 if c["i"] == d.dat_nhat else 1)
        for k in np.arange(0, roll, 0.045):
            tick(st + ARRIVE + 0.03 + k)
        if c["i"] == d.dat_nhat:
            boom(st + ARRIVE)
            if ghi_chu_dat_nhat(d.mon[c["i"]]):
                pop(st + 2.6)
    e = d.end_start
    whoosh(e + 0.05, 0.5)
    for k in range(len(d.rlines) + 1):
        in_bl(e + PRINT0 + PRINT_STEP * k)
    kaching(e + d.t_total_line, 1.1)
    if len(d.nhom) > 1:
        whoosh(e + d.t_bars, 0.6)
        whoosh(e + d.t_bars + 0.25, 0.6)
    fx = np.stack([buf, buf])[:, : int(d.total * SR)] * 0.6
    peak = np.abs(fx).max()
    if peak > 0.95:
        fx *= 0.95 / peak
    (d.proj / "audio").mkdir(exist_ok=True)
    sf.write(d.proj / "audio/hieu-ung.wav", fx.T, SR)


# ---------- hinh nen va render ----------
def doan_nen(d):
    segs = [("mo_dau", d.cfg["mo_dau"])]
    for m in d.mon:
        if "mo" in m:
            segs.append((m["ten"] + ".mo", m["mo"]))
        segs.append((m["ten"] + ".anh", m["anh"]))
    return [s for _, s in segs]


def loc_nen(d, segs):
    parts, labels = [], []
    for n, s in enumerate(segs):
        z = 0.05
        dur = s["dai"]
        parts.append(f"[{n}:v]setpts=PTS-STARTPTS,fps={FPS},trim=end_frame={round(dur * FPS)},"
                     f"scale=w='trunc({W}*(1+{z}*t/{dur})/2)*2':h='trunc({H}*(1+{z}*t/{dur})/2)*2':eval=frame:flags=bicubic,"
                     f"crop={W}:{H},setsar=1,format=yuv420p[s{n}]")
        labels.append(f"[s{n}]")
    parts.append(f"[{len(segs)}:v]setpts=PTS-STARTPTS,fps={FPS},trim=duration=0.05,scale={W}:{H},"
                 f"tpad=stop_mode=clone:stop_duration={d.end_dur},trim=end_frame={round(d.end_dur * FPS)},boxblur=20:2,"
                 f"eq=brightness=-0.12:saturation=0.8,setsar=1,format=yuv420p[se]")
    labels.append("[se]")
    parts.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0[base]")
    parts.append(f"[{len(segs) + 1}:v]format=rgba[ov];[base][ov]overlay=0:0:format=auto,format=yuv420p[out]")
    return ";".join(parts)


def dung(d, ra):
    segs = doan_nen(d)
    video = d.proj / d.cfg["video"]
    # moi doan mot dau vao rieng co -ss: cat nhieu doan tu mot file dai bang trim tren mot dau vao lam ffmpeg dung do (broken pipe)
    ins = []
    for s in segs + [{"tu": d.end_src, "dai": 0.2}]:
        ins += ["-ss", f"{s['tu']}", "-t", f"{s['dai'] + 0.3}", "-i", str(video)]
    na = len(segs) + 2
    cmd = ["ffmpeg", "-v", "error", "-y", *ins,
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{d.total:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
           "-filter_complex", loc_nen(d, segs), "-map", "[out]", "-map", f"{na}:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", "-t", f"{d.total:.3f}", str(ra)]
    ra.parent.mkdir(parents=True, exist_ok=True)
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nfr = int(round(d.total * FPS))
    try:
        for f in range(nfr):
            pr.stdin.write(khung(d, f / FPS).tobytes())
            if f % 300 == 0:
                print(f"  khung {f}/{nfr}", flush=True)
        pr.stdin.close()
    except BrokenPipeError:
        pass
    if pr.wait() != 0:
        sys.exit("[LOI] ffmpeg that bai (xem thong bao o tren)")


def ghi_timeline(d):
    sc = [{"id": "mo-dau", "start": 0.0, "end": round(d.mo_dau["dai"], 3)}]
    for c in d.canh:
        sc.append({"id": f"m{c['i'] + 1:02d}", "ten": d.mon[c["i"]]["ten"], "start": round(c["start"], 3),
                   "end": round(c["start"] + c["dur"], 3)})
    sc.append({"id": "ket", "start": round(d.end_start, 3), "end": round(d.total, 3)})
    for s in sc:
        s["visual_start"] = s["start"]
        s["visual_duration"] = round(s["end"] - s["start"], 3)
    (d.proj / "timeline.json").write_text(json.dumps({"total": round(d.total, 3), "scenes": sc}, ensure_ascii=False, indent=1),
                                          encoding="utf-8")


def xuat_khung(d):
    out = d.proj / "qa/tien-bay"
    out.mkdir(parents=True, exist_ok=True)
    video = d.proj / d.cfg["video"]
    mo = [0.0 if not d.cfg.get("ngay") else 1.2, d.canh[0]["t0"] + 0.8, d.canh[0]["t0"] + 2.1, d.canh[d.dat_nhat]["t0"] + 3.5,
          d.end_start + d.t_total_line + 0.5, d.end_start + d.t_bars + 1.4]
    for t in mo:
        t = min(t, d.total - 0.1)
        nen = out / f"nen_{t:06.2f}.png"
        # khung goc tam: lay tu dau doan trung voi t (chi de xem bo cuc, khong phai khung that)
        src = d.cfg["ket"]["nen_tu"] if t >= d.end_start else d.cfg["mo_dau"]["tu"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{src}", "-i", str(video), "-frames:v", "1",
                        "-vf", f"scale={W}:{H}", str(nen)], check=True)
        base = Image.open(nen).convert("RGBA")
        base.alpha_composite(khung(d, t))
        base.convert("RGB").save(out / f"khung_{t:06.2f}.png")
        nen.unlink()
    print(f"Da ghi {len(mo)} khung lop phu vao {out}")


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in ("kiem", "khung", "dung"):
        sys.exit(__doc__)
    proj = Path(sys.argv[1]).resolve()
    cmd = sys.argv[2]
    cfg = doc_cau_hinh(proj)
    loi, canh_bao, tong = kiem(proj, cfg)
    for c in canh_bao:
        print(f"[CANH BAO] {c}")
    if loi:
        for l in loi:
            print(f"[LOI] {l}")
        sys.exit(1)
    print(f"[DAT] {len(cfg['mon'])} mon, tong {vnd(tong)}")
    if cmd == "kiem":
        return
    d = khoi_tao(proj, cfg, tong)
    if cmd == "khung":
        xuat_khung(d)
        return
    ra = proj / "renders/final_portrait.mp4"
    if "--ra" in sys.argv:
        i = sys.argv.index("--ra")
        if i + 1 >= len(sys.argv):
            sys.exit("[LOI] --ra can duong dan file ra")
        ra = Path(sys.argv[i + 1])
    ghi_timeline(d)
    tao_tieng(d)
    print(f"Tong {d.total:.2f} giay; {len(d.mon)} mon; nhom: " + ", ".join(f"{g} {vnd(v)}" for g, v in d.nhom_tien.items()))
    dung(d, ra)
    print(f"Da render {ra}. Tiep theo: nhac_nen.py PROJECT --kieu <kieu>, chuan_am.sh, check_output.py")


if __name__ == "__main__":
    main()
