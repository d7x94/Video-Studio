#!/usr/bin/env python3
"""Nhac nen do studio tu sang tac bang code, roi ghep vao video va tu giam am khi co loi doc.

Dung:
  python3 nhac_nen.py PROJECT --kieu nhe-nhang              # sang tac + ghep vao renders/final_*.mp4
  python3 nhac_nen.py PROJECT --kieu vui --chi-tao          # chi sang tac audio/nhac-nen.wav (+ .mp3 nghe thu)
  python3 nhac_nen.py PROJECT --kieu vui renders/preview_portrait.mp4   # ghep vao file chi dinh
  python3 nhac_nen.py PROJECT --bo                           # go nhac, tra lai ban khong nhac

Kieu: vui, nhe-nhang, nghiem-tuc, hoi-hop, ke-chuyen (bang KIEU ben duoi).

Toan bo am thanh tong hop tu song sin bang numpy (hoa am, arpeggio, giai dieu, bass, trong nhe, vang),
khong dung mau nhac, file nhac hay thu vien nhac ben ngoai. Tat dinh: cung PROJECT, kieu, seed thi ra
cung mot ban nhac (seed mac dinh lay tu ten thu muc du an).

Ghep: ban khong nhac duoc giu o renders/<ten>.khong-nhac.mp4 va luon ghep tu ban nay, nen chay lai
bao nhieu lan cung khong chong nhac. Nhac giam am theo loi doc bang bo nen sidechain cua ffmpeg,
vao dan 1,5 giay, ra dan 2,5 giay cuoi. Render lai video thi chay lai lenh nay.
"""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 48000
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
MAJOR = [0, 2, 4, 5, 7, 9, 11]
MINOR = [0, 2, 3, 5, 7, 8, 10]

# Moi kieu: thang am, nhip (bpm), vong hoa am (bac trong thang, 0 = bac I), cac lop nhac
KIEU = {
    "vui":        {"scale": MAJOR, "bpm": 112, "keys": ["C", "D", "F", "G"], "prog": [[0, 4, 5, 3], [0, 5, 3, 4]],
                   "pad": 0.5, "arp": "8", "bass": "12", "kick": True, "shaker": True, "bell": 0.6, "seventh": False},
    "nhe-nhang":  {"scale": MAJOR, "bpm": 84, "keys": ["F", "G", "D", "C"], "prog": [[0, 3, 5, 4], [0, 5, 3, 4]],
                   "pad": 0.8, "arp": "4", "bass": "1", "kick": False, "shaker": False, "bell": 0.5, "seventh": True},
    "nghiem-tuc": {"scale": MINOR, "bpm": 92, "keys": ["A", "D", "E", "C"], "prog": [[0, 5, 2, 6], [0, 3, 5, 4]],
                   "pad": 0.8, "arp": "16", "bass": "8", "kick": True, "shaker": False, "bell": 0.0, "seventh": False},
    "hoi-hop":    {"scale": MINOR, "bpm": 72, "keys": ["D", "E", "A"], "prog": [[0, 0, 5, 4], [0, 5, 0, 4]],
                   "pad": 0.9, "arp": "", "bass": "1", "kick": False, "shaker": False, "bell": 0.25, "seventh": False,
                   "tick": True},
    "ke-chuyen":  {"scale": MAJOR, "bpm": 76, "keys": ["G", "C", "F"], "prog": [[0, 2, 3, 0], [5, 3, 0, 4]],
                   "pad": 0.7, "arp": "4", "bass": "1", "kick": False, "shaker": False, "bell": 0.9, "seventh": False},
}


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a, r):
    """Bao do am: len trong a giay, giu, tat trong r giay o cuoi."""
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def tone_pad(m, dur, det):
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros_like(t)
    for k in range(1, 7):
        y += np.sin(2 * np.pi * hz(m) * k * (1 + det) * t) / k ** 1.6
    return y * env(len(t), min(0.8, dur / 3), min(0.8, dur / 3))


def tone_pluck(m, dur, rng):
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros_like(t)
    ph = rng.uniform(0, 2 * np.pi, 8)
    for k in range(1, 9):
        y += np.sin(2 * np.pi * hz(m) * k * t + ph[k - 1]) * np.exp(-t * (2.2 + 1.6 * k)) / k
    return y * env(len(t), 0.003, 0.05)


def tone_bell(m, dur):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    y = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4.5)
         + 0.12 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 8))
    return y * env(len(t), 0.002, 0.08)


def tone_bass(m, dur):
    t = np.arange(int(dur * SR)) / SR
    y = np.sin(2 * np.pi * hz(m) * t) + 0.25 * np.sin(4 * np.pi * hz(m) * t)
    return y * np.exp(-t * 1.2) * env(len(t), 0.01, 0.06)


def kick():
    t = np.arange(int(0.35 * SR)) / SR
    f = 45 + 75 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def noise_hit(rng, dur, decay, hp=True):
    n = rng.standard_normal(int(dur * SR))
    if hp:
        n = np.diff(n, prepend=0)
    return n * np.exp(-np.arange(len(n)) / SR * decay)


def add(buf, sig, at, gain, pan=0.0):
    i = int(at * SR)
    if i >= buf.shape[1]:
        return
    sig = sig[: buf.shape[1] - i] * gain
    buf[0, i:i + len(sig)] += sig * (1 - pan) / 2 * 2 ** 0.5
    buf[1, i:i + len(sig)] += sig * (1 + pan) / 2 * 2 ** 0.5


def reverb(buf, rng, secs=1.8, wet=0.22):
    n = int(secs * SR)
    out = np.empty_like(buf)
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 3.2)
        ir[0] = 0
        L = 1 << int(np.ceil(np.log2(buf.shape[1] + n)))
        wetc = np.fft.irfft(np.fft.rfft(buf[c], L) * np.fft.rfft(ir, L), L)[: buf.shape[1]]
        wetc /= np.max(np.abs(wetc)) + 1e-9
        out[c] = buf[c] + wet * wetc * np.max(np.abs(buf[c]))
    return out


def compose(kieu, total, seed):
    K = KIEU[kieu]
    rng = np.random.default_rng(seed)
    key = NOTE[K["keys"][seed % len(K["keys"])]]
    sc = K["scale"]
    prog = K["prog"][(seed // 7) % len(K["prog"])]
    beat = 60.0 / K["bpm"]
    bar = 4 * beat
    nbar = int(math.ceil(total / bar))
    buf = np.zeros((2, int(total * SR) + SR * 3))

    def deg(d, octave):                       # bac d cua thang -> so midi
        return 12 * (octave + 1) + key + sc[d % 7] + 12 * (d // 7)

    def chord(d):
        tones = [d, d + 2, d + 4] + ([d + 6] if K["seventh"] else [])
        return tones

    # giai dieu: mot motif 2 o nhip lap lai co bien tau (A A' B A)
    motif = [(int(rng.integers(0, 3)) * 2, float(r)) for r in rng.choice([0.5, 1.0, 1.5], size=4)]
    for b in range(nbar):
        t0 = b * bar
        d = prog[b % len(prog)]
        last = b == nbar - 1
        if last:
            d = 0
        # hoa am nen
        for i, x in enumerate(chord(d)):
            for det, pan in ((-0.002, -0.5), (0.002, 0.5)):
                add(buf, tone_pad(deg(x, 3), bar + 0.6, det), t0, 0.05 * K["pad"], pan)
        # bass
        hits = {"1": [0], "12": [0, 2], "8": [i * 0.5 for i in range(8)]}.get(K["bass"], [])
        for h in hits:
            add(buf, tone_bass(deg(d, 2), beat * (0.45 if K["bass"] == "8" else 1.8)), t0 + h * beat, 0.16)
        if b == 0:
            continue                          # o nhip dau chi co hoa am, bass: vao nhe
        # arpeggio
        if K["arp"]:
            step = {"4": 1.0, "8": 0.5, "16": 0.25}[K["arp"]]
            seq = chord(d) + [chord(d)[1] + 7]
            n = int(4 / step)
            for i in range(n):
                x = seq[i % len(seq)] if (i // len(seq)) % 2 == 0 else seq[-1 - i % len(seq)]
                add(buf, tone_pluck(deg(x, 4), 1.2, rng), t0 + i * step * beat,
                    0.07 if K["arp"] == "16" else 0.09, 0.35 if i % 2 else -0.35)
        # giai dieu chuong (bo o nhip cuoi de ket bang hop am)
        if K["bell"] and not last:
            phrase = (b - 1) % 4
            mt = motif if phrase != 2 else [(p + 2, r) for p, r in motif[::-1]]
            pos = 0.0
            for j, (p, r) in enumerate(mt):
                if pos >= 4:
                    break
                note = d + p + (1 if (phrase == 1 and j == len(mt) - 1) else 0)
                add(buf, tone_bell(deg(note, 5), 1.6), t0 + pos * beat, 0.11 * K["bell"], 0.15)
                pos += r * 2 if K["bpm"] < 90 else r * 1.5
        # trong
        if K.get("kick") and not last:
            for h in ([0, 2] if K["bpm"] > 100 else [0]):
                add(buf, kick(), t0 + h * beat, 0.35)
        if K.get("shaker") and not last:
            for i in range(8):
                add(buf, noise_hit(rng, 0.08, 60), t0 + i * 0.5 * beat, 0.025 if i % 2 else 0.04, 0.4)
        if K.get("tick") and not last:
            for i in range(8):
                add(buf, noise_hit(rng, 0.03, 200), t0 + i * 0.5 * beat, 0.03, -0.3)
    # hop am ket keo dai
    for x in chord(0):
        add(buf, tone_pad(deg(x, 3), 3.0, 0.0), (nbar - 1) * bar, 0.04 * K["pad"])

    buf = reverb(buf[:, : int(total * SR)], rng)
    n = buf.shape[1]
    buf *= env(n, 1.5, 2.5)
    # chuan muc: RMS ve -18 dBFS de --muc co nghia nhu nhau o moi kieu; dinh khong vuot -1 dBFS
    rms = np.sqrt(np.mean(buf ** 2)) + 1e-9
    buf *= 10 ** (-18 / 20) / rms
    peak = np.max(np.abs(buf))
    if peak > 0.89:
        buf *= 0.89 / peak
    return buf, {"key": K["keys"][seed % len(K["keys"])], "prog": prog,
                                                        "bpm": K["bpm"], "bars": nbar}


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def mix(video, music, out, level_db):
    """Ghep nhac (da giam am theo loi doc) vao video; giu nguyen luong hinh."""
    fc = (f"[1:a]volume={level_db}dB,aformat=sample_rates=48000:channel_layouts=stereo[m];"
          "[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[v1][v2];"
          "[m][v2]sidechaincompress=threshold=0.03:ratio=4:attack=30:release=450[md];"
          "[v1][md]amix=inputs=2:duration=first:normalize=0[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(music), "-filter_complex", fc,
                    "-map", "0:v", "-c:v", "copy", "-map", "[a]", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", str(out)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("videos", nargs="*", help="file video can ghep (mac dinh renders/final_*.mp4)")
    ap.add_argument("--kieu", choices=sorted(KIEU), help="bat buoc tru khi --bo")
    ap.add_argument("--seed", type=int, help="doi ban nhac khac cung kieu")
    ap.add_argument("--muc", type=float, default=-10.0, help="muc nhac truoc khi giam am (dB), mac dinh -10")
    ap.add_argument("--chi-tao", action="store_true")
    ap.add_argument("--bo", action="store_true", help="go nhac, tra lai ban khong nhac")
    a = ap.parse_args()
    p = Path(a.project)
    vids = [Path(v) if Path(v).is_absolute() else p / v for v in a.videos] or sorted((p / "renders").glob("final_*.mp4"))
    vids = [v for v in vids if not v.name.endswith(".khong-nhac.mp4")]

    if a.bo:
        for v in vids:
            raw = v.with_name(v.stem + ".khong-nhac.mp4")
            if raw.exists():
                shutil.move(raw, v)
                print(f"Da go nhac: {v}")
        return
    if not a.kieu:
        ap.error("can --kieu")

    tl = json.loads((p / "timeline.json").read_text(encoding="utf-8"))
    total = float(tl["total"])
    seed = a.seed if a.seed is not None else int(hashlib.sha256(p.resolve().name.encode()).hexdigest()[:8], 16) % 10000
    import soundfile as sf
    music, meta = compose(a.kieu, total + 0.2, seed)
    wav = p / "audio/nhac-nen.wav"
    wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(wav, music.T, SR)
    meta.update({"kieu": a.kieu, "seed": seed, "muc_db": a.muc, "giay": round(total, 2)})
    (p / "audio/nhac-nen.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    print(f"Nhac nen: kieu {a.kieu}, giong {meta['key']}, {meta['bpm']} bpm, seed {seed}, {total:.1f} giay -> {wav}")
    if a.chi_tao:
        mp3 = wav.with_suffix(".mp3")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-b:a", "160k", str(mp3)], check=True)
        print(f"Nghe thu: {mp3}")
        return
    if not vids:
        sys.exit("Chua co renders/final_*.mp4: render ban cuoi truoc, hoac ghi file video can ghep")
    for v in vids:
        raw = v.with_name(v.stem + ".khong-nhac.mp4")
        if not raw.exists() or v.stat().st_mtime > raw.stat().st_mtime + 1:
            shutil.copy2(v, raw)                # ban moi render (chua co nhac): giu lam ban goc
        if abs(duration(raw) - total) > 1.0:
            print(f"[CANH BAO] {v.name} dai {duration(raw):.1f} giay, timeline {total:.1f} giay")
        tmp = v.with_name(v.stem + ".tmp.mp4")
        mix(raw, wav, tmp, a.muc)
        tmp.replace(v)
        import os
        st = raw.stat()
        os.utime(raw, (st.st_atime, v.stat().st_mtime))   # ban goc cung moc gio: chay lai khong coi la ban moi
        print(f"Da ghep nhac: {v} (ban khong nhac: {raw.name})")


if __name__ == "__main__":
    main()
