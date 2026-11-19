#!/usr/bin/env python3
"""Phu de tung tu (tu dang doc doi mau) cho video co san, ghi cung vao hinh.

Dung:
  python3 phu_de_tung_tu.py PROJECT [--font TEN] [--mau-nhan FFD166] [--mep-duoi 120] [--co-chu 46]
                            [--ass phu-de-tung-tu.ass] [--ghi VIDEO_VAO VIDEO_RA]

Doc PROJECT/moc-tu.json (moc_tu.py), PROJECT/timeline.json, PROJECT/timeline_ghep.json (job.py dung / ghep_loi_video_co_san.py).
Moi tu cua phu de (truong "sub" trong moc-tu.json: chu chuan cua subtitle, khong phai cach doc) la mot su kien ASS
trong khoang tu luc tu do bat dau doc den luc tu ke tiep bat dau; tu dang doc mau vang, cac tu con lai mau trang.
Moc tu timeline.json doi sang moc video cuoi bang: moc_ghep[canh] - moc_timeline[canh] (cong cho moi tu cua canh).
Phai chay SAU job.py dung (timeline_ghep.json moi) va SAU moc_tu.py (moc-tu.json moi); doi loi doc thi chay lai ca hai.

--ghi VIDEO_VAO VIDEO_RA: ghi cung file .ass vao video bang ffmpeg (x264 crf 17, tieng giu nguyen). Khong co --ghi thi chi ra .ass.
Font: --font, neu khong co thi tim "Be Vietnam Pro" ban TTF/OTF trong he thong (fc-list), roi "Inter"; khong co ca hai thi
dung font mac dinh cua fontconfig va in [CANH BAO]. Be Vietnam Pro do setup.sh cai (@fontsource) chi co woff/woff2
nen libass (ffmpeg ass=) khong doc duoc; muon dung phai tu cai ban TTF/OTF.
Hai su kien khong hien cung luc: ket thuc cua su kien bi cat o luc su kien ke tiep bat dau (ke ca giua hai canh).
Script tu kiem dinh dang ASS (moi dong Dialogue du 7 truong, moc thoi gian dung dang, Name va Effect rong); loi thi thoat ma 1.
Phu de nam o day khung hinh doc 720x1280 (PlayRes theo video khi co --ghi: doc kich thuoc bang ffprobe).
Yeu cau: python3, ffmpeg/ffprobe, fc-list (tuy chon).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def chon_font(yeu_cau):
    if yeu_cau:
        return yeu_cau
    try:
        ds = subprocess.run(["fc-list", ":", "family", "file"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        ds = ""
    for ten in ("Be Vietnam Pro", "Inter"):
        for dong in ds.splitlines():
            if ten.lower() in dong.lower() and re.search(r"\.(ttf|otf)\b", dong.lower()):
                return ten
    print("[CANH BAO] khong thay font Be Vietnam Pro hay Inter dang TTF/OTF; dung font mac dinh, kiem tra dau tieng Viet tren hinh",
          file=sys.stderr)
    return "Sans"


def tg(x):
    h = int(x // 3600)
    m = int(x % 3600 // 60)
    return f"{h}:{m:02d}:{x % 60:05.2f}"


def kich_thuoc(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0:s=x", str(video)], capture_output=True, text=True)
    w, h = r.stdout.strip().split("x")
    return int(w), int(h)


def dung_ass(proj, font, mau, mep, co_chu, rong, cao):
    tl = {s["id"]: s for s in json.loads((proj / "timeline.json").read_text(encoding="utf-8"))["scenes"]}
    g = json.loads((proj / "timeline_ghep.json").read_text(encoding="utf-8"))
    moc = {s["id"]: s for s in json.loads((proj / "moc-tu.json").read_text(encoding="utf-8"))["scenes"]}
    bgr = mau[4:6] + mau[2:4] + mau[0:2]   # ASS dung thu tu BGR
    hi = f"&H00{bgr.upper()}&"
    dau = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {rong}\nPlayResY: {cao}\nWrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,"
        "StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
        f"Style: Cap,{font},{co_chu},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,1,2,50,50,{mep},1\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,Effect,Text\n"
    )
    su_kien = []
    thieu = []
    for sid, m in moc.items():
        tu = m.get("sub") or []
        if not tu:
            continue
        if sid not in g["start"] or sid not in tl:
            thieu.append(sid)
            continue
        lech = g["start"][sid] - tl[sid]["start"]
        for i, w in enumerate(tu):
            s = w["s"] + lech
            e = (tu[i + 1]["s"] + lech) if i + 1 < len(tu) else w["e"] + lech + 0.25
            e = max(e, s + 0.06)
            if i == 0:
                s = max(0.0, s - 0.05)
            van = " ".join((f"{{\\c{hi}}}{x['w']}{{\\c&H00FFFFFF&}}" if j == i else x["w"]) for j, x in enumerate(tu))
            su_kien.append([s, e, van])
    if thieu:
        print(f"[CANH BAO] canh co trong moc-tu.json nhung khong co trong timeline: {', '.join(thieu)}", file=sys.stderr)
    # Khong de hai su kien hien cung luc (libass xep thanh hai dong): cat ket thuc o luc su kien ke tiep bat dau.
    # Hai loi cach nhau duoi 0,3 giay thi phan keo dai 0,25 giay cua tu cuoi va 0,05 giay hien som cua tu dau se chong.
    su_kien.sort(key=lambda x: x[0])
    dong = []
    for k, (s, e, van) in enumerate(su_kien):
        if k + 1 < len(su_kien):
            e = min(e, su_kien[k + 1][0])
        if e - s < 0.01:
            continue
        dong.append(f"Dialogue: 0,{tg(s)},{tg(e)},Cap,,,{van}")
    return dau + "\n".join(dong) + "\n", len(dong)


THOI_ASS = re.compile(r"^\d+:\d{2}:\d{2}\.\d{2}$")


def kiem_dinh_dang(noi_dung):
    """Moi dong Dialogue: Layer,Start,End,Style,Name,Effect,Text. Script nay luon de trong Name va Effect, nen
    Name hoac Effect khac rong nghia la dong bi thua truong (vd ban viet tay "Cap,,0,0,0,,chu" lam "0,0,," lot len hinh).
    Khong xet noi dung Text: phu de co the bat dau bang so thap phan kieu Viet ("2,5 met")."""
    loi = []
    for n, d in enumerate(noi_dung.splitlines(), 1):
        if not d.startswith("Dialogue:"):
            continue
        truong = d[len("Dialogue:"):].strip().split(",", 6)
        if len(truong) != 7:
            loi.append(f"dong {n}: {len(truong)} truong, can 7")
        elif not (THOI_ASS.match(truong[1]) and THOI_ASS.match(truong[2])):
            loi.append(f"dong {n}: moc thoi gian sai dinh dang")
        elif truong[4] or truong[5]:
            loi.append(f"dong {n}: truong Name/Effect khac rong (thua truong)")
    return loi


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--font")
    ap.add_argument("--mau-nhan", default="FFD166", help="mau tu dang doc, RRGGBB")
    ap.add_argument("--mep-duoi", type=int, default=120)
    ap.add_argument("--co-chu", type=int, default=46)
    ap.add_argument("--ass", default="phu-de-tung-tu.ass")
    ap.add_argument("--ghi", nargs=2, metavar=("VIDEO_VAO", "VIDEO_RA"))
    a = ap.parse_args()
    proj = Path(a.project)
    for f in ("moc-tu.json", "timeline.json", "timeline_ghep.json"):
        if not (proj / f).exists():
            sys.exit(f"[LOI] khong thay {proj / f} (chay tts.py, moc_tu.py, job.py dung truoc)")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", a.mau_nhan):
        sys.exit("[LOI] --mau-nhan la RRGGBB, vi du FFD166")
    rong, cao = (720, 1280)
    if a.ghi:
        rong, cao = kich_thuoc(a.ghi[0])
    font = chon_font(a.font)
    nd, n = dung_ass(proj, font, a.mau_nhan, a.mep_duoi, a.co_chu, rong, cao)
    loi = kiem_dinh_dang(nd)
    if loi:
        for x in loi[:10]:
            print(f"[LOI] {x}", file=sys.stderr)
        sys.exit("[CHAN] file ASS sai dinh dang")
    ra = proj / a.ass
    ra.write_text(nd, encoding="utf-8")
    print(f"[OK] {ra}: {n} su kien, font {font}")
    if a.ghi:
        vao, vra = (str(Path(x).resolve()) for x in a.ghi)
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", vao, "-vf", f"ass={a.ass}", "-c:v", "libx264", "-crf", "17",
               "-preset", "veryfast", "-c:a", "copy", "-movflags", "+faststart", vra]
        r = subprocess.run(cmd, cwd=str(proj))
        if r.returncode:
            sys.exit(f"[LOI] ffmpeg that bai (ma {r.returncode})")
        print(f"[OK] {vra}")


if __name__ == "__main__":
    main()
