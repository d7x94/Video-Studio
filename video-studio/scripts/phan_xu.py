#!/usr/bin/env python3
"""Che do dich: Qwen3-ASR-1.7B nghe lai cac cho Whisper, FireRed va chu tren hinh khong dong y, lam phieu thu ba.

Dung:
  python3 phan_xu.py VIDEO PROJECT              # doc PROJECT/dich/chep-goc.json, chep-firered.json, chu-tren-hinh.json
  python3 phan_xu.py VIDEO PROJECT --luong 2    # so luong CPU

Dau ra trong PROJECT/dich/:
  phan-xu.json   cac cua so da nghe, tung doan co cho can phan xu: loi Whisper, loi Qwen o cho do, Qwen theo ben nao
  phan-xu.md     bang de nguoi dung duyet

Chi nghe lai nhung doan co it nhat mot cho khac: dong KHAC cua FireRed (chep-firered.json, bo qua "chi tro tu")
hoac cho khac chu tren hinh (chu-tren-hinh.json). Khong chay Qwen tren ca video, khong nghe khoang trong (Qwen khong
co VAD va bia cau tren tieng go phim: do 2026-11-20 no chep "here's some ideas and more time" cho doan go phim ma
FireRed nghe dung la "asmr typing"), ep ngon ngu theo chep-goc.json (zh, en).
Cua so nghe: moi doan lay tu giay dau - 15 den giay cuoi + 15, cac cua so chong nhau thi gop (toi da 120 giay moi
cua so). Can ngu canh: do 2026-11-20 tren vlog tieng Anh, cua so 0,5 giay hai dau cho "bend" (sai), tu 3 giay tro len
cho "spend" (dung). "pork" (dung, phu de cung ghi vay) chi ra o 2 trong 10 cua so thu (ca clip 143 giay va [0, 95] giay,
cac cua so khong bat dau tu giay 0 deu ra "port"): ket qua cua Qwen o cho nay phu thuoc ranh gioi cua so, khong nen
tin no bat duoc loi ma Whisper va FireRed cung sai (cho do dung chu tren hinh).
Moi cho khac co toi da ba phuong an: loi Whisper, loi FireRed, chu tren hinh. Phuong an giong het nhau gop thanh mot
nhom. Qwen khong co moc thoi gian, nen vung loi Qwen cua doan duoc dinh vi bang cach tim doan co so tu trung nhieu
nhat voi loi Whisper cua doan (cua so len(w)+3 tu). Nhom phuong an nao nam tron, lien nhau trong vung do thi Qwen
theo nhom do. Dung mot nhom: "theo <ben>". Khong nhom nao ma mot ben la "(trong)" (ben kia khong co tu): theo ben
"(trong)". Khong khop gi, nhieu nhom cung nam trong, hoac khong dinh vi duoc vung: "chua ro".
Qwen la phieu thu ba, khong phai bo luat: no cung "sua ngu phap" nhu Whisper (decided thay vi decide, tasted thay vi
tastes), nhieu cho chi lap lai Whisper. Tren clip Trung 27,6 giay no theo FireRed o ca 4 cho phan xu duoc (头发,
跟人家, 给我吹头发); tren vlog Anh no theo FireRed o "spend" va theo Whisper o 5 cho con lai. Nguoi duyet van la nguoi
quyet; khong tu sua ban chep goc.
Mo hinh: scripts/lay_asr.py qwen3-asr-1.7b (GitHub Release, du phong HuggingFace, kiem sha256), khoang 4,7 GB.
Can: torch, qwen-asr, opencc (ban ghim trong setup.sh; bash setup.sh --phan-xu cai). Chay bfloat16 tren CPU,
RAM dinh khoang 5,9 GB (do 2026-11-20, 2 loi CPU), khoang 0,5 giay may cho 1 giay tieng trong cua so. Chay trong tien
trinh rieng, khong chung voi Whisper hay FireRed.
"""
import argparse
import json
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from chep_loi_firered import co_loi_that, doc_tieng, noi, tach  # noqa: E402  (cung cach tach tu voi kiem cheo FireRed)

SR = 16000
LE = 15.0                         # giay ngu canh them moi dau moi doan
TOI_DA = 120.0                    # giay toi da moi cua so nghe
DU = 3                            # so tu thua cua vung Qwen so voi loi Whisper cua doan
HO_TRO = {"zh": "Chinese", "en": "English"}
TEN_BEN = {"whisper": "Whisper", "firered": "FireRed", "chu": "chữ trên hình"}


def chua(q: list, tu: list) -> bool:
    """Day tu `tu` nam tron, lien nhau trong day `q`."""
    n = len(tu)
    return bool(tu) and any(q[i:i + n] == tu for i in range(len(q) - n + 1))


def vung(q: list, w: list):
    """Vung cua day tu Qwen `q` khop nhat voi loi Whisper `w` cua doan: cua so len(w)+DU tu co nhieu tu trung nhat.
    Tra ve (i, j, so_tu_trung)."""
    n = len(w) + DU
    best = (-1, 0, 0)
    for i in range(max(1, len(q) - n + 1)):
        seg = q[i:i + n]
        s = sum(b.size for b in SequenceMatcher(None, w, seg, autojunk=False).get_matching_blocks())
        if s > best[0]:
            best = (s, i, i + len(seg))
    return best[1], best[2], max(best[0], 0)


def chon_ben(q: list, pa: dict):
    """Qwen (day tu q, vung cua doan) theo nhom phuong an nao trong pa = {"whisper": [...], "firered": [...] hoac None,
    "chu": [...] hoac None}. Phuong an giong het nhau gop thanh nhom. Tra ve (cac ben, ghi chu); cac ben la tuple ten
    ben ("whisper", "firered", "chu"), rong khi chua ro."""
    pa = {k: v for k, v in pa.items() if v is not None}
    if not co_loi_that(q):
        return (), "Qwen không nghe được lời (trống hoặc lặp chữ), bỏ qua"
    nhom = {}
    for k, v in pa.items():
        nhom.setdefault(tuple(v), []).append(k)
    nam = [ks for v, ks in nhom.items() if v and chua(q, list(v))]
    if len(nam) == 1:
        return tuple(nam[0]), ""
    if len(nam) > 1:
        return (), "nhiều phương án cùng nằm trong lời Qwen"
    trong = [ks for v, ks in nhom.items() if not v]
    if len(trong) == 1:
        return tuple(trong[0]), "Qwen không nghe thấy từ nào ở chỗ này"
    return (), "Qwen nghe khác cả các bên"


def gom_cho(fr: list, ocr: list) -> list:
    """Gop cho khac cua mot doan tu FireRed ("w / f") va chu tren hinh (whisper, chu) theo tu Whisper.
    Tra ve danh sach {"whisper": str, "firered": str hoac None, "chu": str hoac None}."""
    cho = {}
    for s in fr:
        w, _, f = s.partition(" / ")
        w, f = ("" if w == "(trống)" else w), ("" if f == "(trống)" else f)
        cho.setdefault(tuple(tach(w)), {"whisper": w, "firered": None, "chu": None})["firered"] = f
    for w, c in ocr:
        cho.setdefault(tuple(tach(w)), {"whisper": w, "firered": None, "chu": None})["chu"] = c
    return list(cho.values())


def gom_cua_so(doan: list, dur: float) -> list:
    """Gop cac doan can phan xu thanh cua so nghe: moi doan them LE giay hai dau, cua so chong nhau thi gop,
    toi da TOI_DA giay. Tra ve [[t0, t1, [doan...]], ...]."""
    out = []
    for d in doan:
        t0, t1 = max(0.0, d["start"] - LE), min(dur, d["end"] + LE)
        if out and t0 <= out[-1][1] and t1 - out[-1][0] <= TOI_DA:
            out[-1][1] = max(out[-1][1], t1)
            out[-1][2].append(d)
        else:
            out.append([t0, t1, [d]])
    return out


def ten_ben(ben: list, ghi: str) -> str:
    kq = " + ".join(TEN_BEN[b] for b in ben) if ben else "chưa rõ"
    return kq + (f" ({ghi})" if ghi else "")


def ghi_md(path: Path, kq: dict):
    lines = [f"# Phân xử Qwen3-ASR: {kq['video']}", "",
             f"- Mô hình: {kq['mo_hinh']}. Chỉ nghe lại {len(kq['doan'])} đoạn có chỗ khác (KHÁC của FireRed hoặc khác chữ "
             f"trên hình) cùng {LE:.0f} giây ngữ cảnh hai đầu ({len(kq['cua_so'])} cửa sổ), không nghe khoảng trống.",
             "- Qwen là phiếu thứ ba: cũng hay \"sửa ngữ pháp\" như Whisper (decided thay vì decide) và bịa câu trên "
             "tiếng ồn không lời. Cột Qwen theo ghi nhóm phương án nằm nguyên trong lời Qwen ở chỗ đó; "
             "\"chưa rõ\" là không phân xử được.", "",
             "| Mã | Giây | Chỗ khác | Qwen nghe ở chỗ đó | Qwen theo |", "|---|---|---|---|---|"]
    for d in kq["doan"]:
        for c in d["cho"]:
            tb = "; ".join(f"{TEN_BEN[k]}: {c[k] or '(trống)'}" for k in ("whisper", "firered", "chu") if c[k] is not None)
            lines.append(f"| {d['id']} | {d['start']:.1f}-{d['end']:.1f} | {tb.replace('|', '/')} | "
                         f"{d['qwen'].replace('|', '/')} | {ten_ben(c['qwen_theo'], c['ghi_chu'])} |")
    lines += ["", "Chỗ nào Qwen theo một bên thì có thêm một phiếu cho bên đó, không phải kết luận. Người duyệt (hoặc người biết "
              "ngôn ngữ) nghe lại và quyết định; không tự sửa bản chép gốc theo Qwen."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def thu_muc_mo_hinh() -> Path:
    r = subprocess.run([sys.executable, str(SCRIPTS / "lay_asr.py"), "qwen3-asr-1.7b"], capture_output=True, text=True)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        sys.exit(r.returncode)
    return Path(r.stdout.strip().splitlines()[-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("project")
    ap.add_argument("--luong", type=int, default=2, help="so luong CPU (mac dinh 2)")
    a = ap.parse_args()

    video, proj = Path(a.video), Path(a.project)
    d0 = proj / "dich"
    if not (d0 / "chep-goc.json").exists():
        sys.exit(f"[LOI] Chua co {d0 / 'chep-goc.json'}: chay chep_loi_goc.py truoc.")
    goc = json.loads((d0 / "chep-goc.json").read_text(encoding="utf-8"))
    ngon_ngu = goc["ngon_ngu"].get("chon")
    if ngon_ngu not in HO_TRO:
        sys.exit(f"[LOI] Ngon ngu {ngon_ngu} ngoai danh sach da thu {list(HO_TRO)}.")
    fr, ocr = {}, {}
    if (d0 / "chep-firered.json").exists():
        for d in json.loads((d0 / "chep-firered.json").read_text(encoding="utf-8"))["doan"]:
            if d.get("khac"):
                fr[d["id"]] = d.get("cho_khac", [])
    if (d0 / "chu-tren-hinh.json").exists():
        for d in json.loads((d0 / "chu-tren-hinh.json").read_text(encoding="utf-8")).get("doan", []):
            if d.get("cho_khac"):
                ocr[d["id"]] = [tuple(x) for x in d["cho_khac"]]
    can = [d for d in goc["doan"] if d["id"] in fr or d["id"] in ocr]
    if not can:
        print("[OK] Khong co cho nao Whisper, FireRed va chu tren hinh khong dong y: khong can phan xu.")
        return
    try:
        import opencc  # noqa: F401  (dung trong chuan)
        import torch
        from qwen_asr import Qwen3ASRModel
    except ImportError as e:
        sys.exit(f"[LOI] Thieu {e.name}: chay bash setup.sh --phan-xu")

    md = thu_muc_mo_hinh()
    torch.set_num_threads(a.luong)
    model = Qwen3ASRModel.from_pretrained(str(md), dtype=torch.bfloat16, device_map="cpu",
                                          max_inference_batch_size=1, max_new_tokens=1024)
    x = doc_tieng(video)
    dur = len(x) / SR
    cua_so, ket = [], []
    for t0, t1, ds in gom_cua_so(can, dur):
        q = model.transcribe(audio=(x[int(t0 * SR):int(t1 * SR)], SR), language=HO_TRO[ngon_ngu])[0].text.strip()
        cua_so.append({"start": round(t0, 2), "end": round(t1, 2), "text": q})
        qt = tach(q)
        for d in ds:
            w = tach(d["goc"])
            i, j, diem = vung(qt, w)
            dinh_vi = diem >= max(1, len(w) // 2)
            cho = []
            for c in gom_cho(fr.get(d["id"], []), ocr.get(d["id"], [])):
                if dinh_vi:
                    ben, ghi = chon_ben(qt[i:j], {k: (tach(c[k]) if c[k] is not None else None) for k in ("whisper", "firered", "chu")})
                else:
                    ben, ghi = (), "không định vị được lời Qwen của đoạn này"
                cho.append({**c, "qwen_theo": list(ben), "ghi_chu": ghi})
            ket.append({"id": d["id"], "start": d["start"], "end": d["end"], "whisper": d["goc"],
                        "qwen": noi(qt[i:j]) if dinh_vi else "(không định vị được)", "cho": cho})
    kq = {"phien_ban": 2, "video": video.name, "mo_hinh": "Qwen3-ASR-1.7B (bfloat16, CPU)", "cua_so": cua_so, "doan": ket}
    d0.mkdir(parents=True, exist_ok=True)
    (d0 / "phan-xu.json").write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    ghi_md(d0 / "phan-xu.md", kq)
    dem = {}
    for d in ket:
        for c in d["cho"]:
            k = ten_ben(c["qwen_theo"], "")
            dem[k] = dem.get(k, 0) + 1
    tom = ", ".join(f"{k}: {v}" for k, v in sorted(dem.items()))
    print(f"[OK] dich/phan-xu.md: {len(ket)} doan, {len(cua_so)} cua so, {sum(len(d['cho']) for d in ket)} cho; Qwen theo {tom}")


if __name__ == "__main__":
    main()
