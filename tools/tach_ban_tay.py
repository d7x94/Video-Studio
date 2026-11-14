#!/usr/bin/env python3
"""Tach nen xanh anh ban tay cam but cho kieu ve-net.
Dung:  python3 tools/tach_ban_tay.py anh-goc.jpg [thu-muc-ra]
Dau vao: anh ban tay cam but tren nen xanh la thuan (#00FF00), dau but huong len tren trai, tay vao tu goc duoi phai.
Dau ra:  hand.png, hand-shadow.png (bong den cung hinh dang) va cac hang so can dan vao venet.js
         (HK, toa do dau but, da giac tay ao keo dai). Chi chay khi doi ban tay; ban tay mac dinh da co san trong assets/venet/.
Can: Pillow, numpy."""
import sys, os
import numpy as np
from PIL import Image, ImageFilter

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "."
K = 0.63   # ty le thu nho; handScale 1.2 (khung 1080) cho tay cao khoang 900 px
im = Image.open(src).convert("RGB")
a = np.asarray(im).astype(float)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
alpha = np.clip(1 - ((g - np.maximum(r, b)) - 25) / 70, 0, 1)
al = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(0.9))
rgb = np.dstack([r, np.minimum(g, np.maximum(r, b) + 2), b]).astype(np.uint8)
A = Image.fromarray(rgb, "RGB").convert("RGBA")
A.putalpha(al)
m = np.asarray(al) > 128
ys, xs = np.nonzero(m)
i = np.argmin(xs + ys * 0.3)
tipx, tipy = int(xs[i]), int(ys[i])          # dau but: diem day dac gan goc tren trai
cx, cy = max(0, tipx - 16), max(0, tipy - 16)
A = A.crop((cx, cy, A.width, A.height))
W, H = int(A.width * K), int(A.height * K)
A = A.resize((W, H), Image.LANCZOS)
tip = ((tipx - cx) * K, (tipy - cy) * K)
sh = Image.new("RGBA", A.size, (40, 30, 25, 0))
sh.putalpha(A.getchannel("A"))
os.makedirs(out, exist_ok=True)
A.save(os.path.join(out, "hand.png"))
sh.save(os.path.join(out, "hand-shadow.png"))
arr = np.asarray(A)
op = arr[..., 3] > 200
def edge(y):
    x = np.nonzero(op[y])[0]
    return int(x.min()), int(x.max())
yb = H - 3
l0, _ = edge(yb)
l1, _ = edge(yb - 57)
sl = (l0 - l1) / 57.0
print(f"anh {W}x{H}, dau but ({tip[0]:.2f}, {tip[1]:.2f}), canh trai tay ao x={l0} doc {sl:.3f}")
print("Tay ao keo dai: do canh phai thu cong o vai hang gan cuoi (xem ve-net.md, muc Ban tay), roi sua points cua polygon trong venet.js")
