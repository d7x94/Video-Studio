#!/usr/bin/env python3
"""Chuyen chuyen dong mocap CMU (BVH) thanh clip 2D cho tay chan que cua nhan vat chibi.

Dung:
  python3 tools/mocap/bvh2que.py                 # tai (neu thieu), kiem sha256, chuyen moi clip trong catalog.json,
                                                 # ghi video-studio/assets/chibi/src/mocap-clips.ts
  python3 tools/mocap/bvh2que.py --preview DIR   # them anh xem truoc tung clip (nguoi que) vao DIR
  python3 tools/mocap/bvh2que.py --probe 79_81 [--preview DIR]   # xem thu mot file chua co trong catalog

Nguon: ban BVH cua CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), qua ban chep
github.com/una-dinosauria/cmu-mocap ghim theo ma commit trong catalog.json. Moi file ghi kich thuoc va
sha256; khong khop thi dung lai. File BVH chi luu tam o ~/.cache/video-studio-mocap, khong dua vao git.

Cach chieu: nhan vat chibi nhin chinh dien, nen moi khung hinh duoc chieu len mat phang truoc cua
chinh nguoi dien (truc ngang = huong hong trai sang hong phai, lam muot 0,5 giay; truc dung = phuong
thang dung). Nguoi dien quay di dau thi hinh van la nhin chinh dien. Tay phai nguoi dien la tay truoc
(side = 1) cua chibi.

Du lieu moi khung (don vi hinh que, y huong xuong, lam tron so nguyen, 15 khung/giay):
  tay sau, tay truoc: khuyu (x, y), ban tay (x, y) tinh tu vai; da xoay nguoc theo do nghieng than
  chan trai, chan phai: dau goi (x, y), ban chan (x, y) tinh tu hong
  goc: dx, dy cua hong (dy duong la ha xuong so voi dung thang), nghieng than (do, x10), cui ve truoc (do)
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CATALOG = Path(__file__).with_name("catalog.json")
OUT_TS = ROOT / "video-studio/assets/chibi/src/mocap-clips.ts"
CACHE = Path.home() / ".cache/video-studio-mocap"

ARM_LEN = 80.0      # ARM_A + ARM_B trong que.ts
LEG_LEN = 86.0      # hong (y -92) toi mat ban chan (y -6) trong que.ts
SHOULDER_X = 40.0   # vai que o x = +-40 (que.ts)
# Diem dich khi dua tay len dau, tinh tu vai que cung phia (x huong ra ngoai, y huong xuong).
# Do tren anh chup chibi: mieng giua mat, cao hon vai khoang 44; tai o mep dau, cao hon vai khoang 66.
FACE_TARGET = {"mieng": (-SHOULDER_X, -44.0), "tai": (18.0, -66.0)}
FPS_OUT = 15


# ---------------- BVH ----------------
def parse_bvh(text):
    tok = text.split()
    i = 0
    joints = []          # (ten, cha, offset, kenh)
    stack = []
    while tok[i] != "MOTION":
        t = tok[i]
        if t in ("ROOT", "JOINT"):
            joints.append([tok[i + 1], stack[-1] if stack else -1, None, []])
            i += 2
        elif t == "End":
            joints.append(["_end", stack[-1], None, []])
            i += 2
        elif t == "{":
            stack.append(len(joints) - 1)
            i += 1
        elif t == "}":
            stack.pop()
            i += 1
        elif t == "OFFSET":
            joints[stack[-1]][2] = np.array([float(x) for x in tok[i + 1:i + 4]])
            i += 4
        elif t == "CHANNELS":
            n = int(tok[i + 1])
            joints[stack[-1]][3] = tok[i + 2:i + 2 + n]
            i += 2 + n
        else:
            i += 1
    i += 1
    assert tok[i] == "Frames:"
    nf = int(tok[i + 1])
    ft = float(tok[i + 4])
    data = np.array(tok[i + 5:], dtype=float)
    nch = sum(len(j[3]) for j in joints)
    data = data[: nf * nch].reshape(nf, nch)
    return joints, data, ft


def rot(axis, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    if axis == "X":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "Y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def fk(joints, data, frames):
    """Vi tri the gioi cua moi khop o cac khung chon. Tra ve {ten: mang (n, 3)}."""
    names = [j[0] for j in joints]
    out = np.zeros((len(frames), len(joints), 3))
    for fi, f in enumerate(frames):
        row = data[f]
        k = 0
        R = [None] * len(joints)
        P = [None] * len(joints)
        for ji, (name, parent, off, ch) in enumerate(joints):
            pos = off.copy()
            M = np.eye(3)
            for c in ch:
                v = row[k]
                k += 1
                if c.endswith("position"):
                    pos["XYZ".index(c[0])] = v if parent < 0 else pos["XYZ".index(c[0])]
                else:
                    M = M @ rot(c[0], v)
            if parent < 0:
                R[ji], P[ji] = M, pos
            else:
                P[ji] = P[parent] + R[parent] @ off
                R[ji] = R[parent] @ M
            out[fi, ji] = P[ji]
    return {n: out[:, i] for i, n in enumerate(names) if n != "_end"}


def bone_len(joints, child):
    for name, _, off, _ in joints:
        if name == child:
            return float(np.linalg.norm(off))
    raise KeyError(child)


# ---------------- chieu 2D ----------------
def smooth(a, n):
    if n <= 1:
        return a
    k = np.ones(n) / n
    pad = np.pad(a, ((n // 2, n - 1 - n // 2), (0, 0)), mode="edge")
    return np.stack([np.convolve(pad[:, d], k, mode="valid") for d in range(a.shape[1])], axis=1)


def convert(bvh_text, t0, t1, face=None, step_sec=1 / FPS_OUT):
    joints, data, ft = parse_bvh(bvh_text)
    nf = data.shape[0]
    f0 = max(1, int(round(t0 / ft)) + 1)        # khung 0 la tu the chu T them vao, bo qua
    f1 = min(nf - 1, int(round(t1 / ft)) + 1) if t1 else nf - 1
    frames = list(range(f0, f1 + 1, max(1, int(round(step_sec / ft)))))
    J = fk(joints, data, frames)
    up = np.array([0.0, 1.0, 0.0])

    lat = J["RightUpLeg"] - J["LeftUpLeg"]
    lat[:, 1] = 0
    lat = smooth(lat, max(1, int(round(0.5 * FPS_OUT))))
    lat /= np.linalg.norm(lat, axis=1, keepdims=True)
    fwd = np.cross(up, lat)                       # huong mat nguoi dien
    # kiem tra chieu: mui ban chan phai o phia truoc
    toe = (J["LeftToeBase"] + J["RightToeBase"]) / 2 - (J["LeftFoot"] + J["RightFoot"]) / 2
    if np.mean(np.sum(toe * fwd, axis=1)) < 0:
        fwd = -fwd

    def proj(v):            # (n,3) -> (n,2): x = phia tay phai nguoi dien, y huong xuong
        return np.stack([np.sum(v * lat, axis=1), -v[:, 1]], axis=1)

    arm_s = ARM_LEN / (bone_len(joints, "LeftForeArm") + bone_len(joints, "LeftHand"))
    leg_up = bone_len(joints, "LeftLeg") + bone_len(joints, "LeftFoot")
    leg_s = LEG_LEN / leg_up

    hips = (J["LeftUpLeg"] + J["RightUpLeg"]) / 2
    chest = (J["LeftArm"] + J["RightArm"]) / 2
    spine = chest - hips
    tilt = np.degrees(np.arctan2(np.sum(spine * lat, axis=1), spine[:, 1]))       # nghieng sang phai duong
    lean = np.degrees(np.arctan2(np.sum(spine * fwd, axis=1), spine[:, 1]))       # cui ve truoc duong
    tilt = np.clip(tilt * 0.6, -12, 12)       # nghieng vua phai: than chibi ngan, nghieng nhieu trong nhu nga
    lean = np.clip(lean, -15, 60)

    # mat dat: mat ca chan thap nhat trong clip; dung thang khi hong cach mat ca dung chieu dai chan
    ankle_y = np.minimum(J["LeftFoot"][:, 1], J["RightFoot"][:, 1])
    ground = np.percentile(ankle_y, 5)
    dy = (leg_up - (hips[:, 1] - ground)) * leg_s
    lat0 = np.sum((hips - hips[0]) * lat, axis=1)
    dx = (lat0 - np.median(lat0)) * leg_s

    def rot2(v, deg):       # xoay (n,2) mot goc deg (theo chieu man hinh)
        r = np.radians(deg)[:, None]
        c, s = np.cos(r), np.sin(r)
        return np.concatenate([v[:, :1] * c + v[:, 1:] * s, -v[:, :1] * s + v[:, 1:] * c], axis=1)

    # Dau chibi to gap nhieu lan nguoi that: tay dua len mat (an, uong, danh rang) theo dung ti le thi
    # chi toi nguc. Khi ban tay o gan dau nguoi dien, keo ban tay (va mot nua khuyu) ve phia mat chibi.
    arm_len = bone_len(joints, "LeftForeArm") + bone_len(joints, "LeftHand")
    cols = []
    for side, sgn in (("Left", -1), ("Right", 1)):  # tay sau (trai), tay truoc (phai)
        sh = J[f"{side}Arm"]
        e = rot2(proj(J[f"{side}ForeArm"] - sh) * arm_s, -tilt)
        h = rot2(proj(J[f"{side}Hand"] - sh) * arm_s, -tilt)
        head_m = rot2(proj(J["Head"] - sh) * arm_s, -tilt)
        tx, ty = FACE_TARGET.get(face or "mieng")
        face_c = np.array([sgn * tx, ty])
        rel = (J[f"{side}Hand"] - J["Head"]) / arm_len
        dist = np.linalg.norm(rel, axis=1)
        # chi keo voi clip dong tac dua tay len dau (catalog "face": "mieng" hoac "tai"); tay om nguc thi giu nguyen
        wf = (np.clip((1.0 - dist) / 0.3, 0, 1) * (1.0 if face else 0.0))[:, None]
        wf = wf * wf * (3 - 2 * wf)
        h2 = face_c + (h - head_m) * 0.35          # gan mat: giu huong, thu nho khoang cach toi mat
        shift = (h2 - h) * wf
        cols += [e + shift * 0.5, h + shift]
    # Dang dung rieng cua nguoi dien (chan dang rong, mot chan chech ra) trong khong dep tren chibi:
    # dich ban chan ve dang dung cua que (ban chan lech hong 2 don vi ra ngoai) theo trung vi ca clip,
    # giu nguyen bien dong (buoc, nhay, nhun).
    for side, sgn in (("Left", -1), ("Right", 1)):
        hp = J[f"{side}UpLeg"]
        k = proj(J[f"{side}Leg"] - hp) * leg_s
        fo = proj(J[f"{side}Foot"] - hp) * leg_s
        off = np.median(fo[:, 0]) - sgn * 2
        k[:, 0] -= off / 2
        fo[:, 0] -= off
        cols += [k, fo]
    cols += [np.stack([dx, dy], 1), np.stack([tilt * 10, lean], 1)]
    arr = np.rint(np.concatenate(cols, axis=1)).astype(int)
    return arr, len(frames) * step_sec


# ---------------- xem truoc ----------------
def preview(arr, path, title):
    from PIL import Image, ImageDraw
    n = arr.shape[0]
    pick = np.linspace(0, n - 1, min(n, 12)).astype(int)
    W, H = 150, 260
    img = Image.new("RGB", (W * len(pick), H + 20), "white")
    d = ImageDraw.Draw(img)
    d.text((4, 2), title, fill="black")
    for k, fi in enumerate(pick):
        r = arr[fi]
        ox, base = W * k + W / 2 + r[16] * 0.8, 230
        hipy = base - 86 * 0.8 + r[17] * 0.8
        P = lambda x, y, sx, sy: (sx + x * 0.8, sy + y * 0.8)
        sh_y = hipy - 70 * 0.8
        d.line([(ox, hipy), (ox, sh_y)], fill="black", width=3)
        d.ellipse([ox - 18, sh_y - 50, ox + 18, sh_y - 14], outline="black", width=3)
        for a, side in ((0, -1), (4, 1)):
            sx = ox + side * 32 * 0.8
            col = "red" if side > 0 else "gray"
            d.line([(sx, sh_y), P(r[a], r[a + 1], sx, sh_y), P(r[a + 2], r[a + 3], sx, sh_y)], fill=col, width=3)
        for a, side in ((8, -1), (12, 1)):
            hx = ox + side * 12 * 0.8
            col = "red" if side > 0 else "gray"
            d.line([(hx, hipy), P(r[a], r[a + 1], hx, hipy), P(r[a + 2], r[a + 3], hx, hipy)], fill=col, width=3)
        d.line([(W * k, base + 6), (W * k + W, base + 6)], fill="#bbb")
        d.text((W * k + 4, base + 10), f"{fi / FPS_OUT:.1f}s", fill="black")
    img.save(path)


# ---------------- tai va kiem ----------------
def fetch(cat, item):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{item['file']}.bvh"
    sub = item["file"].split("_")[0].zfill(3)
    url = cat["url"].format(commit=cat["commit"], sub=sub, file=item["file"])
    if not path.exists():
        r = subprocess.run(["curl", "-fsSL", "--retry", "2", "-o", str(path), url])
        if r.returncode:
            sys.exit(f"[LOI] khong tai duoc {url}")
    raw = path.read_bytes()
    got = (len(raw), hashlib.sha256(raw).hexdigest())
    if "sha256" in item and (got[0] != item["size"] or got[1] != item["sha256"]):
        path.unlink()
        sys.exit(f"[LOI] {item['file']}: kich thuoc/sha256 khong khop catalog ({got})")
    return raw.decode("ascii"), got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", help="thu muc ghi anh xem truoc")
    ap.add_argument("--probe", help="ma file CMU (vd 79_81), chi xem thu")
    ap.add_argument("--t0", type=float, default=0)
    ap.add_argument("--t1", type=float, default=0)
    ap.add_argument("--face", choices=["mieng", "tai"], help="keo ban tay ve mieng hoac tai chibi khi gan dau")
    a = ap.parse_args()
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    if a.probe:
        text, got = fetch(cat, {"file": a.probe})
        arr, dur = convert(text, a.t0, a.t1, a.face)
        print(f"{a.probe}: {dur:.1f}s, size {got[0]}, sha256 {got[1]}")
        if a.preview:
            Path(a.preview).mkdir(parents=True, exist_ok=True)
            preview(arr, Path(a.preview) / f"{a.probe}.png", f"{a.probe} {a.t0}-{a.t1 or 'het'}")
        return

    lines = ["// mocap-clips.ts: SINH TU DONG boi tools/mocap/bvh2que.py tu tools/mocap/catalog.json. Khong sua tay.",
             "// Nguon: CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), ban BVH cua B. Hahne,",
             f"// chep tai github.com/una-dinosauria/cmu-mocap commit {cat['commit']}.",
             "// The data used in this project was obtained from mocap.cs.cmu.edu.",
             "// The database was created with funding from NSF EIA-0196217.",
             "// d: chuoi so cach nhau dau phay (de goi build giu tren mot dong); mocap.ts tach thanh mang khi dung lan dau.",
             "export interface MocapClip { fps: number; loop: boolean; n: number; d: string }",
             f"export const MOCAP_STRIDE = 20;",
             "export const MOCAP: Record<string, MocapClip> = {"]
    for item in cat["clips"]:
        text, got = fetch(cat, item)
        if "sha256" not in item:
            sys.exit(f"[LOI] {item['id']}: catalog thieu size/sha256 (gia tri dang tai: {got})")
        arr, dur = convert(text, item["t0"], item["t1"], item.get("face"))
        lines.append(f"  '{item['id']}': {{ fps: {FPS_OUT}, loop: {str(item.get('loop', False)).lower()}, "
                     f"n: {arr.shape[0]}, d: '{','.join(map(str, arr.flatten()))}' }},")
        print(f"{item['id']:<14} {item['file']:<6} {dur:4.1f}s {arr.shape[0]} khung")
        if a.preview:
            Path(a.preview).mkdir(parents=True, exist_ok=True)
            preview(arr, Path(a.preview) / f"{item['id']}.png", f"{item['id']} ({item['file']})")
    lines.append("};")
    OUT_TS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Da ghi {OUT_TS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
