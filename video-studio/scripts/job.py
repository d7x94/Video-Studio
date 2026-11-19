#!/usr/bin/env python3
"""Dieu phoi job long tieng video co san qua mot file job.json: kiem, lam mo, sinh cau hinh ghep, dung lai.

Dung:
  python3 job.py kiem PROJECT       # kiem job.json (va doi chieu scenes.json neu co); thoat ma 1 neu co loi
  python3 job.py lam-mo PROJECT     # chay lan luot cac buoc lam_mo -> PROJECT/video_mo.mp4, roi xuat bang khung kiem lam mo
  python3 job.py sinh PROJECT       # ghi ghep.json va dong.json tu job.json
  python3 job.py dung PROJECT       # sinh, ghep loi, chuan am, chep ra output/, ghi chu len hinh neu job co "chu"

job.json (phan_tich_dau_vao.py tao ban mau, dien them tay):
{
 "phien_ban": 1, "ten": "obge", "video_goc": "goc.mov",
 "giong": "Hai Dang", "toc_do": 1.0,              # phai khop voi voice, speed trong scenes.json (canh bao neu lech)
 "anh_tinh": [{"tu": 53.6, "den": 83.4}],         # doan anh tinh do bang freezedetect
 "lam_mo": [                                      # chay theo thu tu, ket qua buoc truoc la dau vao buoc sau
   {"cach": "vung_trang", "tu": 0, "den": 2.97, "vung": "430:850", "le": 18},
   {"cach": "phieu_chat", "tu": 3.0, "den": 5.6, "vung": [200, 520, 500, 740]},
   {"cach": "tay", "khung": [[2.3, 210, 500, 370, 690], [2.5, 190, 480, 360, 650]]}],
 "canh": {                                        # moi canh trong scenes.json mot muc, chi mot trong hai
   "s01": {"cue": 0.3},                           #   cue: giay bat dau loi tren video goc
   "s11": {"giu_hinh": {"hien_ro": 76.13, "dong_bang": 78.64}}},   # keo dai anh tinh bang cach giu khung hinh
 "chu": [[42.6, 46.0, "Chu chinh", "Nguon: ..."]],   # chu ghi tren hinh (chu_may_chu.py), tuy chon
 "nhac": {"kieu": "khong", "muc": -13},           # kieu nhac nen cua nhac_nen.py, "khong" = khong them nhac
 "tung_tu": false,                                # true: them output/<ten>-phu-de-tung-tu.mp4 (phu de tung tu, tu dang doc doi mau);
                                                  # co ca "chu" thi them output/<ten>-chu-phu-de-tung-tu.mp4 (du ca hai)
 "khoang_truoc": 0.15, "khoang_sau": 0.35         # tuy chon
}
Duong dan trong job.json tuong doi PROJECT (hoac tuyet doi). Tat ca script goi ben duoi la script san co:
lam_mo_vung_trang.py, lam_mo_phieu_chat.py, lam_mo_tay.py, kiem_khung_lam_mo.py, ghep_loi_video_co_san.py,
dung_lai_video_co_san.sh, chu_may_chu.py; job.py khong lam them viec nao khac ngoai gom tham so lai mot cho.
Gioi han: job.py khong viet loi, khong chon vung che, khong chon nguon: nhung viec do van la cua nguoi duyet.
Moi buoc lam mo van phai xem bang anh kiem (qa/lam-mo/bang-NN.png) truoc khi ghep.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACH = ("vung_trang", "phieu_chat", "tay")


def doc(proj):
    p = proj / "job.json"
    if not p.exists():
        sys.exit(f"[LOI] chua co {p}: chay phan_tich_dau_vao.py hoac tao tay theo mau trong --help")
    return json.loads(p.read_text(encoding="utf-8"))


def duong(proj, s):
    p = Path(s)
    return p if p.is_absolute() else proj / p


def kiem_tra(proj, job):
    loi, cb = [], []
    if not job.get("video_goc"):
        loi.append("thieu video_goc")
    elif not duong(proj, job["video_goc"]).exists():
        loi.append(f"khong thay video_goc: {job['video_goc']}")
    for i, b in enumerate(job.get("lam_mo", []), 1):
        t = f"lam_mo[{i}]"
        c = b.get("cach")
        if c not in CACH:
            loi.append(f"{t}: cach phai la mot trong {', '.join(CACH)}")
            continue
        if c in ("vung_trang", "phieu_chat"):
            if not isinstance(b.get("den"), (int, float)):
                loi.append(f"{t}: thieu den (giay)")
            elif b.get("tu", 0) >= b["den"]:
                loi.append(f"{t}: tu phai nho hon den")
        if c == "phieu_chat":
            v = b.get("vung")
            if v is not None and not (isinstance(v, list) and len(v) == 4):
                loi.append(f"{t}: vung phieu_chat la [X0, X1, Y0, Y1]")
        if c == "tay":
            k = b.get("khung")
            if not k or any(not (isinstance(x, list) and len(x) == 5) for x in k):
                loi.append(f"{t}: khung la danh sach [giay, x0, y0, x1, y1]")
            elif [x[0] for x in k] != sorted(x[0] for x in k):
                loi.append(f"{t}: khung phai xep theo thoi gian")
    sc_path = proj / "scenes.json"
    canh = job.get("canh", {})
    if sc_path.exists():
        sc = json.loads(sc_path.read_text(encoding="utf-8"))
        ids = [s["id"] for s in sc["scenes"]]
        for k in ids:
            if k not in canh:
                loi.append(f"canh {k} co trong scenes.json nhung chua co moc trong job.json")
        for k in canh:
            if k not in ids:
                loi.append(f"canh {k} co trong job.json nhung khong co trong scenes.json")
        if job.get("giong") and sc.get("voice") and job["giong"] != sc["voice"]:
            cb.append(f"giong job.json ({job['giong']}) khac scenes.json ({sc['voice']})")
        if job.get("toc_do") and sc.get("speed") and abs(float(job["toc_do"]) - float(sc["speed"])) > 1e-6:
            cb.append(f"toc_do job.json ({job['toc_do']}) khac scenes.json ({sc['speed']})")
    for k, v in canh.items():
        if ("cue" in v) == ("giu_hinh" in v):
            loi.append(f"canh {k}: dien dung mot trong cue hoac giu_hinh")
            continue
        if "cue" in v and not isinstance(v["cue"], (int, float)):
            loi.append(f"canh {k}: cue phai la so giay")
        if "giu_hinh" in v:
            g = v["giu_hinh"]
            if not all(isinstance(g.get(x), (int, float)) for x in ("hien_ro", "dong_bang")):
                loi.append(f"canh {k}: giu_hinh can hien_ro va dong_bang (giay)")
            elif g["dong_bang"] < g["hien_ro"]:
                loi.append(f"canh {k}: dong_bang phai sau hien_ro")
            else:
                trong = any(a["tu"] - 0.3 <= g["hien_ro"] and g["dong_bang"] <= a["den"] + 0.05
                            for a in job.get("anh_tinh", []))
                if job.get("anh_tinh") and not trong:
                    cb.append(f"canh {k}: hien_ro/dong_bang khong nam trong doan anh tinh nao (anh_tinh)")
    for i, c in enumerate(job.get("chu", []), 1):
        if not (isinstance(c, list) and len(c) == 4 and c[0] < c[1]):
            loi.append(f"chu[{i}]: can [bat_dau, ket_thuc, chu_chinh, dong_nguon] voi bat_dau < ket_thuc")
    return loi, cb


def chay(cmd):
    print("$ " + " ".join(str(x) for x in cmd), flush=True)
    r = subprocess.run([str(x) for x in cmd])
    if r.returncode:
        sys.exit(f"[LOI] lenh tren that bai (ma {r.returncode})")


def thoi_luong_file(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def uoc_thoi_luong(proj, job):
    """Uoc tong thoi luong sau khi giu khung hinh (cung cong thuc ghep_loi_video_co_san.py). None neu thieu tieng hoac video."""
    gv = duong(proj, job.get("video_goc", ""))
    if not gv.is_file() or not job.get("canh"):
        return None
    goc = thoi_luong_file(gv)
    truoc, sau = job.get("khoang_truoc", 0.15), job.get("khoang_sau", 0.35)
    giu = sorted(((k, v["giu_hinh"]) for k, v in job["canh"].items() if "giu_hinh" in v), key=lambda x: x[1]["hien_ro"])
    chi_tiet, dich = [], 0.0
    for sid, g in giu:
        w = proj / "audio" / f"{sid}.wav"
        d = thoi_luong_file(w) if w.exists() else None
        if goc is None or d is None:
            return None
        ext = max(0.0, g["hien_ro"] + dich + truoc + d + sau - (g["dong_bang"] + dich))
        chi_tiet.append((sid, ext))
        dich += ext
    return goc, dich, chi_tiet


def cmd_kiem(proj, job, im=False):
    loi, cb = kiem_tra(proj, job)
    for x in cb:
        print(f"[CANH BAO] {x}", file=sys.stderr)
    if loi:
        for x in loi:
            print(f"[LOI] {x}", file=sys.stderr)
        sys.exit(f"[CHAN] {len(loi)} loi trong job.json")
    if not im:
        print("[OK] job.json hop le")
        u = uoc_thoi_luong(proj, job)
        if u and u[0] is not None:
            goc, them, ct = u
            dai = ", ".join(f"{k} +{e:.1f}s" for k, e in sorted(ct, key=lambda x: -x[1])[:3] if e >= 0.05)
            print(f"[THONG TIN] thoi luong du kien {goc + them:.1f}s (video goc {goc:.1f}s, giu hinh them {them:.1f}s"
                  + (f"; keo dai nhieu nhat: {dai}" if dai else "") + "). Muon ngan hon thi rut loi cac canh giu hinh")


def cmd_lam_mo(proj, job):
    cmd_kiem(proj, job, im=True)
    buoc = job.get("lam_mo", [])
    goc = duong(proj, job["video_goc"])
    if not buoc:
        print("[OK] job khong co buoc lam mo; bo qua")
        return
    wd = proj / "lam_mo"
    wd.mkdir(exist_ok=True)
    cur = goc
    tu_min, den_max, vung_kiem = 1e9, 0.0, None
    for i, b in enumerate(buoc, 1):
        nxt = wd / f"b{i}.mp4"
        c = b["cach"]
        if c == "vung_trang":
            cmd = [sys.executable, HERE / "lam_mo_vung_trang.py", cur, nxt, "--tu", b.get("tu", 0), "--den", b["den"]]
            if b.get("vung"):
                cmd += ["--vung", b["vung"]]
            if b.get("le") is not None:
                cmd += ["--le", b["le"]]
            tu_min, den_max = min(tu_min, b.get("tu", 0)), max(den_max, b["den"])
        elif c == "phieu_chat":
            cmd = [sys.executable, HERE / "lam_mo_phieu_chat.py", cur, nxt, "--tu", b.get("tu", 0), "--den", b["den"]]
            if b.get("vung"):
                cmd += ["--vung", ",".join(str(x) for x in b["vung"])]
                vung_kiem = vung_kiem or ",".join(str(x) for x in b["vung"])
            tu_min, den_max = min(tu_min, b.get("tu", 0)), max(den_max, b["den"])
        else:
            kp = wd / f"khung{i}.json"
            kp.write_text(json.dumps(b["khung"]), encoding="utf-8")
            cmd = [sys.executable, HERE / "lam_mo_tay.py", cur, nxt, "--khung", kp]
            tu_min, den_max = min(tu_min, b["khung"][0][0]), max(den_max, b["khung"][-1][0])
        chay(cmd)
        cur = nxt
    final = proj / "video_mo.mp4"
    final.write_bytes(Path(cur).read_bytes())
    print(f"[OK] {final}")
    cmd = [sys.executable, HERE / "kiem_khung_lam_mo.py", goc, final, proj / "qa" / "lam-mo",
           "--tu", max(0.0, tu_min), "--den", den_max + 0.5]
    if vung_kiem:
        cmd += ["--vung-trang", vung_kiem]
    chay(cmd)
    print(f"[VIEC CON LAI] xem {proj / 'qa' / 'lam-mo'}/bang-*.png bang mat truoc khi ghep")


def cmd_sinh(proj, job):
    cmd_kiem(proj, job, im=True)
    cue, giu = {}, []
    for k, v in job["canh"].items():
        if "cue" in v:
            cue[k] = v["cue"]
        else:
            giu.append({"id": k, **v["giu_hinh"]})
    giu.sort(key=lambda g: g["hien_ro"])
    video = "video_mo.mp4" if job.get("lam_mo") else job["video_goc"]
    cfg = {"video": video, "cue": cue, "giu_hinh": giu,
           "khoang_truoc": job.get("khoang_truoc", 0.15), "khoang_sau": job.get("khoang_sau", 0.35)}
    (proj / "ghep.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    if job.get("chu"):
        (proj / "dong.json").write_text(json.dumps(job["chu"], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[OK] ghep.json ({len(cue)} cue, {len(giu)} giu_hinh)" + (", dong.json" if job.get("chu") else ""))


def cmd_dung(proj, job):
    cmd_sinh(proj, job)
    nhac = job.get("nhac", {"kieu": "khong", "muc": -13})
    ten = job.get("ten") or "video"
    chay(["bash", HERE / "dung_lai_video_co_san.sh", proj, "--kieu", nhac.get("kieu", "khong"),
          "--muc", nhac.get("muc", -13), "--ten", ten] + (["--tung-tu"] if job.get("tung_tu") else []))
    if job.get("chu"):
        chay([sys.executable, HERE / "chu_may_chu.py", proj / "dong.json", proj / "chu.ass",
              "--vao", proj / "renders" / "final_portrait.mp4", "--ra", proj / "output" / f"{ten}-chu.mp4"])
        if job.get("tung_tu"):
            # ban du ca hai: chu ghi tren hinh (dai nen phia tren) chong len ban da co phu de tung tu (day khung)
            chay([sys.executable, HERE / "chu_may_chu.py", proj / "dong.json", proj / "chu.ass",
                  "--vao", proj / "output" / f"{ten}-phu-de-tung-tu.mp4",
                  "--ra", proj / "output" / f"{ten}-chu-phu-de-tung-tu.mp4"])


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("kiem", "lam-mo", "sinh", "dung"):
        sys.exit(__doc__)
    cmd, proj = sys.argv[1], Path(sys.argv[2])
    job = doc(proj)
    {"kiem": cmd_kiem, "lam-mo": cmd_lam_mo, "sinh": cmd_sinh, "dung": cmd_dung}[cmd](proj, job)


if __name__ == "__main__":
    main()
