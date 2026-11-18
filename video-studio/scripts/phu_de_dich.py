#!/usr/bin/env python3
"""Che do dich: ban dich theo doan, kiem ban dich, xuat phu de .srt va ghi phu de cung vao video.

Dung:
  python3 phu_de_dich.py khoi PROJECT                 # tao dich/ban-dich.json tu dich/chep-goc.json (truong "dich" de trong)
  python3 phu_de_dich.py kiem PROJECT [--cps 15]      # kiem ban dich; thoat 1 khi co loi chan
  python3 phu_de_dich.py srt PROJECT [--song-ngu]     # ghi output/phu-de-vi.srt (song ngu: them dong goc phia duoi)
  python3 phu_de_dich.py ghi PROJECT VIDEO [--ra OUT.mp4] [--song-ngu] [--font Inter]
                                                      # kiem, ghi .srt, roi ghi phu de cung vao hinh (giu nguyen tieng)

dich/ban-dich.json: {"phien_ban": 1, "ngon_ngu_goc": "en", "doan": [{"id", "start", "end", "goc", "dich",
  "nguoi_noi" (tuy chon), "bo" (tuy chon, true = khong hien phu de doan nay)}]}
Nguoi dich (dieu phoi hoac agent) dien "dich"; duoc gop hoac tach doan, sua start/end, mien la khong chong nhau.

Kiem (loi chan):
  - doan thieu "dich", start >= end, doan chong nhau, vuot thoi luong video
  - chu so trong loi goc (vd 10, 2024, 3.5) khong co trong ban dich: dich so phai giu nguyen hoac ghi ro (chi so chu so
    A-rap; so viet bang chu Han hay chu cai thi nguoi kiem dich doc lai)
  - phu de qua 2 dong sau khi ngat dong
  - chu chua o dang NFC (dau to hop roi lam lech dau khi ghi)
Doan doc nhanh hon --cps duoc keo dai thoi gian hien vao khoang trong phia sau, toi da --keo-dai giay (mac dinh 1,5),
khong cham doan sau; chi ap khi xuat, khong sua ban-dich.json.
Kiem (canh bao): toc do doc (sau khi keo dai) > --cps ky tu/giay (khong tinh khoang trang; mac dinh 15 theo doc_chu.py, chua do rieng cho
phu de tieng Viet), doan hien duoi 1 giay, doan goc co co nghi-bia hay tin-thap ma van giu.

Video goc da co phu de cung (vd song ngu Trung Anh): xem dich/qa-phu-de.png sau lenh ghi; neu chu chong nhau thi
--vi-tri tren, hoac --che-day 0.2 (lam mo dai day khung cao 20% roi ghi phu de dich len do).
Phu de cung: file .ass cung kich thuoc video, chu trang vien den, dat giua duoi; co chu = 4,5% chieu cao khung (khung doc
3,5%), ngat dong theo chieu rong. Ma hoa lai hinh libx264 crf 18, chep nguyen luong tieng.
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path


def nap(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def ghi_json(p: Path, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def so(text):
    return set(re.sub(r"(?<=\d)[,.](?=\d{3}\b)", "", m) for m in re.findall(r"\d+(?:[.,]\d+)*", text or ""))


def so_ky_tu(text):
    return sum(1 for c in text if not c.isspace())


def ngat_dong(text, toi_da):
    words, dong, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > toi_da:
            dong.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        dong.append(cur)
    if len(dong) == 2:   # can bang hai dong cho de doc
        allw = text.split()
        best = min(range(1, len(allw)), key=lambda i: abs(len(" ".join(allw[:i])) - len(" ".join(allw[i:]))))
        a, b = " ".join(allw[:best]), " ".join(allw[best:])
        if len(a) <= toi_da and len(b) <= toi_da:
            dong = [a, b]
    return dong


def kich_thuoc(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", str(video)],
                         capture_output=True, text=True, check=True)
    d = json.loads(out.stdout)
    st = d["streams"][0]
    return st["width"], st["height"], float(d["format"]["duration"])


def bo_cuc(w, h):
    co = round(h * (0.035 if h > w else 0.045))
    toi_da = max(16, int(w * 0.88 / (co * 0.52)))   # 0,52 em: be rong trung binh chu Latin co dau o phong sans
    return co, toi_da


def doan_hien(proj, cps, keo, dur=None):
    """Doan se hien, theo thu tu; doan doc nhanh qua cps duoc keo dai vao khoang trong phia sau (toi da keo giay,
    cach doan sau 0,1 giay, khong qua thoi luong video). Khong ghi lai ban-dich.json."""
    bd = nap(proj / "dich" / "ban-dich.json")
    doan = [dict(d) for d in bd["doan"] if not d.get("bo")]
    for i, d in enumerate(doan):
        dich = (d.get("dich") or "").strip()
        if not dich or keo <= 0:
            continue
        can = so_ky_tu(dich) / cps - (d["end"] - d["start"])
        if can <= 0:
            continue
        tran = doan[i + 1]["start"] - 0.1 if i + 1 < len(doan) else (dur if dur else d["end"] + keo)
        moi = min(d["end"] + min(can, keo), tran)
        if moi > d["end"]:
            d["keo_tu"] = d["end"]
            d["end"] = round(moi, 2)
    return bd, doan


def kiem(proj, cps, toi_da=None, dur=None, keo=1.5):
    bd, doan = doan_hien(proj, cps, keo, dur)
    loi, canh = [], []
    toi_da = toi_da or 42
    prev_end = 0.0
    for d in doan:
        i, dich, goc = d["id"], (d.get("dich") or "").strip(), d.get("goc", "")
        if not dich:
            loi.append(f"{i}: thieu ban dich")
            continue
        if unicodedata.normalize("NFC", dich) != dich:
            loi.append(f"{i}: chu chua o dang NFC")
        if d["start"] >= d["end"]:
            loi.append(f"{i}: start >= end")
        if d["start"] < prev_end - 0.01:
            loi.append(f"{i}: chong voi doan truoc ({d['start']} < {prev_end})")
        prev_end = max(prev_end, d["end"])
        if dur and d["end"] > dur + 0.05:
            loi.append(f"{i}: vuot thoi luong video ({d['end']} > {dur:.2f})")
        thieu = so(goc) - so(dich)
        if thieu:
            loi.append(f"{i}: so {sorted(thieu)} trong loi goc khong co trong ban dich")
        if len(ngat_dong(dich, toi_da)) > 2:
            loi.append(f"{i}: qua 2 dong (toi da {toi_da} ky tu moi dong), rut gon hoac tach doan")
        t = d["end"] - d["start"]
        if t > 0 and so_ky_tu(dich) / t > cps + 0.05:
            canh.append(f"{i}: doc nhanh {so_ky_tu(dich) / t:.1f} ky tu/giay > {cps}"
                        + (f" (da keo dai tu {d['keo_tu']} den {d['end']}, van thieu)" if "keo_tu" in d else "")
                        + ": rut gon ban dich")
        if t < 1.0:
            canh.append(f"{i}: hien {t:.2f} giay < 1 giay")
        if set(d.get("co", [])) & {"nghi-bia", "tin-thap"}:
            canh.append(f"{i}: doan goc co co {d['co']}, da duoc nguoi nghe lai chua?")
    bo = [d["id"] for d in bd["doan"] if d.get("bo")]
    return loi, canh, bo


def srt_t(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def ass_t(x):
    cs = int(round(x * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ghi_srt(doan, proj, song_ngu, toi_da):
    rows = []
    for d in doan:
        txt = "\n".join(ngat_dong(d["dich"].strip(), toi_da))
        if song_ngu:
            txt += "\n" + d["goc"].strip()
        rows.append(f"{len(rows) + 1}\n{srt_t(d['start'])} --> {srt_t(d['end'])}\n{txt}\n")
    out = proj / "output"
    out.mkdir(exist_ok=True)
    p = out / "phu-de-vi.srt"
    p.write_text("\n".join(rows), encoding="utf-8")
    return p, len(rows)


def ghi_ass(doan, proj, w, h, font, song_ngu, tren=False):
    co, toi_da = bo_cuc(w, h)
    canh = 8 if tren else 2
    le = round(h * (0.12 if h > w else 0.06))
    vien = max(2, round(co * 0.08))
    hdr = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
           "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,"
           "Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,"
           "MarginV,Encoding\n"
           f"Style: Dich,{font},{co},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,{vien},1,{canh},"
           f"{round(w * 0.06)},{round(w * 0.06)},{le},1\n"
           f"Style: Goc,{font},{round(co * 0.7)},&H00D0D0D0,&H00D0D0D0,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,"
           f"{max(1, vien - 1)},1,{canh},{round(w * 0.06)},{round(w * 0.06)},{le},1\n\n"
           "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    ev = []
    xuong = "\\N"
    for d in doan:
        dong = xuong.join(ngat_dong(d["dich"].strip(), toi_da))
        t0, t1 = ass_t(d["start"]), ass_t(d["end"])
        if song_ngu:   # dong goc nho phia duoi, ban dich day len tren
            ev.append(f"Dialogue: 0,{t0},{t1},Dich,,0,0,{le + round(co * 0.9)},,{dong}")
            ev.append(f"Dialogue: 0,{t0},{t1},Goc,,0,0,{le},,{d['goc'].strip()}")
        else:
            ev.append(f"Dialogue: 0,{t0},{t1},Dich,,0,0,0,,{dong}")
    p = proj / "dich" / "phu-de-vi.ass"
    p.write_text(hdr + "\n".join(ev) + "\n", encoding="utf-8")
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lenh", choices=["khoi", "kiem", "srt", "ghi"])
    ap.add_argument("project")
    ap.add_argument("video", nargs="?")
    ap.add_argument("--ra")
    ap.add_argument("--cps", type=float, default=15.0)
    ap.add_argument("--keo-dai", type=float, default=1.5,
                    help="giay toi da keo dai doan doc nhanh vao khoang trong phia sau (0 = tat)")
    ap.add_argument("--song-ngu", action="store_true")
    ap.add_argument("--font", default="Inter")
    ap.add_argument("--fontsdir", default="/usr/share/fonts/opentype/inter")
    ap.add_argument("--vi-tri", choices=["duoi", "tren"], default="duoi",
                    help="video goc da co phu de cung o duoi thi dat phu de dich len tren, hoac dung --che-day")
    ap.add_argument("--che-day", type=float, default=0.0,
                    help="ti le chieu cao dai day khung lam mo (vd 0.2) de che phu de cung san co cua video goc")
    a = ap.parse_args()
    proj = Path(a.project)

    if a.lenh == "khoi":
        cg = nap(proj / "dich" / "chep-goc.json")
        p = proj / "dich" / "ban-dich.json"
        if p.exists():
            sys.exit(f"[LOI] {p} da co; xoa tay neu muon tao lai (tranh mat ban dich)")
        ghi_json(p, {"phien_ban": 1, "ngon_ngu_goc": cg["ngon_ngu"]["chon"],
                     "doan": [{"id": d["id"], "start": d["start"], "end": d["end"], "goc": d["goc"], "dich": "",
                               "co": d["co"]} for d in cg["doan"]]})
        print(f"[OK] {p}: {len(cg['doan'])} doan, dien truong \"dich\"")
        return

    w = h = dur = None
    if a.video:
        w, h, dur = kich_thuoc(a.video)
    toi_da = bo_cuc(w, h)[1] if w else 42
    loi, canh, bo = kiem(proj, a.cps, toi_da, dur, a.keo_dai)
    _, doan = doan_hien(proj, a.cps, a.keo_dai, dur)
    keo = [d["id"] for d in doan if "keo_tu" in d]
    if keo:
        print(f"Keo dai thoi gian hien (doc nhanh): {', '.join(keo)}")
    for c in canh:
        print(f"[CANH BAO] {c}")
    for l in loi:
        print(f"[LOI] {l}")
    if bo:
        print(f"Bo khong hien: {', '.join(bo)}")
    if loi:
        sys.exit(1)
    if a.lenh == "kiem":
        print(f"[OK] ban dich dat ({len(canh)} canh bao)")
        return

    srt, n = ghi_srt(doan, proj, a.song_ngu, toi_da)
    print(f"[OK] {srt}: {n} dong phu de")
    if a.lenh == "srt":
        return
    if not a.video:
        sys.exit("[LOI] lenh ghi can VIDEO")
    ass = ghi_ass(doan, proj, w, h, a.font, a.song_ngu, a.vi_tri == "tren")
    ra = Path(a.ra) if a.ra else proj / "output" / (Path(a.video).stem + "-phu-de-vi.mp4")
    fd = f":fontsdir={a.fontsdir}" if a.fontsdir and Path(a.fontsdir).is_dir() else ""
    if not 0 <= a.che_day < 0.5:
        sys.exit("[LOI] --che-day trong khoang 0 den 0.5")
    if a.che_day:
        r = a.che_day
        loc = (f"[0:v:0]split[g][d];[d]crop=iw:ih*{r}:0:ih*(1-{r}),boxblur=20:3[m];"
               f"[g][m]overlay=0:H*(1-{r})[c];[c]ass={ass}{fd}[v]")
    else:
        loc = f"[0:v:0]ass={ass}{fd}[v]"
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-map", "0:a?",
                           "-filter_complex", loc, "-map", "[v]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                           "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(ra)])
    w2, h2, dur2 = kich_thuoc(ra)
    if (w2, h2) != (w, h) or abs(dur2 - dur) > 0.2:
        sys.exit(f"[LOI] video ra lech: {w2}x{h2} {dur2:.2f}s so voi {w}x{h} {dur:.2f}s")
    print(f"[OK] {ra} ({w2}x{h2}, {dur2:.1f} giay)")
    # Bang khung kiem: giua 6 dong phu de rai deu, de nguoi duyet thay chu co de len chu san co cua video khong
    chon = [doan[round(i * (len(doan) - 1) / 5)] for i in range(min(6, len(doan)))]
    anh = proj / "dich" / "qa-phu-de.png"
    vao = []
    for d in chon:
        vao += ["-ss", f"{(d['start'] + d['end']) / 2:.2f}", "-i", str(ra)]
    n = len(chon)
    cot = 3 if n > 3 else n
    loc2 = "".join(f"[{i}:v]scale=640:-2,setpts=PTS-STARTPTS[k{i}];" for i in range(n))
    vt = [("+".join(["w0"] * (i % cot)) or "0") + "_" + ("+".join(["h0"] * (i // cot)) or "0") for i in range(n)]
    loc2 += "".join(f"[k{i}]" for i in range(n)) + f"xstack=inputs={n}:layout=" + "|".join(vt) + "[o]"
    if n == 1:
        loc2 = "[0:v]scale=640:-2[o]"
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", *vao, "-filter_complex", loc2, "-map", "[o]",
                           "-frames:v", "1", str(anh)])
    print(f"[OK] {anh}: khung kiem phu de (xem chu dich co de len phu de san co, logo, mat nguoi khong)")


if __name__ == "__main__":
    main()
