#!/usr/bin/env python3
"""Tieng dong (hieu ung am thanh) tu tong hop bang numpy, dat theo moc canh hoac theo mot tu trong loi doc.

Dung:
  python3 tieng_dong.py PROJECT                   # doc truong "sfx" cua tung canh trong scenes.json -> audio/tieng-dong.wav
  python3 tieng_dong.py PROJECT --muc -18         # dinh am luong (dBFS), mac dinh -16
  python3 tieng_dong.py --danh-sach               # in cac loai tieng
  python3 tieng_dong.py --nghe-thu OUT.wav        # moi loai mot lan, cach nhau 1 giay, de nghe thu
Sau do chay nhac_nen.py nhu thuong le: co audio/tieng-dong.wav thi tu tron vao (khong giam theo loi doc).

Truong "sfx" cua canh trong scenes.json (moi muc mot tieng):
  {"loai": "vut", "luc": 0.3}                  luc: giay tinh tu dau hinh canh (T.<id>), cung moc voi tween
  {"loai": "ding", "tu": "xa phong"}           tu: tieng dong vang dung luc cum tu nay duoc doc (trong canh do;
                                               khong phan biet dau va hoa thuong; moc tu moc_tu.py)
  {"loai": "nuoc", "luc": 0, "dai": 3.5}       dai: giay, cho tieng keo dai (buoc-chan, vo-tay, nuoc, tim-dap, dong-ho)
  them "muc" (dB cong them, vd -6) va "pan" (-1 trai .. 1 phai) neu can.
"tu" va "luc" cung co thi lay moc cua tu roi cong them "luc".

Moi tieng deu la tong hop (song sin, nhieu trang loc), khong dung mau am thanh hay thu vien ngoai.
Tat dinh: cung PROJECT va seed thi ra cung mot file. Chua duoc nghe thu bang tai nguoi tren video that:
nghe lai va chinh "muc" truoc khi giao.
"""
import argparse
import hashlib
import json
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
TAU = 2 * np.pi


# ---------------------------------------------------------------- cong cu
def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def bandpass(x, lo, hi, edge=0.25):
    n = len(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    w = max((hi - lo) * edge, 1.0)
    m = np.minimum(np.clip((f - (lo - w)) / (2 * w), 0, 1), np.clip(((hi + w) - f) / (2 * w), 0, 1))
    return np.fft.irfft(np.fft.rfft(x) * m, n)


def norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)


def decay(n, tau):
    return np.exp(-np.arange(n) / SR / tau)


def attack(x, a=0.004):
    k = min(len(x), max(1, int(a * SR)))
    x = x.copy()
    x[:k] *= np.linspace(0, 1, k)
    return x


def fade_out(x, r=0.03):
    k = min(len(x), max(1, int(r * SR)))
    x = x.copy()
    x[-k:] *= np.linspace(1, 0, k)
    return x


def bell(f0, dur, ratios=(1, 2.76, 5.4, 8.93), amps=(1, 0.45, 0.25, 0.12), tau=0.5):
    t = t_axis(dur)
    x = sum(a * np.sin(TAU * f0 * r * t) * np.exp(-t / (tau / (1 + 0.6 * i)))
            for i, (r, a) in enumerate(zip(ratios, amps)))
    return attack(norm(x), 0.002)


def thump(f0, dur, rng, noise=0.3, tau=0.05):
    t = t_axis(dur)
    f = f0 * (1 + 0.8 * np.exp(-t / 0.015))
    x = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / tau)
    x += noise * bandpass(rng.standard_normal(len(t)), 60, 900) * np.exp(-t / (tau * 0.4))
    return attack(norm(x), 0.001)


# ---------------------------------------------------------------- cac loai tieng: (ham, keo dai?, mo ta)
def s_vut(rng, dai):
    dur = 0.45
    n = int(dur * SR)
    x = rng.standard_normal(n + 2048)
    out = np.zeros(n + 2048)
    win, hop = np.hanning(2048), 512
    f = np.fft.rfftfreq(2048, 1 / SR)
    for j in range(0, n, hop):      # loc chong lap (khong co mep cat): tam loc quet len roi xuong
        c = 500 + 2600 * np.sin(np.pi * min(j / n, 1))
        m = np.exp(-0.5 * (np.log(np.maximum(f, 1) / c) / 0.45) ** 2)
        out[j:j + 2048] += np.fft.irfft(np.fft.rfft(x[j:j + 2048] * win) * m, 2048) * win
    out = out[1024:1024 + n]
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6
    return norm(out * env)


def s_bop(rng, dai):
    t = t_axis(0.11)
    f = 300 + 650 * np.exp(-t / 0.025)
    return attack(norm(np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.04)), 0.001)


def s_cham(rng, dai):
    n = int(0.03 * SR)
    x = bandpass(rng.standard_normal(n), 1800, 6000) * decay(n, 0.004)
    return norm(x + 0.5 * np.sin(TAU * 2400 * np.arange(n) / SR) * decay(n, 0.006))


def s_ding(rng, dai):
    return bell(1318.5, 1.4, tau=0.6)


def s_dung(rng, dai):
    a, b = bell(1046.5, 1.0, tau=0.45), bell(1568.0, 1.3, tau=0.6)
    out = np.zeros(int(0.12 * SR) + len(b))
    out[: len(a)] += 0.8 * a
    out[int(0.12 * SR):] += b
    return norm(out)


def s_sai(rng, dai):
    out = []
    for f in (220, 175):
        t = t_axis(0.17)
        x = np.sign(np.sin(TAU * f * t)) * 0.6 + np.sin(TAU * f * 2 * t) * 0.3
        out.append(fade_out(attack(bandpass(x, 80, 2500) * (1 - 0.4 * t / 0.17), 0.003), 0.02))
    return norm(np.concatenate(out))


def s_chuong(rng, dai):
    out = np.zeros(int(1.6 * SR))
    for i, f in enumerate((1046.5, 1318.5, 1568.0)):
        b = bell(f, 1.2, tau=0.5)
        k = int(i * 0.09 * SR)
        out[k:k + len(b)] += b * (0.9 - 0.15 * i)
    return norm(out)


def s_ting(rng, dai):
    out = np.zeros(int(0.9 * SR))
    for i, f in enumerate((2093, 2637, 3136, 4186)):
        b = bell(f, 0.5, ratios=(1, 2.0), amps=(1, 0.3), tau=0.18)
        k = int(i * 0.06 * SR)
        out[k:k + len(b)] += b * 0.7
    return norm(out)


def s_go_cua(rng, dai):
    out = np.zeros(int(0.75 * SR))
    for i in range(3):
        n = int(0.12 * SR)
        t = np.arange(n) / SR
        x = (np.sin(TAU * 190 * t) * np.exp(-t / 0.03) + 0.6 * np.sin(TAU * 430 * t) * np.exp(-t / 0.018)
             + 0.4 * bandpass(rng.standard_normal(n), 300, 2500) * np.exp(-t / 0.006))
        k = int(i * 0.19 * SR)
        out[k:k + n] += x * (1 - 0.1 * i)
    return norm(out)


def s_giay(rng, dai):
    n = int(0.45 * SR)
    x = bandpass(rng.standard_normal(n), 1500, 9000)
    gate = np.zeros(n)
    for _ in range(26):                     # nhung tieng lach tach ngan
        k = int(rng.uniform(0, n - 900))
        gate[k:k + 900] += decay(900, 0.004) * rng.uniform(0.3, 1)
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 0.7
    return norm(x * (0.25 + gate) * env)


def s_buoc_chan(rng, dai):
    dai = dai or 2.0
    out = np.zeros(int((dai + 0.2) * SR))
    k, i = 0.0, 0
    while k < dai:
        x = thump(70 + rng.uniform(-6, 6), 0.16, rng, noise=0.6, tau=0.035) * rng.uniform(0.75, 1.0)
        j = int(k * SR)
        out[j:j + len(x)] += x[: len(out) - j]
        k += 0.48 + rng.uniform(-0.03, 0.03)
        i += 1
    return norm(out)


def s_vo_tay(rng, dai):
    dai = dai or 2.5
    n = int(dai * SR)
    out = np.zeros(n + int(0.05 * SR))
    for _ in range(int(dai * 45)):          # khoang 45 tieng vo moi giay, nhieu nguoi
        m = int(0.03 * SR)
        c = rng.uniform(900, 2400)
        x = bandpass(rng.standard_normal(m), c * 0.6, c * 1.6) * decay(m, 0.006)
        j = int(rng.uniform(0, n))
        out[j:j + m] += x * rng.uniform(0.3, 1)
    env = np.minimum(1, np.linspace(0, dai, len(out)) / 0.25) * np.clip((dai - np.linspace(0, dai, len(out))) / 0.8, 0, 1)
    return norm(out * env)


def s_nuoc(rng, dai):
    dai = dai or 3.0
    n = int(dai * SR)
    x = bandpass(rng.standard_normal(n), 500, 7000)
    k = max(2, int(dai * 30))
    mod = np.interp(np.linspace(0, k - 1, n), np.arange(k), rng.random(k))
    out = x * (0.6 + 0.4 * mod)
    for _ in range(int(dai * 25)):          # giot nuoc nho
        m = int(0.02 * SR)
        f = rng.uniform(900, 2200)
        t = np.arange(m) / SR
        j = int(rng.uniform(0, n - m))
        out[j:j + m] += 0.8 * np.sin(TAU * np.cumsum(f * (1 + 2 * t / 0.02)) / SR) * np.exp(-t / 0.006)
    env = np.minimum(1, np.linspace(0, dai, n) / 0.3) * np.clip((dai - np.linspace(0, dai, n)) / 0.5, 0, 1)
    return norm(out * env)


def s_tim_dap(rng, dai):
    dai = dai or 2.5
    out = np.zeros(int((dai + 0.3) * SR))
    k = 0.0
    while k < dai:
        for off, g in ((0.0, 1.0), (0.17, 0.7)):        # "thinh - thich"
            x = thump(52, 0.2, rng, noise=0.1, tau=0.06) * g
            j = int((k + off) * SR)
            out[j:j + len(x)] += x[: len(out) - j]
        k += 60 / 72
    return norm(out)


def s_dong_ho(rng, dai):
    dai = dai or 3.0
    out = np.zeros(int((dai + 0.1) * SR))
    k, i = 0.0, 0
    while k < dai:
        n = int(0.02 * SR)
        f = 3200 if i % 2 == 0 else 2600
        x = (bandpass(rng.standard_normal(n), f * 0.7, f * 1.3) + np.sin(TAU * f * np.arange(n) / SR)) * decay(n, 0.003)
        j = int(k * SR)
        out[j:j + n] += x
        k += 0.5
        i += 1
    return norm(out)


LOAI = {
    "vut":       (s_vut, False, "vut gio khi chuyen canh, vat bay vao"),
    "bop":       (s_bop, False, "bop nhe khi chu, bieu tuong hien ra"),
    "cham":      (s_cham, False, "tieng cham, bam nut, dau tich"),
    "ding":      (s_ding, False, "mot tieng chuong trong, nhan manh mot y"),
    "dung":      (s_dung, False, "hai not di len: dung, hoan thanh"),
    "sai":       (s_sai, False, "hai not tram di xuong: sai, can tranh"),
    "chuong":    (s_chuong, False, "chuong thong bao ba not"),
    "ting":      (s_ting, False, "lap lanh: sach se, sang bong"),
    "go-cua":    (s_go_cua, False, "go cua ba tieng"),
    "giay":      (s_giay, False, "sot soat giay, lat ho so"),
    "buoc-chan": (s_buoc_chan, True, "buoc chan deu (dai mac dinh 2 giay)"),
    "vo-tay":    (s_vo_tay, True, "vo tay dong nguoi (dai mac dinh 2,5 giay)"),
    "nuoc":      (s_nuoc, True, "nuoc chay tu voi (dai mac dinh 3 giay)"),
    "tim-dap":   (s_tim_dap, True, "tim dap 72 nhip/phut (dai mac dinh 2,5 giay)"),
    "dong-ho":   (s_dong_ho, True, "dong ho tich tac (dai mac dinh 3 giay)"),
}
# muc rieng tung loai (dB) de cac tieng nghe can nhau truoc khi chuan dinh chung
GAIN = {"vut": -4, "bop": -6, "cham": -8, "ding": -6, "dung": -6, "sai": -7, "chuong": -6, "ting": -8,
        "go-cua": -3, "giay": -6, "buoc-chan": -4, "vo-tay": -6, "nuoc": -9, "tim-dap": -2, "dong-ho": -9}


def place(buf, sig, at, gain_db, pan):
    i = int(round(at * SR))
    if i >= buf.shape[1] or i + len(sig) <= 0:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    sig = sig[: buf.shape[1] - i] * 10 ** (gain_db / 20)
    pan = max(-1.0, min(1.0, pan))
    buf[0, i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2)
    buf[1, i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2)


def write_wav(path, buf):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(buf.T, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def word_time(moc, sid, phrase):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import moc_tu
    sc = next((x for x in moc["scenes"] if x["id"] == sid), None)
    return moc_tu.find({"scenes": [sc]}, phrase) if sc else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?")
    ap.add_argument("--muc", type=float, default=-16.0, help="dinh am luong tieng dong (dBFS), mac dinh -16")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--danh-sach", action="store_true")
    ap.add_argument("--nghe-thu", metavar="OUT.wav")
    a = ap.parse_args()

    if a.danh_sach:
        for k, (_, long_, mo_ta) in LOAI.items():
            print(f"{k:10s} {'(dai)' if long_ else '     '} {mo_ta}")
        return
    if a.nghe_thu:
        rng = np.random.default_rng(a.seed or 1)
        parts = [LOAI[k][0](rng, 2.0) * 10 ** (GAIN[k] / 20) for k in LOAI]
        buf = np.zeros((2, sum(len(p) + SR for p in parts)))
        at = 0.5
        for p in parts:
            place(buf, p, at, 0, 0)
            at += len(p) / SR + 1.0
        buf *= 10 ** (a.muc / 20) / (np.max(np.abs(buf)) + 1e-9)
        write_wav(Path(a.nghe_thu), buf)
        print(f"Nghe thu {len(LOAI)} loai theo thu tu: {', '.join(LOAI)} -> {a.nghe_thu}")
        return
    if not a.project:
        ap.error("can thu muc du an")

    p = Path(a.project)
    try:
        tl = json.loads((p / "timeline.json").read_text(encoding="utf-8"))
        scenes = json.loads((p / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    except (OSError, ValueError, KeyError) as e:
        sys.exit(f"[LOI] Khong doc duoc timeline.json hoac scenes.json: {e}")
    vstart = {sc["id"]: float(sc["visual_start"]) for sc in tl["scenes"]}
    total = float(tl["total"])
    seed = a.seed if a.seed is not None else int(hashlib.sha256(p.resolve().name.encode()).hexdigest()[:8], 16) % 10000
    rng = np.random.default_rng(seed)
    moc = None
    buf = np.zeros((2, int((total + 0.5) * SR)))
    errors, placed = [], []
    for sc in scenes:
        for i, q in enumerate(sc.get("sfx") or []):
            where = f"{sc['id']}.sfx[{i}]"
            k = q.get("loai")
            if k not in LOAI:
                errors.append(f"{where}: loai \"{k}\" khong co (xem --danh-sach)")
                continue
            if sc["id"] not in vstart:
                errors.append(f"{where}: canh khong co trong timeline.json (chay lai tts.py)")
                continue
            t = vstart[sc["id"]] + float(q.get("luc", 0))
            if q.get("tu"):
                if moc is None:
                    sys.path.insert(0, str(Path(__file__).resolve().parent))
                    import moc_tu
                    moc = moc_tu.load_or_build(p)
                wt = word_time(moc, sc["id"], q["tu"])
                if wt is None:
                    errors.append(f"{where}: khong thay \"{q['tu']}\" trong loi doc cua canh")
                    continue
                t = wt + float(q.get("luc", 0))
            dai = float(q["dai"]) if q.get("dai") else 0.0
            if t >= total:
                errors.append(f"{where}: moc {t:.2f}s sau khi video het ({total:.2f}s)")
                continue
            sig = LOAI[k][0](rng, dai)
            place(buf, sig, t, GAIN[k] + float(q.get("muc", 0)), float(q.get("pan", 0)))
            placed.append((t, f"{t:6.2f}s {sc['id']} {k}" + (f" ({dai:.1f}s)" if LOAI[k][1] else "") +
                          (f" tai \"{q['tu']}\"" if q.get("tu") else "")))
    if errors:
        for e in errors:
            print("[LOI]", e)
        sys.exit(1)
    if not placed:
        sys.exit("[LOI] Khong canh nao co truong \"sfx\" trong scenes.json")
    buf *= 10 ** (a.muc / 20) / (np.max(np.abs(buf)) + 1e-9)
    out = p / "audio" / "tieng-dong.wav"
    write_wav(out, buf)
    for _, line in sorted(placed):
        print(line)
    print(f"Tieng dong: {len(placed)} tieng, seed {seed}, dinh {a.muc} dBFS -> {out}")


if __name__ == "__main__":
    main()
