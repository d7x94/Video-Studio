#!/usr/bin/env python3
"""Tieng but ve cho kieu ve-net: tong hop bang code tieng but chay tren giay, dung theo tung net ve.

Dung:
  bash ve_net_kiem_tra.sh build/portrait --json PROJECT/venet-report.json     # lay thoi diem tung net tu composition
  python3 tieng_but.py PROJECT                                                # ghi PROJECT/audio/hieu-ung.wav
  python3 tieng_but.py PROJECT --bao-cao khac.json --muc -22 --seed 3

Doc PROJECT/venet-report.json (moi canh co "ev": [{t, d, k}], t la giay tinh tu dau video, d la do dai net,
k la "stroke" | "write" | "wipe") va PROJECT/timeline.json (lay tong thoi luong). Ghi audio/hieu-ung.wav
(48 kHz, 2 kenh). nhac_nen.py tu tron file nay vao video khi no ton tai (khong qua bo nen theo loi doc,
nen giu nho; mac dinh dinh -18 dBFS, khoang 11 dB duoi giong doc).

Cac tieng (tat ca la nhieu trang loc bang numpy, khong dung mau am thanh ben ngoai):
  stroke: cay but ma sat tren giay, bao do theo nua song sin (xuong luc ra dau va cuoi net), chap chon nhe
  write:  but viet chu, ngat thanh tung dot ngan (moi dot la mot net chu) bien do ngau nhien
  wipe:   but da quang to vet, nhieu rong va tram hon, em hon
  moi net bat dau bang mot tieng cham dau but rat ngan; moi canh moi co tieng lat giay nhe
Tat dinh: cung PROJECT, bao cao va seed thi ra cung mot file (seed mac dinh lay tu ten thu muc du an).
Day la am thanh tong hop, chua duoc nghe thu bang tai nguoi: nghe lai va chinh --muc truoc khi giao.
"""
import argparse
import hashlib
import json
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000


def bandpass(x, lo, hi, edge=0.25):
    """Loc thong dai bang FFT; bo mep mem (ty le edge cua be rong dai) de khong keu."""
    n = len(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    m = np.zeros_like(f)
    w = max((hi - lo) * edge, 1.0)
    up = np.clip((f - (lo - w)) / (2 * w), 0, 1)
    dn = np.clip(((hi + w) - f) / (2 * w), 0, 1)
    m = np.minimum(up, dn)
    return np.fft.irfft(np.fft.rfft(x) * m, n)


def smooth_noise(rng, n, hz):
    """Nhieu cham (doi bien do) o khoang hz lan moi giay, 0..1."""
    k = max(2, int(n / SR * hz) + 2)
    pts = rng.random(k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)


def scratch(rng, dur, lo, hi, gate_hz=None):
    n = max(int(dur * SR), 64)
    x = bandpass(rng.standard_normal(n), lo, hi)
    x /= np.max(np.abs(x)) + 1e-9
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 0.6                      # nhac but o dau, nhac but o cuoi
    a = min(n, int(0.012 * SR))
    env[:a] *= np.linspace(0, 1, a)
    amp = 0.55 + 0.45 * smooth_noise(rng, n, 22)        # chap chon nhe nhu luc mui but di tren giay
    if gate_hz:                                         # chu viet: ngat thanh tung dot ngan
        g = smooth_noise(rng, n, gate_hz)
        amp *= np.clip((g - 0.28) / 0.5, 0.08, 1) ** 1.3
    return x * env * amp


def tick(rng):
    n = int(0.012 * SR)
    x = np.diff(rng.standard_normal(n), prepend=0) * np.exp(-np.arange(n) / SR * 600)
    return x / (np.max(np.abs(x)) + 1e-9)


def swish(rng, dur=0.28):
    n = int(dur * SR)
    x = bandpass(rng.standard_normal(n), 300, 2200)
    x /= np.max(np.abs(x)) + 1e-9
    t = np.linspace(0, 1, n)
    return x * np.sin(np.pi * t) ** 2


def add(buf, sig, at, gain, pan):
    i = int(round(at * SR))
    if i >= buf.shape[1] or i + len(sig) <= 0:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    sig = sig[: buf.shape[1] - i] * gain
    buf[0, i:i + len(sig)] += sig * (1 - pan) / 2 * 2 ** 0.5
    buf[1, i:i + len(sig)] += sig * (1 + pan) / 2 * 2 ** 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--bao-cao", help="file bao cao (mac dinh PROJECT/venet-report.json)")
    ap.add_argument("--muc", type=float, default=-18.0, help="dinh am luong tieng but (dBFS), mac dinh -18")
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()
    p = Path(a.project)
    rp = Path(a.bao_cao) if a.bao_cao else p / "venet-report.json"
    try:
        rep = json.loads(rp.read_text(encoding="utf-8"))
        total = float(json.loads((p / "timeline.json").read_text(encoding="utf-8"))["total"])
    except (OSError, ValueError, KeyError) as e:
        sys.exit(f"[LOI] Khong doc duoc bao cao hoac timeline.json: {e}. Chay ve_net_kiem_tra.sh --json truoc.")
    scenes = rep.get("scenes", [])
    if not any(s.get("ev") for s in scenes):
        sys.exit("[LOI] Bao cao khong co thoi diem tung net (ev): composition dung venet.js cu? Cap nhat venet.js roi chay lai ve_net_kiem_tra.sh --json")
    seed = a.seed if a.seed is not None else int(hashlib.sha256(p.resolve().name.encode()).hexdigest()[:8], 16) % 10000
    rng = np.random.default_rng(seed)
    buf = np.zeros((2, int((total + 0.5) * SR)))
    n_ev = 0
    for si, s in enumerate(scenes):
        if si:
            add(buf, swish(rng), s["start"] - 0.05, 0.35, float(rng.uniform(-0.3, 0.3)))
        for e in s.get("ev", []):
            t, d, k = float(e["t"]), max(float(e["d"]), 0.05), e.get("k", "stroke")
            pan = float(rng.uniform(-0.25, 0.25))
            if k == "wipe":
                add(buf, scratch(rng, d, 400, 3200), t, 0.45, pan)
            elif k == "write":
                add(buf, scratch(rng, d, 1500, 6500, gate_hz=9), t, 1.0, pan)
                add(buf, tick(rng), t, 0.5, pan)
            else:
                add(buf, scratch(rng, d, 1800, 7000), t, 0.9, pan)
                add(buf, tick(rng), t, 0.6, pan)
            n_ev += 1
    peak = np.max(np.abs(buf)) + 1e-9
    buf *= 10 ** (a.muc / 20) / peak
    out = p / "audio" / "hieu-ung.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(buf.T, -1, 1) * 32767).astype("<i2")
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"Tieng but: {n_ev} net, {len(scenes)} canh, {total:.1f} giay, seed {seed}, dinh {a.muc} dBFS -> {out}")


if __name__ == "__main__":
    main()
