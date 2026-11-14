#!/usr/bin/env python3
"""Tao bo net chu viet tay tieng Viet (duong tam net don) cho assets/venet/venet-chu.js.

Dung:  python3 -I tools/venet_chu.py FONT_DIR OUT.js     (thuong goi qua tools/build_venet_chu.sh)
FONT_DIR chua patrick-hand-{latin,latin-ext,vietnamese}-400-normal.woff (goi npm @fontsource/patrick-hand).
Can: Pillow, numpy, scipy, fontTools.

Cach lam: ve moi ky tu to bang Pillow, lam mong (Zhang-Suen) ve duong tam 1 pixel, roi di theo duong tam nhu mot
cay but (bat dau o dau mut tren-trai, di theo huong muot nhat, nhac but khi het net). Y tuong va thuat toan lay tu
styles/sketchnote/demo/tools/skeleton.py cua Lemo-Opuscar (MIT, Copyright (c) 2026 Lemomo (LemoLab)); viet lai cho repo nay,
them: tieng Viet day du (dau thanh, dau mu, dau ngang, rau o u, dau nang), giu rieng cac dau cham roi (dau cham than,
dau nang), tra be rong tien cua tung ky tu.

Dau ra (module ES): { hw: nua be rong net (em), adv: {ky tu: be rong tien (em)}, g: {ky tu: [[x,y,x,y,...], ...]} }
toa do theo em, goc tai (mep trai, duong co chu), y huong xuong. Tat dinh: cung phong thi cung ket qua.
"""
import io
import json
import os
import sys

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

S = 220  # kich thuoc ve (pixel tren 1 em)
VI = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
EXTRA = "’…–"
CHARS = "".join(dict.fromkeys(
    "".join(chr(c) for c in range(33, 127)) + VI + VI.upper() + EXTRA))
NB = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def thin(img):
    """Zhang-Suen, img: mang bool."""
    I = np.pad(img.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            P2 = I[:-2, 1:-1]; P3 = I[:-2, 2:]; P4 = I[1:-1, 2:]; P5 = I[2:, 2:]
            P6 = I[2:, 1:-1]; P7 = I[2:, :-2]; P8 = I[1:-1, :-2]; P9 = I[:-2, :-2]
            nb = [P2, P3, P4, P5, P6, P7, P8, P9]
            B = sum(n.astype(int) for n in nb)
            seq = nb + [P2]
            A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(int) for i in range(8))
            if step == 0:
                c = (P2 * P4 * P6 == 0) & (P4 * P6 * P8 == 0)
            else:
                c = (P2 * P4 * P8 == 0) & (P2 * P6 * P8 == 0)
            m = (I[1:-1, 1:-1] == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if m.any():
                I[1:-1, 1:-1][m] = 0
                changed = True
        if not changed:
            break
    return I[1:-1, 1:-1].astype(bool)


def trace(sk):
    """Di theo duong tam nhu but: tra ve danh sach net, moi net la danh sach (x, y) pixel."""
    left = set(zip(*np.nonzero(sk.T)))

    def nbrs(p, pool):
        return [(p[0] + dx, p[1] + dy) for dx, dy in NB if (p[0] + dx, p[1] + dy) in pool]

    strokes, cur = [], None
    while left:
        ends = [p for p in left if len(nbrs(p, left)) <= 1]
        cand = ends if ends else list(left)
        if cur is None:
            key = lambda p: (p[0] * 1.0 + p[1] * 0.6, p)
        else:
            key = lambda p, c=cur: ((p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2, p)
        start = min(cand, key=key)
        path = [start]
        left.discard(start)
        d = None
        while True:
            nx = nbrs(path[-1], left)
            if not nx:
                break
            if d is None:
                q = min(nx, key=lambda p: (abs(p[0] - path[-1][0]) + abs(p[1] - path[-1][1]), p))
            else:
                q = max(nx, key=lambda p: (((p[0] - path[-1][0]) * d[0] + (p[1] - path[-1][1]) * d[1]) /
                                           max(1e-6, np.hypot(p[0] - path[-1][0], p[1] - path[-1][1])), p))
            for r in nbrs(path[-1], left):  # bac thang: lang gieng khac cung cham q la thua
                if r != q and abs(r[0] - q[0]) <= 1 and abs(r[1] - q[1]) <= 1:
                    left.discard(r)
            path.append(q)
            left.discard(q)
            k = min(len(path) - 1, 4)
            d = (path[-1][0] - path[-1 - k][0], path[-1][1] - path[-1 - k][1])
        cur = path[-1]
        near = bool(strokes) and np.hypot(path[0][0] - strokes[-1][-1][0], path[0][1] - strokes[-1][-1][1]) <= 4
        if len(path) >= 3 or not near:
            strokes.append(path)        # net that, hoac cham roi (dau cham than, dau nang): giu rieng
        else:
            strokes[-1].extend(path)    # vun vat sat dau net truoc: noi vao
    return strokes


def rdp(P, eps):
    if len(P) < 3:
        return P
    a, b = np.array(P[0], float), np.array(P[-1], float)
    ab = b - a
    L = np.hypot(*ab)
    d = [abs(ab[0] * (p[1] - a[1]) - ab[1] * (p[0] - a[0])) / L if L else np.hypot(*(np.array(p, float) - a)) for p in P]
    i = int(np.argmax(d))
    if d[i] > eps:
        return rdp(P[:i + 1], eps)[:-1] + rdp(P[i:], eps)
    return [P[0], P[-1]]


def main():
    fdir, outp = sys.argv[1], sys.argv[2]
    fonts = []
    for sub in ("latin", "latin-ext", "vietnamese"):
        tt = TTFont(os.path.join(fdir, f"patrick-hand-{sub}-400-normal.woff"))
        cmap = tt.getBestCmap()
        tt.flavor = None
        buf = io.BytesIO()
        tt.save(buf)
        fonts.append((cmap, ImageFont.truetype(io.BytesIO(buf.getvalue()), S)))
    g, adv, hws = {}, {}, []
    for ch in CHARS:
        for cmap, font in reversed(fonts):      # vietnamese > latin-ext > latin
            if ord(ch) in cmap:
                break
        else:
            print("thieu glyph:", ch)
            continue
        adv[ch] = round(font.getlength(ch) / S, 4)
        pad = S
        img = Image.new("L", (S * 3, S * 3), 0)
        ImageDraw.Draw(img).text((pad, pad * 2), ch, font=font, fill=255, anchor="ls")
        a = np.array(img) > 110
        if not a.any():
            continue
        dt = ndimage.distance_transform_edt(a)
        sk = thin(a)
        hws.append(np.percentile(dt[sk], 90))
        g[ch] = [[round(v, 3) for p in rdp(st, 0.9) for v in ((p[0] - pad) / S, (p[1] - pad * 2) / S)] for st in trace(sk)]
    out = {"hw": round(float(np.median(hws)) / S, 4), "adv": adv, "g": g}
    with open(outp, "w", encoding="utf-8") as f:
        f.write("// venet-chu.js: net chu viet tay tieng Viet cho venet.js (S.write). Sinh tu phong Patrick Hand (SIL OFL 1.1) bang\n"
                "// tools/venet_chu.py; khong sua tay, chay bash tools/build_venet_chu.sh. Xem README muc Ghi cong.\n"
                "export default " + json.dumps(out, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print(len(g), "ky tu, hw", out["hw"], "kich thuoc", os.path.getsize(outp))


if __name__ == "__main__":
    main()
