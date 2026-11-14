#!/usr/bin/env python3
"""Ghep tieng doc va phu de vao composition, xuat file .srt.

Dung:
  python3 inject.py PROJECT/timeline.json PROJECT/build/portrait/index.html [--no-burn]
  python3 inject.py PROJECT/timeline.json --srt-only PROJECT/phu-de.srt

Viec script lam (de agent dung hinh khong phai tu tinh moc thoi gian):
  - dong bo data-start/data-duration cua moi <section id="sc-<id>"> theo timeline
  - thay khoi // TIMES:BEGIN ... // TIMES:END bang `const T = {"s01": 0.0, ...}` de
    tween viet dang `T.s01 + 0.3`; doc lai mot canh thi chi can chay lai script nay
  - thay khoi <!-- AUDIO:BEGIN --> ... <!-- AUDIO:END --> bang cac the <audio>
  - thay khoi <!-- CAPTIONS:BEGIN --> ... <!-- CAPTIONS:END --> bang phu de dot chu
    (bo qua neu --no-burn, vd ban YouTube da co file .srt rieng)
  - dat data-duration cua #root bang tong thoi luong
  - ghi phu-de.srt canh index.html (hoac vao duong dan --srt-only)

Phu de duoc chia theo cau va dau phay, toi da --max-chars ky tu mot dong.
Dong hien duoi 1,2 giay duoc gop voi dong ke ben.
Thoi gian moi dong chia theo ty le so ky tu trong do dai tieng doc cua canh;
du chinh xac cho cau doc deu, co the lech vai tram ms o cau dai.

Phu de lay truong "subtitle" cua canh trong PROJECT/scenes.json neu co (chu viet
dang chuan: "iOS 27.2.1", "iPhone 11"), khong thi lay "narration" (viet theo cach
doc cho TTS). "Wi-Fi" trong phu de dot chu duoc giu khong ngat dong.
"""
import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path


def balanced_wrap(text: str, max_chars: int):
    """Chia cum dai thanh cac dong dai gan bang nhau, tranh mot chu mo coi o dong cuoi."""
    words = text.split()
    n = -(-len(text) // max_chars)
    while True:
        target = len(text) / n
        lines, buf = [], ""
        for w in words:
            cand = f"{buf} {w}".strip()
            if buf and len(cand) > target and len(lines) < n - 1:
                lines.append(buf)
                buf = w
            else:
                buf = cand
        lines.append(buf)
        if all(len(l) <= max_chars for l in lines) or n >= len(words):
            return lines
        n += 1


def split_text(text: str, max_chars: int):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?;:])\s+", text) if s.strip()]
    chunks = []
    for s in sentences:
        if len(s) <= max_chars:
            chunks.append(s)
            continue
        parts = [p.strip() for p in re.split(r"(?<=,)\s+", s) if p.strip()]
        buf = ""
        for p in parts:
            cand = f"{buf} {p}".strip()
            if len(cand) <= max_chars:
                buf = cand
                continue
            if buf:
                chunks.append(buf)
                buf = ""
            if len(p) <= max_chars:
                buf = p
            else:
                chunks.extend(balanced_wrap(p, max_chars))
        if buf:
            chunks.append(buf)
    return chunks


MIN_SHOW = 1.2   # giay: dong phu de hien ngan hon muc nay thi gop voi dong ke ben


def read_floor(text):
    """Thoi gian toi thieu mot dong phu de nen hien.

    Phu de chay theo loi doc (tieng Viet khoang 3,5 tieng moi giay). Khong dung nguong
    0,5 + 0,3 giay moi tu cua HyperFrames check (tinh cho tieng Anh): voi tieng Viet nguong
    do luon bi vuot, lam moi dong bi gop roi cat lai theo so ky tu, ngat giua cum tu
    (vd "sau khi di / ve sinh") thay vi ngat o dau cau va dau phay.
    """
    return MIN_SHOW


def merge_short(chunks, scene_dur, max_chars):
    """Gop dong hien qua nhanh voi dong ke ben neu tong do dai van trong gioi han."""
    changed = True
    while changed and len(chunks) > 1:
        changed = False
        total = sum(len(c) for c in chunks)
        for i, c in enumerate(chunks):
            if scene_dur * len(c) / total >= read_floor(c):
                continue
            j = i + 1 if i + 1 < len(chunks) else i - 1
            a, b = sorted((i, j))
            merged = f"{chunks[a]} {chunks[b]}"
            if len(merged) <= max_chars:
                chunks[a:b + 1] = [merged]
                changed = True
                break
            # Gop qua dai: chia lai cap dong cho can (tranh mot cum chu mo coi)
            parts = balanced_wrap(merged, max_chars)
            if len(parts) == 2 and parts != [chunks[a], chunks[b]]:
                chunks[a:b + 1] = parts
                changed = True
                break
    return chunks


def build_captions(timeline, max_chars):
    caps = []
    try:
        _sub = {x["id"]: x["subtitle"] for x in json.load(open(Path(timeline.get("_project", ".")) / "scenes.json"))["scenes"] if x.get("subtitle")}
        for _sc in timeline["scenes"]:
            if _sc["id"] in _sub: _sc["subtitle"] = _sub[_sc["id"]]
    except Exception:
        pass
    for sc in timeline["scenes"]:
        chunks = merge_short(split_text(sc.get("subtitle") or sc["narration"], max_chars), sc["duration"], max_chars)
        weights = [max(len(c), 1) for c in chunks]
        total_w = sum(weights)
        t = sc["start"]
        for c, w in zip(chunks, weights):
            d = sc["duration"] * w / total_w
            caps.append({"start": round(t, 3), "end": round(t + d, 3), "text": c.rstrip(".")})
            t += d
    return caps


def srt_time(s):
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def write_srt(caps, path: Path):
    lines = []
    for i, c in enumerate(caps, 1):
        lines += [str(i), f"{srt_time(c['start'])} --> {srt_time(c['end'])}", c["text"], ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_speech_env(voiceover: Path, out: Path, fps=30):
    """Am luong loi doc (0..1) moi khung hinh. voiceover.wav da canh theo moc timeline
    (tts.py ghep dung khoang nghi pause_before cua tung canh), nen chi so khung = giay * fps."""
    import numpy as np
    import soundfile as sf
    a, sr = sf.read(str(voiceover))
    if a.ndim > 1:
        a = a.mean(axis=1)
    hop = sr // fps
    n = len(a) // hop + 1
    env = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2)) if len(a[i * hop:(i + 1) * hop]) else 0.0
                    for i in range(n)])
    env = np.clip(env / (np.percentile(env[env > 0], 95) if (env > 0).any() else 1.0), 0, 1)
    env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
    out.write_text("window.SPEECH = " + json.dumps({"fps": fps, "env": [round(float(x), 3) for x in env]}) + ";\n",
                   encoding="utf-8")


def replace_block(src, name, body):
    pat = re.compile(rf"(<!-- {name}:BEGIN -->)(.*?)(<!-- {name}:END -->)", re.S)
    if not pat.search(src):
        raise SystemExit(f"Thieu cap danh dau <!-- {name}:BEGIN/END --> trong composition")
    return pat.sub(lambda m: m.group(1) + "\n" + body + "\n      " + m.group(3), src)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timeline")
    ap.add_argument("index", nargs="?")
    ap.add_argument("--no-burn", action="store_true", help="Khong dot phu de vao hinh")
    ap.add_argument("--max-chars", type=int, help="Mac dinh: 56 cho doc (toi da 2 dong), 48 cho ngang")
    ap.add_argument("--srt-only", help="Chi ghi file .srt toi duong dan nay")
    a = ap.parse_args()

    tl_path = Path(a.timeline)
    timeline = json.loads(tl_path.read_text(encoding="utf-8"))
    project = tl_path.parent
    timeline["_project"] = str(project)  # de build_captions tim scenes.json (truong subtitle)

    if a.srt_only:
        write_srt(build_captions(timeline, a.max_chars or 42), Path(a.srt_only))
        return
    if not a.index:
        ap.error("can duong dan index.html")

    index = Path(a.index)
    src = index.read_text(encoding="utf-8")
    portrait = 'data-resolution="portrait"' in src

    # Dong bo khung thoi gian cua cac canh
    # Bo qua the nam trong chu thich HTML: template co dong vi du `<section id="sc-s01" ...>`
    # trong chu thich, khong duoc bat nham va khong duoc ghi de len do.
    for sc in timeline["scenes"]:
        pat = re.compile(rf'<section\b[^>]*\bid="sc-{re.escape(sc["id"])}"[^>]*>')
        comments = [mm.span() for mm in re.finditer(r"<!--.*?-->", src, re.S)]
        m = next((mm for mm in pat.finditer(src)
                  if not any(a <= mm.start() < b for a, b in comments)), None)
        if not m:
            raise SystemExit(f'Thieu <section id="sc-{sc["id"]}"> trong {index}')
        tag = m.group(0)
        if 'data-start="' not in tag or 'data-duration="' not in tag:
            raise SystemExit(f'<section id="sc-{sc["id"]}"> thieu data-start hoac data-duration trong {index}')
        new = re.sub(r'data-start="[^"]*"', f'data-start="{sc["visual_start"]}"', tag)
        new = re.sub(r'data-duration="[^"]*"', f'data-duration="{sc["visual_duration"]}"', new)
        src = src[:m.start()] + new + src[m.end():]

    times = json.dumps({sc["id"]: sc["visual_start"] for sc in timeline["scenes"]})
    pat = re.compile(r"(// TIMES:BEGIN).*?(// TIMES:END)", re.S)
    if not pat.search(src):
        raise SystemExit("Thieu cap danh dau // TIMES:BEGIN/END trong composition")
    src = pat.sub(lambda m: f"{m.group(1)}\n      const T = {times};\n      {m.group(2)}", src)
    caps = build_captions(timeline, a.max_chars or (56 if portrait else 48))

    # Chep audio vao du an composition de duong dan tuong doi dung khi render
    (index.parent / "audio").mkdir(exist_ok=True)
    audio_tags = []
    for sc in timeline["scenes"]:
        shutil.copy2(project / sc["audio"], index.parent / sc["audio"])
        audio_tags.append(
            f'      <audio id="vo-{sc["id"]}" src="{sc["audio"]}" data-start="{sc["start"]}" '
            f'data-duration="{sc["duration"]}" data-volume="1"></audio>')
    src = replace_block(src, "AUDIO", "\n".join(audio_tags))

    wifi = '<i style="font-style:normal;white-space:nowrap">Wi-Fi</i>'
    cap_tags = [] if a.no_burn else [
        f'      <div id="cap-{i:03d}" class="cap clip" data-start="{c["start"]}" '
        f'data-duration="{round(c["end"] - c["start"], 3)}"><span>{html.escape(c["text"]).replace("Wi-Fi", wifi)}</span></div>'
        for i, c in enumerate(caps, 1)]
    src = replace_block(src, "CAPTIONS", "\n".join(cap_tags))

    total = timeline["total"]
    src, n = re.subn(r'(id="root"[^>]*?data-duration=")[^"]*(")', rf"\g<1>{total}\g<2>", src, flags=re.S)
    if n != 1:
        raise SystemExit('Khong tim thay data-duration tren phan tu id="root"')

    # Phan tu keo dai ca video (vd san khau 3D): data-span="full"
    def full_span(m):
        tag = re.sub(r'data-start="[^"]*"', 'data-start="0"', m.group(0))
        return re.sub(r'data-duration="[^"]*"', f'data-duration="{total}"', tag)
    src = re.sub(r'<[^>]*\bdata-span="full"[^>]*>', full_span, src)

    # Canh 3D: am luong loi doc theo tung khung hinh, dung cho gat dau va cu chi khi noi
    if 'src="speech.js"' in src:
        write_speech_env(project / "voiceover.wav", index.parent / "speech.js")
    if 'src="tinh-cach.js"' in src:
        # tinh cach (cach dien) cua vai: thu vien SKILL/tinh-cach/ + PROJECT/tinh-cach/
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import vai
        tcs, err = vai.read_tc(project)
        if err:
            sys.exit("Loi tinh cach: " + "; ".join(err))
        (index.parent / "tinh-cach.js").write_text(
            "window.TINH_CACH = " + json.dumps({k: t for k, (_, t) in tcs.items()}, ensure_ascii=False) + ";\n",
            encoding="utf-8")

    index.write_text(src, encoding="utf-8")
    write_srt(caps, index.parent / "phu-de.srt")
    print(f"{index}: {len(audio_tags)} doan tieng, {len(cap_tags)} dong phu de dot, tong {total}s")


if __name__ == "__main__":
    main()
