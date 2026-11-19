#!/usr/bin/env python3
"""Kiem loi doc tu dong truoc khi long tieng va sau khi ghep (video co san).

Dung:
  python3 kiem_loi_doc.py PROJECT [--xung-ho-toi-da N] [--nghiem]

Doc PROJECT/scenes.json; neu co PROJECT/job.json thi doi chieu moc anh tinh; neu co audio/<id>.wav thi do do dai loi
(ffprobe), neu co timeline_ghep.json thi dung moc da ghep (khong co thi tinh moc cue va giu_hinh tu job.json, co cong phan keo dai giu hinh) (CANH BAO neu file nay cu hon job.json, scenes.json
hoac mot audio/<id>.wav: chay job.py dung roi kiem lai). Kiem:
  LOI (thoat ma 1):
    - loi chong len nhau (ket thuc loi truoc sau luc bat dau loi sau)
  CANH BAO:
    - cach doc viet co gach noi kieu "H-D-M-I" (giong doc ngat tung chu, xem references/giong-doc.md)
    - dai tu xung ho (minh, tui, toi, to, tao): dem theo canh va tong; canh bao khi vuot --xung-ho-toi-da
      (hoac "xung_ho_toi_da" trong job.json); khong dat thi chi liet ke
    - tu khen tuyet doi, cam ket, khuyen mua (tuyet doi, hoan hao, tot nhat, chac chan, nen mua ...)
    - ten rieng lan chu hoa thuong, chu viet tat, chi so (OBgE, HDMI, SPF50+) nam trong narration: phai ghi cach doc
      trong narration va chu chuan trong subtitle
    - khoang cach giua hai loi duoi 0,2 giay
    - loi dai hon doan anh tinh chua no (khi job.json co anh_tinh va canh khong dung giu_hinh)
  THONG TIN: so tieng moi giay tung canh (tieng = tu cach nhau dau cach); khong co nguong, chi de chia ngan sach loi.
Danh sach tu va nguong 0,2 giay lay tu quy tac trong SKILL.md va profiles/unbox.md; script khong hieu ngu nghia,
cau dung quy tac van phai doc lai bang mat. --nghiem: thoat ma 1 neu co bat ky canh bao nao.
Yeu cau: python3, ffprobe (khi can do do dai).
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

XUNG_HO = r"(?<!\w)(mình|tui|tôi|tớ|tao)(?!\w)"
TUYET_DOI = ("tuyet doi", "hoan hao", "tot nhat", "chac chan", "tuyet voi", "so mot", "so 1", "luon luon",
             "khong bao gio", "duy nhat", "dinh nhat", "nen mua", "phai mua", "dang tien", "nhat the gioi",
             "cam ket")
GACH_NOI = re.compile(r"(?<![\w-])(?:[A-Za-zĐđ]-){2,}[A-Za-zĐđ](?![\w-])")
TEN_LAN = re.compile(r"\b(?:[A-Za-z]*[a-z][A-Z][A-Za-z]*|[A-Z]{2,}\d*\+?|[A-Z]+\d+\+?|\d+\+)\b")


def bo_dau(s):
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "d"))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn"))).strip()


def thoi_luong(wav):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(wav)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--xung-ho-toi-da", type=int)
    ap.add_argument("--nghiem", action="store_true")
    a = ap.parse_args()

    proj = Path(a.project)
    scenes = json.loads((proj / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    job = json.loads((proj / "job.json").read_text(encoding="utf-8")) if (proj / "job.json").exists() else {}
    toi_da = a.xung_ho_toi_da if a.xung_ho_toi_da is not None else job.get("xung_ho_toi_da")
    loi, cb, tt = [], [], []

    # thoi luong
    dur = {}
    for sc in scenes:
        w = proj / "audio" / f"{sc['id']}.wav"
        if w.exists():
            d = thoi_luong(w)
            if d:
                dur[sc["id"]] = d

    # moc bat dau
    start = {}
    tg = proj / "timeline_ghep.json"
    if tg.exists():
        start = {k: float(v) for k, v in json.loads(tg.read_text(encoding="utf-8")).get("start", {}).items()}
        moi_hon = [f for f in ("job.json", "scenes.json") if (proj / f).exists() and (proj / f).stat().st_mtime > tg.stat().st_mtime]
        moi_hon += [f"audio/{k}.wav" for k in dur if (proj / "audio" / f"{k}.wav").stat().st_mtime > tg.stat().st_mtime]
        if moi_hon:
            cb.append(f"timeline_ghep.json cu hon {', '.join(moi_hon[:4])}{' ...' if len(moi_hon) > 4 else ''}: moc loi va ket qua kiem chong loi "
                      "co the sai; chay job.py dung (hoac ghep_loi_video_co_san.py) roi kiem lai")
    elif job.get("canh"):
        truoc = job.get("khoang_truoc", 0.15)
        sau = job.get("khoang_sau", 0.35)
        for k, v in job["canh"].items():
            if "cue" in v:
                start[k] = float(v["cue"])
        # Chua co timeline_ghep.json: tinh moc giu_hinh bang cung cong thuc ghep_loi_video_co_san.py
        # (moi canh giu hinh keo dai khung hinh nen day cac canh giu hinh sau no); thieu tieng thi khong keo dai duoc.
        dich = 0.0
        giu = sorted(((k, v["giu_hinh"]) for k, v in job["canh"].items() if "giu_hinh" in v), key=lambda x: float(x[1]["hien_ro"]))
        for k, g in giu:
            s = float(g["hien_ro"]) + dich + truoc
            start[k] = s
            if k in dur:
                dich += max(0.0, s + dur[k] + sau - (float(g["dong_bang"]) + dich))
            else:
                cb.append(f"{k}: chua co audio/{k}.wav, chua tinh duoc phan keo dai giu hinh nen moc cac canh giu hinh sau no co the lech")

    tong_xh = 0
    for sc in scenes:
        sid = sc["id"]
        nar = sc.get("narration", "")
        sub = sc.get("subtitle") or ""
        for m in GACH_NOI.finditer(nar):
            cb.append(f"{sid}: cach doc co gach noi kieu danh van \"{m.group(0)}\" (viet lien theo cach doc, xem giong-doc.md)")
        xh = re.findall(XUNG_HO, nar, flags=re.IGNORECASE)
        if xh:
            tong_xh += len(xh)
            tt.append(f"{sid}: {len(xh)} dai tu xung ho ({', '.join(sorted(set(x.lower() for x in xh)))})")
        for t in TUYET_DOI:
            if re.search(rf"(?<![a-z0-9]){re.escape(t)}(?![a-z0-9])", bo_dau(nar + " " + sub)):
                cb.append(f"{sid}: tu khen tuyet doi hoac khuyen mua \"{t}\"")
        ten = sorted(set(TEN_LAN.findall(nar)))
        if ten:
            cb.append(f"{sid}: narration con ten rieng/chu viet tat/chi so viet nguyen dang ({', '.join(ten)}): "
                      "ghi cach doc trong narration, chu chuan trong subtitle")
        if sid in dur:
            n_tieng = len(nar.split())
            tt.append(f"{sid}: {n_tieng} tieng / {dur[sid]:.2f} giay = {n_tieng / dur[sid]:.1f} tieng moi giay")

    if toi_da is not None and tong_xh > toi_da:
        cb.append(f"tong {tong_xh} dai tu xung ho, vuot muc toi da {toi_da}")
    elif toi_da is None and tong_xh:
        tt.append(f"tong {tong_xh} dai tu xung ho (chua dat --xung-ho-toi-da)")

    # chong len nhau, khoang cach
    dd = sorted((s, k) for k, s in start.items() if k in dur)
    for (s1, k1), (s2, k2) in zip(dd, dd[1:]):
        gap = s2 - (s1 + dur[k1])
        if gap < 0:
            loi.append(f"loi {k1} (den {s1 + dur[k1]:.2f}s) chong len loi {k2} (bat dau {s2:.2f}s) {-gap:.2f}s")
        elif gap < 0.2:
            cb.append(f"loi {k1} va {k2} cach nhau {gap:.2f}s, duoi 0,2s")

    # loi dai hon anh tinh
    giu = {k for k, v in (job.get("canh") or {}).items() if "giu_hinh" in v}
    for k, s in start.items():
        if k in giu or k not in dur:
            continue
        for at in job.get("anh_tinh", []):
            if at["tu"] <= s < at["den"] and s + dur[k] > at["den"]:
                cb.append(f"{k}: loi dai hon doan anh tinh {at['tu']}-{at['den']}s (ket thuc {s + dur[k]:.2f}s): "
                          "rut loi hoac dung giu_hinh")
    for sc in scenes:
        if start and sc["id"] not in start:
            cb.append(f"{sc['id']}: chua co moc bat dau")
        if dur and sc["id"] not in dur:
            cb.append(f"{sc['id']}: chua co audio/{sc['id']}.wav (chay tts.py)")

    for x in tt:
        print(f"[THONG TIN] {x}")
    for x in cb:
        print(f"[CANH BAO] {x}", file=sys.stderr)
    for x in loi:
        print(f"[LOI] {x}", file=sys.stderr)
    print(f"[{'CHAN' if loi else 'OK'}] {len(loi)} loi, {len(cb)} canh bao, {len(scenes)} canh")
    if loi or (a.nghiem and cb):
        sys.exit(1)


if __name__ == "__main__":
    main()
