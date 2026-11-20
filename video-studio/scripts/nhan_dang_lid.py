#!/usr/bin/env python3
"""Che do dich: nhan dang ngon ngu bang FireRedLID tren cac khuc co tieng noi (doi chieu voi Whisper).

Dung (thuong do chep_loi_goc.py --lid goi, chay tien trinh rieng de khong giu ca hai mo hinh trong RAM):
  python3 nhan_dang_lid.py VIDEO --doan noi.json --ra lid.json [--luong 2]

  noi.json   danh sach [bat_dau, ket_thuc] (giay) cac khuc co tieng noi, lay tu VAD cua Whisper
  lid.json   ket qua: tung khuc (ngon ngu, phuong ngu, do tin), tong giay theo ngon ngu, ngon ngu chon

Cach bau: khuc dai hon 30 giay cat nho (moi phan toi da 30 giay), bo phan duoi 1 giay; chi tinh phan co do tin
>= 0,8 (khuc khong loi nhu go phim, nhac cho ket qua bua voi do tin thap); cong thoi luong theo ngon ngu, chon ngon
ngu nhieu giay nhat. Ma ngon ngu cua FireRedLID cung kieu Whisper (en, zh, yue, jw, su...); nhan "zh mandarin" thi
phan dau la ngon ngu, phan sau la phuong ngu.

Mo hinh: scripts/lay_asr.py lid (khoang 3,6 GB, GitHub Release, du phong HuggingFace, kiem sha256).
Ma suy luan: scripts/vendor/fireredlid (chep nguyen ban tu FireRedASR2S, xem vendor/fireredlid/NGUON.md).
Checkpoint nap bang torch.load(mmap=True): nap cach goc lam tran RAM o workspace 7 GB (do 2026-11-20).
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

SR = 16000
TOI_DA = 30.0
TOI_THIEU = 1.0
NGUONG_TIN = 0.8
SCRIPTS = Path(__file__).resolve().parent


def doc_tieng(video: str) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", str(SR),
                        "-f", "s16le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.int16).copy()


def chia_khuc(noi):
    out = []
    for s, e in noi:
        t = s
        while e - t >= TOI_THIEU:
            out.append((t, min(e, t + TOI_DA)))
            t += TOI_DA
    return out


def bau(khuc):
    tong = {}
    for k in khuc:
        if k["tin"] >= NGUONG_TIN and k["ngon_ngu"]:
            tong[k["ngon_ngu"]] = tong.get(k["ngon_ngu"], 0.0) + (k["den"] - k["tu"])
    tong = {k: round(v, 2) for k, v in sorted(tong.items(), key=lambda x: -x[1])}
    tin_giay = sum(tong.values())
    chon = next(iter(tong), None)
    return {"chon": chon, "ty_le": round(tong[chon] / tin_giay, 3) if chon else None,
            "giay_tin_cay": round(tin_giay, 2), "giay_tieng_noi": round(sum(k["den"] - k["tu"] for k in khuc), 2),
            "tong": tong}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--doan", required=True, help="JSON [[bat_dau, ket_thuc], ...] cac khuc co tieng noi")
    ap.add_argument("--ra", required=True)
    ap.add_argument("--luong", type=int, default=2)
    a = ap.parse_args()

    try:
        import torch
    except ImportError:
        sys.exit("[LOI] Chua cai torch cho FireRedLID. Chay: bash SKILL/scripts/setup.sh --lid")
    torch.set_num_threads(a.luong)
    goc_load = torch.load
    torch.load = lambda *x, **k: goc_load(*x, **{**k, "mmap": True})
    sys.path.insert(0, str(SCRIPTS / "vendor"))
    from fireredlid import FireRedLid, FireRedLidConfig

    r = subprocess.run([sys.executable, str(SCRIPTS / "lay_asr.py"), "lid"], capture_output=True, text=True)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        sys.exit(r.returncode)
    model_dir = r.stdout.strip().splitlines()[-1]

    audio = doc_tieng(a.video)
    phan = chia_khuc(json.loads(Path(a.doan).read_text(encoding="utf-8")))
    t0 = time.time()
    model = FireRedLid.from_pretrained(model_dir, FireRedLidConfig(use_gpu=False, use_half=False))
    t_nap = time.time() - t0
    khuc = []
    t1 = time.time()
    for i, (s, e) in enumerate(phan):
        mau = audio[int(s * SR):int(e * SR)]
        kq = model.process([f"k{i:03d}"], [(SR, mau)])[0]
        nhan = (kq.get("lang") or "").split()
        khuc.append({"tu": round(s, 2), "den": round(e, 2), "ngon_ngu": nhan[0] if nhan else "",
                     "phuong_ngu": " ".join(nhan[1:]), "tin": float(kq.get("confidence", 0.0))})
    kq = {"mo_hinh": "FireRedLID", "nguong_tin": NGUONG_TIN, "giay_nap": round(t_nap, 1),
          "giay_chay": round(time.time() - t1, 1), "khuc": khuc, **bau(khuc)}
    Path(a.ra).write_text(json.dumps(kq, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[OK] FireRedLID: {kq['chon']} ({kq['giay_tin_cay']}/{kq['giay_tieng_noi']} giay tin cay), "
          f"{len(khuc)} khuc, chay {kq['giay_chay']} giay", file=sys.stderr)


if __name__ == "__main__":
    main()
