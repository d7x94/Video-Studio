#!/usr/bin/env python3
"""Moc thoi gian tung tu (tung tieng) cua loi doc, uoc luong tu file tieng tung canh.

Dung:
  python3 moc_tu.py PROJECT                 # ghi PROJECT/moc-tu.json, in tom tat tung canh
  python3 moc_tu.py PROJECT --tim "rua tay" # in giay bat dau cua cum tu trong loi doc (lan dau xuat hien)

Can PROJECT/timeline.json va audio/<id>.wav (do tts.py tao). Doc them PROJECT/scenes.json de lay truong
"subtitle" (phu de viet dang chuan) neu co.

Cach uoc luong (khong dung mo hinh nhan dang giong noi, khong tai gi):
  1. Do am luong moi 10 ms, tim cac doan im lang. Khoang lang tu 0,15 giay la cho ngat cau.
  2. Chia loi doc thanh cum theo dau cau (, . ; : ! ? ...). Ghep moi cho ngat cum voi mot khoang lang:
     du khoang lang thi lay cac khoang dai nhat; thieu thi ghep khoang lang voi cho ngat gan nhat theo ty le.
  3. Trong moi cum, chia thoi gian co tieng (bo qua im lang) cho tung tieng theo do dai chu,
     roi dich moi ranh gioi ve cho am luong thap nhat trong +-0,08 giay (ranh gioi giua hai tieng thuong o do).
Tieng Viet moi tu viet cach la mot tieng, nen "tu" o day la mot tieng. Do chinh xac: ranh gioi cum
khop cho ngat that cua giong doc; trong cum co the lech vai chuc den khoang 150 ms o cau dai.

Phu de khac loi doc (truong "subtitle", vd "iOS 27.2.1" doc thanh "i-o-et hai muoi bay..."): neu so cum
bang nhau thi moi cum phu de nhan dung khoang thoi gian cua cum loi doc tuong ung; khong bang thi chia
deu theo do dai chu tren toan bo thoi gian co tieng cua canh.

Dau ra moc-tu.json: {"scenes": [{"id", "words": [{"w","s","e"}] (loi doc), "sub": [{"w","s","e"}] (phu de)}]}
Giay tinh tu dau video (cung moc voi timeline.json).
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np

HOP = 0.01          # giay moi o do am luong
GAP_PAUSE = 0.15    # khoang lang tu muc nay la cho ngat cau
GAP_JOIN = 0.06     # khoang lang ngan hon muc nay coi nhu lien tieng
SNAP = 0.08         # tim cho am luong thap nhat trong +- muc nay quanh moi ranh gioi tieng
MIN_WORD = 0.06     # moi tieng toi thieu
PUNCT_END = re.compile(r"[,.;:!?…]+[\"'”)\]]*$")


def read_mono(path):
    import soundfile as sf
    a, sr = sf.read(str(path), dtype="float32")
    if a.ndim > 1:
        a = a.mean(axis=1)
    return a, sr


def envelope(a, sr):
    hop = max(1, int(sr * HOP))
    n = len(a) // hop
    if n == 0:
        return np.zeros(1)
    x = a[: n * hop].reshape(n, hop)
    return np.sqrt(np.mean(x ** 2, axis=1)) + 1e-9


def voiced_spans(env):
    """Cac doan co tieng [(a, b)] theo giay, da gop khoang lang rat ngan."""
    db = 20 * np.log10(env)
    top = np.percentile(db, 95)
    on = db > max(top - 32, -50)
    spans, i, n = [], 0, len(on)
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            spans.append([i * HOP, j * HOP])
            i = j
        else:
            i += 1
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] < GAP_JOIN:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    merged = [s for s in merged if s[1] - s[0] >= 0.03] or merged
    return merged


def tokens(text):
    return [t for t in text.split() if re.search(r"\w", t)]


def weight(tok):
    letters = len(re.sub(r"\W", "", tok))
    return 0.6 + 0.1 * letters


def phrases(toks):
    """Chi so tieng cuoi moi cum (cum ket thuc o dau cau)."""
    ends = [i for i, t in enumerate(toks) if PUNCT_END.search(t)]
    if not ends or ends[-1] != len(toks) - 1:
        ends.append(len(toks) - 1)
    return ends


class SpeechClock:
    """Doi giua thoi gian thuc va 'thoi gian co tieng' (bo cac doan lang) trong mot khoang."""

    def __init__(self, spans, a, b):
        self.iv = [(max(s, a), min(e, b)) for s, e in spans if min(e, b) > max(s, a)]
        if not self.iv:
            self.iv = [(a, b)]
        self.total = sum(e - s for s, e in self.iv)

    def at(self, u):
        """u: thoi gian co tieng tinh tu dau khoang -> giay thuc."""
        for s, e in self.iv:
            if u <= e - s:
                return s + u
            u -= e - s
        return self.iv[-1][1]


def snap(t, env, lo, hi):
    a = max(lo + MIN_WORD, t - SNAP)
    b = min(hi - MIN_WORD, t + SNAP)
    if b <= a:
        return t
    i0, i1 = int(a / HOP), int(b / HOP) + 1
    seg = env[i0:i1]
    if len(seg) == 0:
        return t
    return (i0 + int(np.argmin(seg))) * HOP + HOP / 2


def distribute(toks, spans, a, b, env):
    """Chia [a, b] (giay trong canh) cho cac tieng theo trong so, chi tren thoi gian co tieng."""
    if not toks:
        return []
    clk = SpeechClock(spans, a, b)
    w = np.array([weight(t) for t in toks])
    cum = np.concatenate([[0], np.cumsum(w)]) / w.sum() * clk.total
    edges = [clk.at(u) for u in cum]
    edges[0], edges[-1] = clk.iv[0][0], clk.iv[-1][1]
    for k in range(1, len(edges) - 1):
        edges[k] = snap(edges[k], env, edges[k - 1], edges[k + 1] if k + 1 < len(edges) - 1 else edges[-1])
        edges[k] = min(max(edges[k], edges[k - 1] + MIN_WORD), edges[-1] - MIN_WORD * (len(edges) - 1 - k))
    out = []
    for k, t in enumerate(toks):
        s, e = edges[k], edges[k + 1]
        # tieng ket thuc truoc khoang lang dai: cat o cuoi doan co tieng chua no
        for vs, ve in clk.iv:
            if vs <= s < ve and e > ve + GAP_PAUSE:
                e = ve
        out.append([t, s, max(e, s + 0.02)])
    return out


def scene_words(text, wav_path):
    a, sr = read_mono(wav_path)
    env = envelope(a, sr)
    spans = voiced_spans(env)
    toks = tokens(text)
    if not toks:
        return [], spans
    if not spans:
        spans = [[0.0, len(a) / sr]]
    start, end = spans[0][0], spans[-1][1]
    ends = phrases(toks)
    gaps = [(spans[i][1], spans[i + 1][0]) for i in range(len(spans) - 1)
            if spans[i + 1][0] - spans[i][1] >= GAP_PAUSE]
    need = len(ends) - 1
    cuts = []                                   # (chi so tieng cuoi cum, giua khoang lang)
    if need and gaps:
        wsum = np.cumsum([weight(t) for t in toks])
        frac = {e: wsum[e] / wsum[-1] for e in ends[:-1]}
        clk = SpeechClock(spans, start, end)
        if len(gaps) >= need:
            pick = sorted(sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:need])
            cuts = list(zip(ends[:-1], pick))
        else:
            # it khoang lang hon cho ngat: ghep moi khoang lang voi cho ngat gan nhat (giu thu tu)
            used, last = set(), -1
            for g in gaps:
                u = sum(min(e_, g[0]) - s_ for s_, e_ in clk.iv if s_ < g[0]) / clk.total
                best = min((e for e in ends[:-1] if e > last and e not in used),
                           key=lambda e: abs(frac[e] - u), default=None)
                if best is not None:
                    used.add(best)
                    last = best
                    cuts.append((best, g))
            cuts.sort()
    words, i0, t0 = [], 0, start
    for e, g in cuts + [(len(toks) - 1, (end, end))]:
        words += distribute(toks[i0:e + 1], spans, t0, g[0], env)
        i0, t0 = e + 1, g[1]
    return words, spans


def norm(s):
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def sub_words(subtitle, narr_words, spans_abs):
    """Phu de viet chuan: chia theo cum neu so cum khop loi doc, khong thi chia deu."""
    st = tokens(subtitle)
    if not st or not narr_words:
        return []
    if [norm(t) for t in st] == [norm(w[0]) for w in narr_words]:
        return [[t, w[1], w[2]] for t, w in zip(st, narr_words)]
    s_ends, n_ends = phrases(st), phrases([w[0] for w in narr_words])
    groups = []
    if len(s_ends) == len(n_ends):
        si = ni = 0
        for se, ne in zip(s_ends, n_ends):
            groups.append((st[si:se + 1], narr_words[ni][1], narr_words[ne][2]))
            si, ni = se + 1, ne + 1
    else:
        groups.append((st, narr_words[0][1], narr_words[-1][2]))
    out = []
    for toks, a, b in groups:
        clk = SpeechClock(spans_abs, a, b)
        w = np.array([max(len(re.sub(r"\W", "", t)), 1) + 1.0 for t in toks])
        cum = np.concatenate([[0], np.cumsum(w)]) / w.sum() * clk.total
        ed = [clk.at(u) for u in cum]
        ed[0], ed[-1] = a, b
        out += [[t, ed[k], max(ed[k + 1], ed[k] + 0.02)] for k, t in enumerate(toks)]
    return out


def build(project: Path):
    tl = json.loads((project / "timeline.json").read_text(encoding="utf-8"))
    subs = {}
    try:
        subs = {x["id"]: x.get("subtitle") for x in
                json.loads((project / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    except (OSError, ValueError, KeyError):
        pass
    out = []
    for sc in tl["scenes"]:
        words, spans = scene_words(sc["narration"], project / sc["audio"])
        off = float(sc["start"])
        words = [[w, round(s + off, 3), round(e + off, 3)] for w, s, e in words]
        spans_abs = [(s + off, e + off) for s, e in spans]
        sub = subs.get(sc["id"])
        sw = sub_words(sub, words, spans_abs) if sub else words
        sw = [[w, round(s, 3), round(e, 3)] for w, s, e in sw]
        out.append({"id": sc["id"], "words": [dict(w=w, s=s, e=e) for w, s, e in words],
                    "sub": [dict(w=w, s=s, e=e) for w, s, e in sw]})
    return {"version": 1, "scenes": out}


def find(data, phrase):
    """Giay bat dau cua cum tu (khong phan biet dau, hoa thuong) trong loi doc; None neu khong thay."""
    q = norm(phrase).split()
    if not q:
        return None
    for sc in data["scenes"]:
        ws = [norm(w["w"]) for w in sc["words"]]
        for i in range(len(ws) - len(q) + 1):
            if ws[i:i + len(q)] == q:
                return sc["words"][i]["s"]
    return None


def load_or_build(project: Path):
    """Doc moc-tu.json neu moi hon timeline.json, khong thi tinh lai va ghi file."""
    f = project / "moc-tu.json"
    tl = project / "timeline.json"
    if f.exists() and f.stat().st_mtime >= tl.stat().st_mtime:
        return json.loads(f.read_text(encoding="utf-8"))
    data = build(project)
    f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--tim", help="in giay bat dau cua cum tu nay trong loi doc")
    a = ap.parse_args()
    p = Path(a.project)
    if not (p / "timeline.json").exists():
        sys.exit("[LOI] Chua co timeline.json: chay tts.py truoc")
    data = build(p)
    (p / "moc-tu.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.tim:
        t = find(data, a.tim)
        if t is None:
            sys.exit(f"[LOI] Khong thay \"{a.tim}\" trong loi doc")
        print(f"{t:.2f}")
        return
    for sc in data["scenes"]:
        w = sc["words"]
        if w:
            print(f"{sc['id']}: {len(w)} tieng, {w[0]['s']:.2f}s -> {w[-1]['e']:.2f}s"
                  + (f", phu de {len(sc['sub'])} tu" if sc["sub"] is not w else ""))
    print(f"Da ghi {p / 'moc-tu.json'}")


if __name__ == "__main__":
    main()
