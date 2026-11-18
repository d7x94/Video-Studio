#!/usr/bin/env python3
"""Khoa kich ban sau cong duyet 1: ghi sha256 phan noi dung tung canh, doi la bao.

Dung:
  python3 khoa_kich_ban.py khoa PROJECT                 # ghi PROJECT/khoa-kich-ban.json (sau khi nguoi dung duyet
                                                        # va kiem chung xong, truoc khi long tieng)
  python3 khoa_kich_ban.py kiem PROJECT                 # so voi ban da khoa; thoat 1 neu co canh doi, them, bot
  python3 khoa_kich_ban.py cap-nhat PROJECT s03 s05 --ly-do "..." [--da-kiem-chung]
                                                        # nhan cac canh da doi vao ban khoa, ghi lich su
  python3 khoa_kich_ban.py xem PROJECT                  # in bang canh, ban khoa, lich su

Phan duoc khoa (moi canh): narration, subtitle, on_screen (ca dong nguon), claims.
Khong khoa: visual, pause_before, speed, voice, sfx (doi khong lam sai noi dung da kiem chung;
giong va toc do do tts.py van tay lo).

Vi sao: sau cong 1, loi doc, chu tren hinh, nguon va so lieu da duyet va da doi chieu nguon. Moi lan sua
sau do (vi nguoi dung phan hoi o cong 2, vi QA, vi doi giong doc "cho de doc") co the lam thong tin sai
ma khong ai doi chieu lai. Script nay chi bao "canh nay khac ban da duyet"; quyet dinh co dung lai khong
van la cua dieu phoi vien va nguoi dung. Canh co claims hoac co chu so ma doi thi cap-nhat doi co
--da-kiem-chung (dieu phoi cam ket da chay lai kiem chung cho canh do va ghi vao kiem-chung.md).
"""
import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

FILE = "khoa-kich-ban.json"
VER = 1


def tach(sc: dict) -> dict:
    """Phan noi dung cua canh duoc khoa."""
    return {
        "narration": (sc.get("narration") or "").strip(),
        "subtitle": (sc.get("subtitle") or "").strip(),
        "on_screen": sc.get("on_screen") or {},
        "claims": sc.get("claims") or [],
    }


def bam(sc: dict) -> str:
    raw = json.dumps(tach(sc), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def doc_scenes(project: Path) -> list:
    p = project / "scenes.json"
    if not p.exists():
        sys.exit(f"[LOI] Khong thay {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        scenes = data["scenes"]
    except (ValueError, KeyError) as e:
        sys.exit(f"[LOI] scenes.json hong: {e}")
    ids = [s.get("id") for s in scenes]
    if len(set(ids)) != len(ids) or not all(ids):
        sys.exit("[LOI] scenes.json: ma canh thieu hoac trung")
    return scenes


def doc_khoa(project: Path) -> dict:
    p = project / FILE
    if not p.exists():
        sys.exit(f"[LOI] Chua khoa kich ban ({FILE} chua co). Chay: khoa_kich_ban.py khoa {project}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        sys.exit(f"[LOI] {FILE} hong: {e}")


def ghi_khoa(project: Path, khoa: dict):
    (project / FILE).write_text(json.dumps(khoa, ensure_ascii=False, indent=1), encoding="utf-8")


def bay_gio() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def so_sanh(scenes: list, khoa: dict):
    """Tra ve (doi, them, bot) so voi ban khoa."""
    da = khoa.get("scenes", {})
    hien = {s["id"]: bam(s) for s in scenes}
    doi = [i for i in hien if i in da and da[i] != hien[i]]
    them = [i for i in hien if i not in da]
    bot = [i for i in da if i not in hien]
    return doi, them, bot


def can_kiem_chung(sc: dict) -> bool:
    """Canh co claims hoac co chu so trong loi doc, phu de, chu tren hinh."""
    if sc.get("claims"):
        return True
    chu = " ".join([sc.get("narration") or "", sc.get("subtitle") or "",
                    json.dumps(sc.get("on_screen") or {}, ensure_ascii=False)])
    return bool(re.search(r"\d", chu))


def cmd_khoa(project: Path, a):
    scenes = doc_scenes(project)
    p = project / FILE
    if p.exists() and not a.ghi_de:
        sys.exit(f"[LOI] {FILE} da co. Doi noi dung sau khi khoa thi dung cap-nhat; --ghi-de chi khi duyet lai ca kich ban.")
    khoa = {"ver": VER, "khoa_luc": bay_gio(),
            "scenes": {s["id"]: bam(s) for s in scenes}, "lich_su": []}
    if p.exists():
        cu = json.loads(p.read_text(encoding="utf-8"))
        khoa["lich_su"] = cu.get("lich_su", []) + [{"luc": bay_gio(), "viec": "khoa lai ca kich ban (--ghi-de)",
                                                    "ly_do": a.ly_do or ""}]
    ghi_khoa(project, khoa)
    print(f"Da khoa {len(scenes)} canh: {', '.join(s['id'] for s in scenes)}")


def cmd_kiem(project: Path, a):
    scenes = doc_scenes(project)
    khoa = doc_khoa(project)
    doi, them, bot = so_sanh(scenes, khoa)
    if not (doi or them or bot):
        print(f"Kich ban khop ban da khoa ({len(scenes)} canh).")
        return
    print("[CHAN] Kich ban khac ban da duyet va khoa:")
    by = {s["id"]: s for s in scenes}
    for i in doi:
        note = "can kiem chung lai" if can_kiem_chung(by[i]) else "khong co so hay khang dinh"
        print(f"  DOI   {i} ({note})")
    for i in them:
        print(f"  THEM  {i}")
    for i in bot:
        print(f"  BOT   {i}")
    print("Neu sua la co chu y: chay lai kiem chung cho canh do, roi "
          "khoa_kich_ban.py cap-nhat PROJECT <ma canh> --ly-do \"...\" [--da-kiem-chung].\n"
          "Neu khong chu y: khoi phuc scenes.json.")
    sys.exit(1)


def cmd_cap_nhat(project: Path, a):
    scenes = doc_scenes(project)
    khoa = doc_khoa(project)
    if not a.ly_do or len(a.ly_do.strip()) < 5:
        sys.exit("[LOI] Can --ly-do (it nhat vai chu): vi sao canh nay doi sau khi duyet")
    doi, them, bot = so_sanh(scenes, khoa)
    thay_doi = set(doi) | set(them) | set(bot)
    by = {s["id"]: s for s in scenes}
    ids = a.canh
    la = [i for i in ids if i not in thay_doi]
    if la:
        sys.exit(f"[LOI] Canh {', '.join(la)} khong khac ban khoa; khong co gi de cap nhat")
    thieu = [i for i in ids if i in by and can_kiem_chung(by[i]) and not a.da_kiem_chung]
    if thieu:
        sys.exit(f"[LOI] Canh {', '.join(thieu)} co claims hoac so lieu: chay lai kiem chung, ghi vao "
                 "kiem-chung.md roi them --da-kiem-chung")
    for i in ids:
        if i in by:
            khoa["scenes"][i] = bam(by[i])
        else:
            khoa["scenes"].pop(i, None)
    khoa.setdefault("lich_su", []).append({
        "luc": bay_gio(), "canh": ids, "ly_do": a.ly_do.strip(), "da_kiem_chung": bool(a.da_kiem_chung)})
    ghi_khoa(project, khoa)
    con = so_sanh(scenes, khoa)
    print(f"Da cap nhat {', '.join(ids)}." + (f" Con lech: {', '.join(sum(con, []))}" if any(con) else ""))


def cmd_xem(project: Path, a):
    khoa = doc_khoa(project)
    scenes = doc_scenes(project)
    doi, them, bot = so_sanh(scenes, khoa)
    print(f"Khoa luc {khoa.get('khoa_luc')}; {len(khoa.get('scenes', {}))} canh; "
          f"hien lech: doi {doi or '-'}, them {them or '-'}, bot {bot or '-'}")
    for h in khoa.get("lich_su", []):
        print(f"  {h.get('luc')}  {h.get('canh') or h.get('viec')}  [{h.get('ly_do', '')}]"
              + ("  da kiem chung" if h.get("da_kiem_chung") else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="lenh", required=True)
    k = sub.add_parser("khoa")
    k.add_argument("project")
    k.add_argument("--ghi-de", action="store_true", help="khoa lai tu dau (khi nguoi dung duyet lai ca kich ban)")
    k.add_argument("--ly-do", default="")
    kk = sub.add_parser("kiem")
    kk.add_argument("project")
    c = sub.add_parser("cap-nhat")
    c.add_argument("project")
    c.add_argument("canh", nargs="+", help="ma canh da doi, them hoac bi bo")
    c.add_argument("--ly-do", default="")
    c.add_argument("--da-kiem-chung", action="store_true")
    x = sub.add_parser("xem")
    x.add_argument("project")
    a = ap.parse_args()
    project = Path(a.project)
    {"khoa": cmd_khoa, "kiem": cmd_kiem, "cap-nhat": cmd_cap_nhat, "xem": cmd_xem}[a.lenh](project, a)


if __name__ == "__main__":
    main()
