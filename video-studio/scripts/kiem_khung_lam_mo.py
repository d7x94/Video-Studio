#!/usr/bin/env python3
"""Bang khung kiem lam mo: xuat anh goc canh anh da mo moi 0,1 giay va canh bao khi vung mo cham tem do hoac da.

Dung:
  python3 kiem_khung_lam_mo.py GOC.mp4 MO.mp4 RA_DIR [--tu 0] [--den 6] [--buoc 0.1] [--dong 8] [--nghiem]

Voi moi moc (moi --buoc giay trong [--tu, --den]):
  - so khung goc voi khung da mo, lay phan thay doi (vung da bi mo);
  - canh bao DO neu vung mo cham vao tem do (diem do bao hoa trong anh goc bi doi: tem "hang de vo");
  - canh bao DA neu phan lon vung mo la mau da (tay, mat) trong anh goc;
  - canh bao MO-LAN neu vung mo chiem qua nhieu khung hinh (--lan-max, mac dinh 0,35 dien tich khung).
Ra RA_DIR:
  bang-NN.png   moi hang la mot moc: [goc | da mo | phan bi mo to xanh, vien do = cham tem do, vien vang = cham da]
  bao-cao.json  so lieu tung moc va danh sach moc co canh bao
Script chi bao diem nghi ngo. Khong thay duoc mat nguoi: van phai xem bang anh va kiem tra phieu con sot
(script khong biet phieu o dau nen khong bao duoc "con lo phieu"; vung trang lon khong doi chi duoc danh dau neu
dat --vung-trang).
--vung-chu X0,X1,Y0,Y1: trong khung nay, tinh "diem chu" cua anh da mo: so o 16x16 nam trong vung sang, it sac (giay trang) co mat do canh cao
  (chu in, ma vach). Diem >= --chu-nguong (mac dinh 12) bao CON-CHU. Day la phep do thuc nghiem: tren video khui hang mau, anh goc co diem 10 den 155
  khi phieu vao khung, anh da mo da lam mo dung cach co diem toi da 9. Khong doc duoc ma vach hay QR (da thu cv2.barcode va QRCodeDetector: 0 lan nhan ra
  tren anh goc), nen chi la tin hieu "con nhieu net chu tren nen trang", khong phai bang chung doc duoc hay khong. Nguong can dat lai theo tung video.
--nghiem: thoat voi ma 1 neu co bat ky canh bao nao (de dung trong chuoi lenh).
--vung-trang X0,X1,Y0,Y1: trong khung nay, bao CON-TRANG (vien cam) neu mot thanh phan trang lon (V>190, S<45, >= --trang-min diem, mac dinh 1200;
  ha xuong 300 khi can bat manh phieu boc nho) cua anh da mo van sac net: do sac net (Laplacian) con hon --sac-ti-le (0,5) so voi anh goc, nghia la chu tren phieu
  chua bi lam mo. Vung trang lon nhung chi la nen trang tron (do sac net goc < --sac-min) khong bi bao.
Chi doc hinh (khong tieng). Yeu cau: ffmpeg, ffprobe, python3 co numpy va opencv-python.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np


def probe(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,duration:format=duration", "-of", "json", path])
    j = json.loads(out)
    s = j["streams"][0]
    dur = float(s.get("duration") or j["format"]["duration"])
    return int(s["width"]), int(s["height"]), dur


def frames(path, w, h, tu, den, buoc):
    """Doc cac khung o moc tu, tu+buoc, ... (bo loc fps) tu khoang [tu, den)."""
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{tu:.3f}", "-t", f"{den - tu:.3f}", "-i", path, "-an",
           "-vf", f"fps=1/{buoc}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        while True:
            b = p.stdout.read(w * h * 3)
            if len(b) < w * h * 3:
                break
            yield np.frombuffer(b, np.uint8).reshape(h, w, 3).copy()
    finally:
        p.kill()
        p.wait()


def red_mask(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    return (((hsv[..., 0] < 8) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 120) & (hsv[..., 2] > 90))


def skin_mask(bgr):
    ycc = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    return (ycc[..., 1] > 135) & (ycc[..., 1] < 173) & (ycc[..., 2] > 77) & (ycc[..., 2] < 127)


def changed_mask(goc, mo, nguong):
    d = cv2.absdiff(cv2.cvtColor(goc, cv2.COLOR_BGR2GRAY), cv2.cvtColor(mo, cv2.COLOR_BGR2GRAY))
    m = (d > nguong).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return m.astype(bool)


def diem_chu(bgr):
    """Diem chu: so o 16x16 trong vung sang it sac co mat do canh cao (chu in, ma vach tren giay trang)."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    sang = ((hsv[..., 2] > 150) & (hsv[..., 1] < 70)).astype(np.uint8)
    sang = cv2.morphologyEx(sang, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    grad = cv2.morphologyEx(g, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    edge = (grad > 45) & (sang > 0)
    h, w = edge.shape
    n = 0
    for y in range(0, h - 15, 16):
        for x in range(0, w - 15, 16):
            if edge[y:y + 16, x:x + 16].mean() > 0.18:
                n += 1
    return n


def draw_row(goc, mo, ch, do_hit, da_hit, nhan, tr, vung_trang_box):
    h, w = goc.shape[:2]
    ov = goc.copy()
    ov[ch] = (0.5 * ov[ch] + 0.5 * np.array([0, 200, 0])).astype(np.uint8)
    for mask, mau in ((do_hit, (0, 0, 255)), (da_hit, (0, 220, 255))):
        if mask.any():
            cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(ov, cs, -1, mau, max(2, w // 240))
    for (x, y, bw, bh) in vung_trang_box:
        cv2.rectangle(ov, (x, y), (x + bw, y + bh), (255, 128, 0), max(2, w // 240))
    row = np.hstack([goc, mo, ov])
    tl = tr / w
    row = cv2.resize(row, (int(row.shape[1] * tl), int(row.shape[0] * tl)), interpolation=cv2.INTER_AREA)
    bar = np.full((22, row.shape[1], 3), 255, np.uint8)
    mau = (0, 0, 200) if "CANH BAO" in nhan else (0, 0, 0)
    cv2.putText(bar, nhan, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, mau, 1, cv2.LINE_AA)
    return np.vstack([bar, row])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("goc")
    ap.add_argument("mo")
    ap.add_argument("ra")
    ap.add_argument("--tu", type=float, default=0.0)
    ap.add_argument("--den", type=float)
    ap.add_argument("--buoc", type=float, default=0.1)
    ap.add_argument("--dong", type=int, default=8, help="so hang moi bang anh")
    ap.add_argument("--rong-o", type=int, default=240, help="be rong moi o anh (diem anh)")
    ap.add_argument("--nguong", type=int, default=12, help="nguong chenh sang xam de coi la da bi mo")
    ap.add_argument("--do-min", type=int, default=150, help="so diem do bi doi toi thieu de bao do")
    ap.add_argument("--da-ti-le", type=float, default=0.35, help="ti le da trong vung mo de bao da")
    ap.add_argument("--da-min", type=int, default=600, help="vung mo toi thieu (diem) de xet da")
    ap.add_argument("--lan-max", type=float, default=0.35)
    ap.add_argument("--vung-trang", help="X0,X1,Y0,Y1")
    ap.add_argument("--trang-min", type=int, default=1200, help="so diem toi thieu cua thanh phan trang de xet con sot (mac dinh 1200; mang phieu boc nho thi ha xuong 300)")
    ap.add_argument("--sac-min", type=float, default=1.0, help="do sac net toi thieu cua vung trang goc de xet con sot")
    ap.add_argument("--sac-ti-le", type=float, default=0.5, help="vung trang con sac net hon ti le nay so voi goc thi bao con sot")
    ap.add_argument("--vung-chu", help="X0,X1,Y0,Y1")
    ap.add_argument("--chu-nguong", type=int, default=12, help="diem chu cua anh da mo tu muc nay bao CON-CHU")
    ap.add_argument("--nghiem", action="store_true")
    a = ap.parse_args()

    w, h, dur = probe(a.goc)
    w2, h2, _ = probe(a.mo)
    if (w, h) != (w2, h2):
        sys.exit(f"[LOI] hai video khac kich thuoc: {w}x{h} va {w2}x{h2}")
    den = a.den if a.den is not None else dur
    out = Path(a.ra)
    out.mkdir(parents=True, exist_ok=True)

    vt = None
    if a.vung_trang:
        vt = tuple(int(v) for v in a.vung_trang.split(","))

    vc = tuple(int(v) for v in a.vung_chu.split(",")) if a.vung_chu else None
    rows, bao_cao, canh_bao = [], [], []
    for i, (g, m) in enumerate(zip(frames(a.goc, w, h, a.tu, den, a.buoc), frames(a.mo, w, h, a.tu, den, a.buoc))):
        t = a.tu + i * a.buoc
        ch = changed_mask(g, m, a.nguong)
        n_ch = int(ch.sum())
        do = red_mask(g)
        do_hit = ch & do
        n_do_hit = int(do_hit.sum())
        da = skin_mask(g)
        da_hit = ch & da
        n_da = int(da_hit.sum())
        flags = []
        if n_do_hit >= a.do_min:
            flags.append("DO")
        if n_ch >= a.da_min and n_da / max(1, n_ch) >= a.da_ti_le:
            flags.append("DA")
        if n_ch / (w * h) >= a.lan_max:
            flags.append("MO-LAN")
        box = []
        if vt:
            x0, x1, y0, y1 = vt
            hsv = cv2.cvtColor(m[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
            tr = ((hsv[..., 2] > 190) & (hsv[..., 1] < 45)).astype(np.uint8)
            tr = cv2.morphologyEx(tr, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
            n, _, st, _ = cv2.connectedComponentsWithStats(tr)
            lg = np.abs(cv2.Laplacian(cv2.cvtColor(g, cv2.COLOR_BGR2GRAY), cv2.CV_32F))
            lm = np.abs(cv2.Laplacian(cv2.cvtColor(m, cv2.COLOR_BGR2GRAY), cv2.CV_32F))
            for k in range(1, n):
                if st[k][4] < a.trang_min:
                    continue
                bx, by, bw, bh = x0 + int(st[k][0]), y0 + int(st[k][1]), int(st[k][2]), int(st[k][3])
                sg = float(lg[by:by + bh, bx:bx + bw].mean())
                sm = float(lm[by:by + bh, bx:bx + bw].mean())
                # vung trang con chu sac net (chua mo): do sac net it giam so voi anh goc
                if sg >= a.sac_min and sm > a.sac_ti_le * sg:
                    box.append((bx, by, bw, bh))
            if box:
                flags.append("CON-TRANG")
        d_chu = None
        if vc:
            x0, x1, y0, y1 = vc
            d_goc, d_chu = diem_chu(g[y0:y1, x0:x1]), diem_chu(m[y0:y1, x0:x1])
            if d_chu >= a.chu_nguong:
                flags.append("CON-CHU")
        nhan = f"t={t:5.2f}s  mo {100 * n_ch / (w * h):4.1f}%  do {n_do_hit}  da {n_da}"
        if vc:
            nhan += f"  chu {d_goc}->{d_chu}"
        if flags:
            nhan += "  CANH BAO " + ",".join(flags)
            canh_bao.append(round(t, 2))
        rows.append(draw_row(g, m, ch, do_hit, da_hit, nhan, a.rong_o, box))
        bao_cao.append({"giay": round(t, 2), "mo_pct": round(100 * n_ch / (w * h), 2), "do_doi": n_do_hit,
                        "da_doi": n_da, "diem_chu_mo": d_chu, "canh_bao": flags})

    if not rows:
        sys.exit("[LOI] khong doc duoc khung hinh nao trong khoang da chon")
    ds = []
    for k in range(0, len(rows), a.dong):
        blk = rows[k:k + a.dong]
        wmax = max(r.shape[1] for r in blk)
        blk = [np.pad(r, ((0, 0), (0, wmax - r.shape[1]), (0, 0)), constant_values=255) for r in blk]
        p = out / f"bang-{k // a.dong + 1:02d}.png"
        cv2.imwrite(str(p), np.vstack(blk))
        ds.append(str(p))
    (out / "bao-cao.json").write_text(
        json.dumps({"goc": a.goc, "mo": a.mo, "buoc": a.buoc, "moc_canh_bao": canh_bao, "khung": bao_cao},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[OK] {len(rows)} moc, {len(ds)} bang anh trong {out}")
    if canh_bao:
        print(f"[CANH BAO] {len(canh_bao)} moc nghi ngo (xem bao-cao.json): " +
              ", ".join(f"{t}s" for t in canh_bao[:20]) + (" ..." if len(canh_bao) > 20 else ""))
        if a.nghiem:
            sys.exit(1)
    else:
        print("[OK] khong co canh bao tu dong; van phai xem bang anh bang mat")


if __name__ == "__main__":
    main()
