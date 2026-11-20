#!/usr/bin/env python3
"""Che do dich: nhan dang ngon ngu va chep loi goc cua video bang Whisper (faster-whisper), kem co nghi ngo.

Dung:
  python3 chep_loi_goc.py VIDEO PROJECT                     # tu nhan dang ngon ngu, ban medium, bat VAD
  python3 chep_loi_goc.py VIDEO PROJECT --ngon-ngu en       # da biet ngon ngu: bo buoc nhan dang
  python3 chep_loi_goc.py VIDEO PROJECT --ban small         # nhanh hon, de bia cau hon (xem references/che-do-dich.md)
  python3 chep_loi_goc.py VIDEO PROJECT --ban large-v3      # lon nhat (khoang 3,1 GB), cham hon medium
  python3 chep_loi_goc.py VIDEO PROJECT --khong-vad         # khong loc khoang lang (de bia cau o doan nhac, go phim)
  python3 chep_loi_goc.py VIDEO PROJECT --lid               # doi chieu ngon ngu voi FireRedLID (can setup.sh --lid)

Dau ra trong PROJECT/dich/:
  chep-goc.json   ngon ngu (chon, xac suat tung khuc, chac chan hay khong), cac doan (id, start, end, goc,
                  avg_logprob, no_speech, co), khoang_trong (doan dai khong co loi, de nguoi dung nghe lai)
  chep-goc.md     bang de nguoi dung duyet (cong duyet ban chep goc)

Nhan dang ngon ngu: cat khuc 30 giay, chi dung khuc co it nhat 3 giay tieng noi theo VAD (khuc chi co nhac, go
phim cho ket qua sai), nhan dang tren moi ngon ngu (khong ep vao danh sach), cong xac suat cac khuc. Chac chan khi
moi khuc cung mot ngon ngu, trung binh >= 0,8 va cach ngon ngu thu hai >= 0,3. Khong chac chan, hoac ngon ngu ngoai
danh sach ho tro (en, zh, vi) thi "can_hoi": true: dieu phoi dung lai hoi nguoi dung truoc khi dich.
--lid: chay them FireRedLID (scripts/nhan_dang_lid.py, tien trinh rieng, truoc khi nap Whisper de khong giu hai mo
hinh trong RAM) tren cac khuc co tieng noi; ket qua ghi o "ngon_ngu"."lid". FireRedLID chon ngon ngu khac Whisper,
hoac khong co khuc nao do tin >= 0,8, thi "can_hoi": true. Bo qua khi da chi dinh --ngon-ngu.

Co tung doan (chi la goi y de nguoi nghe lai, khong tu sua):
  nghi-bia     no_speech_prob > 0,6, compression_ratio > 2,4 (lap chu) hoac trung cau ket quen thuoc
               ("thanks for watching", "subscribe"...): Whisper hay bia nhung cau nay o doan khong co loi
  tin-thap     avg_logprob < -0,7
  ngan         doan duoi 0,5 giay
Nguong lay theo phep do 18/11/2026 tren 3 clip (references/che-do-dich.md), chua hieu chinh tren nhieu video.

Mo hinh: scripts/lay_whisper.py (small, medium) va scripts/lay_asr.py (large-v3) tai tu GitHub Release (du phong huggingface), kiem sha256.
Moc doan lay theo moc tu (word_timestamps) cua tu dau va tu cuoi, cong 0,4 giay: moc doan goc cua Whisper
co the trum ca khoang nhac sau cau.
Tieng doc bang ffmpeg ra mang so 16 kHz roi dua vao faster-whisper (tranh loi PyAV khi dua duong dan file).
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 16000
DEM = 0.4      # giay giu phu de sau tu cuoi
HO_TRO = ["en", "zh", "vi"]
CAU_BIA = ["thanks for watching", "thank you for watching", "subscribe", "like and subscribe",
           "see you next time", "please subscribe", "字幕", "請不吝點贊", "订阅", "感谢观看", "谢谢观看",
           "hẹn gặp lại", "đăng ký kênh"]
SCRIPTS = Path(__file__).resolve().parent


def doc_tieng(video: Path) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def thu_muc_mo_hinh(ban: str) -> str:
    lay = "lay_asr.py" if ban == "large-v3" else "lay_whisper.py"
    r = subprocess.run([sys.executable, str(SCRIPTS / lay), ban], capture_output=True, text=True)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        sys.exit(r.returncode)
    return r.stdout.strip().splitlines()[-1]


def tieng_noi(audio):
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    ts = get_speech_timestamps(audio, VadOptions(min_silence_duration_ms=500))
    return [(t["start"] / SR, t["end"] / SR) for t in ts]


def giao(a, b, c, d):
    return max(0.0, min(b, d) - max(a, c))


def nhan_dang(model, audio, noi):
    dur = len(audio) / SR
    khuc, tong = [], {}
    for i in range(0, max(1, int(np.ceil(dur / 30)))):
        a, b = i * 30.0, min(dur, i * 30.0 + 30)
        co_loi = sum(giao(a, b, s, e) for s, e in noi)
        if co_loi < 3.0:
            khuc.append({"tu": a, "den": round(b, 2), "loi_giay": round(co_loi, 1), "bo_qua": True})
            continue
        lang, p, allp = model.detect_language(audio[int(a * SR):int(b * SR)])
        top = sorted(allp, key=lambda x: -x[1])[:3]
        khuc.append({"tu": a, "den": round(b, 2), "loi_giay": round(co_loi, 1),
                     "top": [[k, round(v, 3)] for k, v in top]})
        for k, v in allp:
            tong[k] = tong.get(k, 0.0) + v
    dung = [k for k in khuc if not k.get("bo_qua")]
    if not dung:
        return {"chon": None, "chac_chan": False, "can_hoi": True, "ly_do": "khong co khuc nao du 3 giay tieng noi",
                "khuc": khuc}
    xep = sorted(((k, v / len(dung)) for k, v in tong.items()), key=lambda x: -x[1])
    (l1, p1), (l2, p2) = xep[0], xep[1]
    dong_y = all(k["top"][0][0] == l1 for k in dung)
    ly_do = []
    if not dong_y:
        ly_do.append("cac khuc khong cung ngon ngu")
    if p1 < 0.8:
        ly_do.append(f"xac suat trung binh {p1:.2f} < 0,8")
    if p1 - p2 < 0.3:
        ly_do.append(f"sat ngon ngu thu hai ({l2} {p2:.2f})")
    chac = not ly_do
    if l1 not in HO_TRO:
        ly_do.append(f"{l1} ngoai danh sach ho tro {HO_TRO}")
    return {"chon": l1, "xac_suat": round(p1, 3), "thu_hai": [l2, round(p2, 3)], "chac_chan": chac,
            "can_hoi": bool(ly_do), "ly_do": "; ".join(ly_do), "khuc": khuc}


def chay_lid(video: Path, out: Path, noi, luong: int) -> dict:
    """Chay nhan_dang_lid.py o tien trinh rieng; tra ve ket qua JSON."""
    vao, ra = out / "lid-khuc-noi.json", out / "lid.json"
    vao.write_text(json.dumps([[round(s, 2), round(e, 2)] for s, e in noi]), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "nhan_dang_lid.py"), str(video), "--doan", str(vao),
                        "--ra", str(ra), "--luong", str(luong)], capture_output=True, text=True)
    sys.stderr.write(r.stderr)
    vao.unlink(missing_ok=True)
    if r.returncode != 0:
        sys.exit(r.returncode)
    return json.loads(ra.read_text(encoding="utf-8"))


def doi_chieu_lid(nn: dict, lid: dict):
    """Ghi ket qua FireRedLID vao nn; khac Whisper hoac khong co khuc tin cay thi can_hoi."""
    nn["lid"] = {k: lid[k] for k in ("chon", "ty_le", "giay_tin_cay", "giay_tieng_noi", "tong")}
    ly_do = []
    if lid["chon"] is None:
        ly_do.append("FireRedLID khong co khuc nao do tin >= 0,8")
    elif lid["chon"] != nn["chon"]:
        ly_do.append(f"FireRedLID chon {lid['chon']} ({lid['giay_tin_cay']} giay tin cay), Whisper chon {nn['chon']}")
    if ly_do:
        nn["chac_chan"] = False
        nn["can_hoi"] = True
        nn["ly_do"] = "; ".join([x for x in [nn.get("ly_do")] if x] + ly_do)


def co_doan(s):
    co = []
    t = s.text.strip().lower()
    if s.no_speech_prob > 0.6 or s.compression_ratio > 2.4 or any(c in t for c in CAU_BIA):
        co.append("nghi-bia")
    if s.avg_logprob < -0.7:
        co.append("tin-thap")
    if s.end - s.start < 0.5:
        co.append("ngan")
    return co


def khoang_trong(doan, dur, nguong=2.0):
    out, t = [], 0.0
    for d in doan:
        if d["start"] - t >= nguong:
            out.append([round(t, 2), round(d["start"], 2)])
        t = max(t, d["end"])
    if dur - t >= nguong:
        out.append([round(t, 2), round(dur, 2)])
    return out


def ghi_md(path: Path, kq):
    nn = kq["ngon_ngu"]
    lines = [f"# Bản chép lời gốc: {kq['video']}", "",
             f"- Mô hình: Whisper {kq['ban']}, VAD {'bật' if kq['vad'] else 'tắt'}; thời lượng {kq['thoi_luong']} giây.",
             f"- Ngôn ngữ: **{nn.get('chon')}**" + (f" ({nn['xac_suat']})" if nn.get("xac_suat") is not None else "")
             + (" (người dùng chọn)" if nn.get("nguoi_chon") else "")
             + ("" if not nn.get("can_hoi") else f". **CẦN HỎI**: {nn.get('ly_do')}"), ""]
    if nn.get("lid"):
        lines += [f"- FireRedLID: {nn['lid']['chon']} ({nn['lid']['giay_tin_cay']}/{nn['lid']['giay_tieng_noi']} giây "
                  f"tin cậy; {', '.join(f'{k} {v}' for k, v in nn['lid']['tong'].items()) or 'không có'}).", ""]
    if nn.get("canh_bao"):
        lines += [f"- **CẢNH BÁO**: {nn['canh_bao']}", ""]
    lines += ["| Mã | Giây | Lời gốc | Cờ |", "|---|---|---|---|"]
    for d in kq["doan"]:
        lines.append(f"| {d['id']} | {d['start']:.1f}-{d['end']:.1f} | {d['goc'].replace('|', '/')} | {', '.join(d['co'])} |")
    if kq["khoang_trong"]:
        lines += ["", "Khoảng không có lời (nghe lại xem có lời bị bỏ sót không): "
                  + ", ".join(f"{a:.1f}-{b:.1f}" for a, b in kq["khoang_trong"])]
    lines += ["", "Cờ: `nghi-bia` có thể là câu Whisper tự thêm; `tin-thap` nghe chưa chắc; `ngan` đoạn rất ngắn.",
              "Người dùng sửa lời gốc sai, gán người nói nếu có nhiều người, rồi mới dịch."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("project")
    ap.add_argument("--ban", choices=["small", "medium", "large-v3"], default="medium")
    ap.add_argument("--ngon-ngu", default="auto", help="auto hoac ma ngon ngu Whisper (en, zh, vi...)")
    ap.add_argument("--khong-vad", action="store_true")
    ap.add_argument("--luong", type=int, default=os.cpu_count() or 2, help="so luong CPU")
    ap.add_argument("--lid", action="store_true", help="doi chieu ngon ngu voi FireRedLID (setup.sh --lid)")
    a = ap.parse_args()

    video, proj = Path(a.video), Path(a.project)
    out = proj / "dich"
    out.mkdir(parents=True, exist_ok=True)
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("[LOI] Chua cai faster-whisper. Chay: bash SKILL/scripts/setup.sh --dich")

    audio = doc_tieng(video)
    dur = len(audio) / SR
    if dur < 1:
        sys.exit("[LOI] Video khong co tieng hoac qua ngan")
    noi = tieng_noi(audio)
    print(f"Tieng noi theo VAD: {sum(e - s for s, e in noi):.1f}/{dur:.1f} giay", file=sys.stderr)
    lid = chay_lid(video, out, noi, a.luong) if a.lid and a.ngon_ngu == "auto" else None
    model = WhisperModel(thu_muc_mo_hinh(a.ban), device="cpu", compute_type="int8", cpu_threads=a.luong)

    if a.ngon_ngu == "auto":
        nn = nhan_dang(model, audio, noi)
        if lid is not None:
            doi_chieu_lid(nn, lid)
    else:
        nn = {"chon": a.ngon_ngu, "nguoi_chon": True, "chac_chan": True, "can_hoi": False, "ly_do": ""}
        if a.ngon_ngu not in HO_TRO:
            nn["canh_bao"] = f"{a.ngon_ngu} ngoai danh sach da thu {HO_TRO}: ban chep co the kem tin cay"
    lang = nn["chon"]
    if lang is None:
        doan = []
    else:
        segs, _ = model.transcribe(audio, language=lang, beam_size=5, vad_filter=not a.khong_vad,
                                   word_timestamps=True)
        doan = []
        for s in segs:
            text = s.text.strip()
            if not text:
                continue
            # Moc doan cua Whisper co the keo dai qua khoang nhac (vd 4,6 den 40,2 giay cho mot cau 2 giay):
            # lay theo tu dau va tu cuoi, cong DEM giay de chu khong tat ngay khi het tieng
            t0, t1 = s.start, s.end
            if s.words:
                t0, t1 = s.words[0].start, min(s.end, s.words[-1].end + DEM)
            doan.append({"id": f"d{len(doan) + 1:03d}", "start": round(t0, 2), "end": round(t1, 2),
                         "goc": text, "avg_logprob": round(s.avg_logprob, 3), "no_speech": round(s.no_speech_prob, 3),
                         "co": co_doan(s)})
    kq = {"phien_ban": 1, "video": video.name, "ban": a.ban, "vad": not a.khong_vad, "thoi_luong": round(dur, 2),
          "ngon_ngu": nn, "doan": doan, "khoang_trong": khoang_trong(doan, dur)}
    (out / "chep-goc.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ghi_md(out / "chep-goc.md", kq)
    n_co = sum(1 for d in doan if d["co"])
    print(f"[OK] {out / 'chep-goc.json'}: ngon ngu {lang}, {len(doan)} doan, {n_co} doan co co, "
          f"{len(kq['khoang_trong'])} khoang khong loi")
    if nn.get("canh_bao"):
        print(f"[CANH BAO] {nn['canh_bao']}")
    if nn.get("can_hoi"):
        print(f"[CAN HOI] Ngon ngu chua chac chan: {nn['ly_do']}. Hoi nguoi dung, roi chay lai voi --ngon-ngu.")


if __name__ == "__main__":
    main()
