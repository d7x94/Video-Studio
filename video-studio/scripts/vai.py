#!/usr/bin/env python3
"""Thu vien ho so vai: vai da casting o video truoc, luu de video sau dung lai.

Ho so vai nam o SKILL/vai/<ma-vai>.json (xem SKILL/vai/README.md). Nhan vat (mat, dang, giong)
la dien vien co dinh trong dan; ho so vai ghi ai dong, ten goi, chuc vu, tuoi, cac bo do (skin)
vai duoc mac va cac cu chi hay dung.

Dung:
  python3 vai.py danh-sach [--kieu line-art|chibi|3d]   # in bang ho so vai
  python3 vai.py kiem [FILE ...]                          # kiem ho so vai (mac dinh: ca thu vien)
  python3 vai.py kiem-casting PROJECT/casting.json        # kiem casting.json, in khung hien khi doi skin theo canh
  python3 vai.py xuat PROJECT/casting.json THU_MUC --video SLUG [--ngay YYYY-MM-DD]
                                                          # ghi ho so vai (moi hoac cap nhat) tu casting da chot

Dan nhan vat, skin, cu chi doc tu assets/lineart/lineart.js va assets/chibi/chibi.js bang node,
nen luon khop ban build. Thoat ma 1 neu co loi.
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
LIB = SKILL / "vai"
KIEU = ("line-art", "chibi", "3d")
GOC = "goc"  # skin dac biet: bo do khoa trong roster cua nhan vat
TUOI = {"child": (3, 15), "adult": (18, 59), "elder": (60, 100)}
MA = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CANH = re.compile(r"^s(\d+)$")


def load_cast():
    """Doc roster, skin, cu chi tu ban build (khong doc nguon TS de chay duoc trong skill da cai)."""
    js = (
        "const L = await import(process.argv[1]); const C = await import(process.argv[2]);"
        "console.log(JSON.stringify({"
        "roster: L.ROSTER.map(r => ({id: r.id, name: r.name, role: r.role, build: r.build, sex: r.sex})),"
        "skins: Object.values(L.SKINS).map(s => ({id: s.id, label: s.label, gestures: s.gestures || {}})),"
        "gestures: [...L.GESTURES], clips: Object.keys(C.MOCAP)}))"
    )
    out = subprocess.run(
        ["node", "--input-type=module", "-e", js,
         (SKILL / "assets/lineart/lineart.js").as_uri(), (SKILL / "assets/chibi/chibi.js").as_uri()],
        capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    d["roster"] = {r["id"]: r for r in d["roster"]}
    d["skins"] = {s["id"]: s for s in d["skins"]}
    actors = json.loads((SKILL / "assets/sim3d/cast.json").read_text(encoding="utf-8"))["actors"]
    d["actors"] = set(actors)
    d["voices"] = load_voices()
    return d


def load_voices():
    voices = set()
    for line in (SKILL / "references/giong-doc.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*(Nam|Nữ)\s*\|", line)
        if m:
            voices.add(m.group(1))
    return voices


def read_cards(paths=None):
    files = paths or sorted(p for p in LIB.glob("*.json") if not p.name.startswith("_"))
    cards = {}
    for p in files:
        p = Path(p)
        try:
            cards[p] = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            cards[p] = {"_loi": f"JSON sai: {e}"}
    return cards


def check_card(c, cast, name="?"):
    """Tra ve danh sach loi cua mot ho so vai."""
    err = []
    if "_loi" in c:
        return [c["_loi"]]
    for k in ("id", "ho_ten", "chuc_vu", "kieu_hinh", "trang_phuc"):
        if not c.get(k):
            err.append(f"thieu `{k}`")
    if c.get("id") and not MA.match(c["id"]):
        err.append(f"id `{c['id']}` chi dung chu thuong khong dau, so, gach noi")
    if c.get("id") and not name.startswith("_") and name not in ("?", f"{c['id']}.json"):
        err.append(f"ten file phai la {c['id']}.json")
    kieu = c.get("kieu_hinh") or []
    for k in kieu:
        if k not in KIEU:
            err.append(f"kieu_hinh `{k}` khong co (co: {', '.join(KIEU)})")
    hai_d = any(k in ("line-art", "chibi") for k in kieu)
    nv = c.get("nhan_vat")
    if hai_d:
        if nv not in cast["roster"]:
            err.append(f"nhan_vat `{nv}` khong co trong dan line-art/chibi")
        elif c.get("tuoi") is not None:
            lo, hi = TUOI[cast["roster"][nv]["build"]]
            if not (isinstance(c["tuoi"], int) and lo <= c["tuoi"] <= hi):
                err.append(f"tuoi {c['tuoi']} khong hop dang `{cast['roster'][nv]['build']}` cua {nv} ({lo}-{hi})")
    if "3d" in kieu and c.get("dien_vien_3d") not in cast["actors"]:
        err.append(f"dien_vien_3d `{c.get('dien_vien_3d')}` khong co trong assets/sim3d/cast.json")
    if c.get("giong") and c["giong"] not in cast["voices"]:
        err.append(f"giong `{c['giong']}` khong co trong references/giong-doc.md")
    tp = c.get("trang_phuc") or {}
    if hai_d and not isinstance(tp, dict):
        err.append("trang_phuc phai la bang ten-bo-do -> ma skin")
        tp = {}
    for ten, sk in tp.items():
        if not MA.match(ten):
            err.append(f"ten bo do `{ten}` chi dung chu thuong khong dau, gach noi")
        if sk != GOC and sk not in cast["skins"]:
            err.append(f"trang_phuc.{ten}: skin `{sk}` khong co (co: {GOC}, {', '.join(cast['skins'])})")
    if hai_d and "mac-dinh" not in tp:
        err.append("trang_phuc can bo `mac-dinh`")
    ok = set(cast["gestures"])
    for sk in tp.values():
        if sk in cast["skins"]:
            ok |= set(cast["skins"][sk]["gestures"])
    if "chibi" in kieu:
        ok |= {"sweep"} | set(cast["clips"])
    for g in c.get("cu_chi") or []:
        if g not in ok:
            err.append(f"cu_chi `{g}` khong co trong rig hay skin cua vai (dong tac moi phai lam vao rig truoc)")
    for v in c.get("da_dong") or []:
        if not isinstance(v, dict) or not v.get("video"):
            err.append("da_dong: moi muc can `video`")
    return err


def check_library(cards, cast):
    """Loi giua cac ho so: trung id; cung mot nhan vat thi cung mot giong."""
    err = []
    ids, giong = {}, {}
    for p, c in cards.items():
        if "_loi" in c:
            continue
        if c.get("id") in ids:
            err.append(f"{p.name}: trung id voi {ids[c['id']].name}")
        ids[c.get("id")] = p
        nv, g = c.get("nhan_vat"), c.get("giong")
        if nv and g:
            if nv in giong and giong[nv][0] != g:
                err.append(f"{p.name}: {nv} da dung giong `{giong[nv][0]}` o {giong[nv][1]}; mot nhan vat mot giong")
            giong.setdefault(nv, (g, p.name))
    return err


def cmd_danh_sach(a):
    cast = load_cast()
    cards = [c for c in read_cards().values() if "_loi" not in c]
    if a.kieu:
        cards = [c for c in cards if a.kieu in (c.get("kieu_hinh") or [])]
    if not cards:
        print("(thu vien ho so vai chua co vai nao" + (f" cho kieu {a.kieu}" if a.kieu else "") + ")")
        return 0
    print("| Ma vai | Ho ten | Chuc vu | Tuoi | Nhan vat | Giong | Bo do | Kieu hinh | So video |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in sorted(cards, key=lambda c: c["id"]):
        nv = c.get("nhan_vat") or c.get("dien_vien_3d") or ""
        if nv in cast["roster"]:
            nv = f"{nv} ({cast['roster'][nv]['name']})"
        tp = ", ".join(f"{k}={v}" for k, v in (c.get("trang_phuc") or {}).items())
        print(f"| {c['id']} | {c.get('ho_ten', '')} | {c.get('chuc_vu', '')} | {c.get('tuoi', '')} | {nv} | "
              f"{c.get('giong', '')} | {tp} | {', '.join(c.get('kieu_hinh', []))} | {len(c.get('da_dong') or [])} |")
    return 0


def cmd_kiem(a):
    cast = load_cast()
    cards = read_cards([Path(p) for p in a.files] if a.files else None)
    n = 0
    for p, c in cards.items():
        for e in check_card(c, cast, p.name):
            print(f"[LOI] {p.name}: {e}"); n += 1
    for e in check_library(read_cards() if a.files else cards, cast):
        print(f"[LOI] {e}"); n += 1
    print(f"{len(cards)} ho so, {n} loi" if n else f"[OK] {len(cards)} ho so vai hop le")
    return 1 if n else 0


def scene_key(s):
    m = CANH.match(s)
    return int(m.group(1)) if m else 10 ** 6


def cmd_kiem_casting(a):
    cast = load_cast()
    data = json.loads(Path(a.casting).read_text(encoding="utf-8"))
    roles = data if isinstance(data, list) else data.get("roles") or data.get("vai") or []
    cards = {c.get("id"): c for c in read_cards().values() if "_loi" not in c}
    err, warn, plan = [], [], []
    seen_char, seen_voice = {}, {}
    for r in roles:
        ten = r.get("role") or r.get("vai_id") or "?"
        char = r.get("character")
        is3d = "model" in r
        if char:
            if char not in cast["roster"]:
                err.append(f"{ten}: character `{char}` khong co trong dan")
            if char in seen_char:
                err.append(f"{ten}: {char} da dong vai `{seen_char[char]}`; mot nhan vat mot vai trong mot video")
            seen_char.setdefault(char, ten)
        v = r.get("voice")
        if v:
            if v not in cast["voices"]:
                err.append(f"{ten}: voice `{v}` khong co trong references/giong-doc.md")
            if v in seen_voice:
                err.append(f"{ten}: giong `{v}` trung vai `{seen_voice[v]}`")
            seen_voice.setdefault(v, ten)
        card = None
        if r.get("vai_id"):
            card = cards.get(r["vai_id"])
            if not card:
                err.append(f"{ten}: vai_id `{r['vai_id']}` khong co trong thu vien SKILL/vai/")
            else:
                if char and card.get("nhan_vat") != char:
                    err.append(f"{ten}: ho so vai ghi nhan_vat `{card.get('nhan_vat')}`, casting ghi `{char}`")
                if v and card.get("giong") and card["giong"] != v:
                    err.append(f"{ten}: ho so vai ghi giong `{card['giong']}`, casting ghi `{v}`")
        stc = r.get("skin_theo_canh")
        if not stc:
            if card and not is3d and r.get("skin") not in (None, GOC, *card.get("trang_phuc", {}).values()):
                err.append(f"{ten}: skin `{r.get('skin')}` khong nam trong trang_phuc cua ho so vai")
            continue
        if is3d:
            err.append(f"{ten}: nhan vat 3D chua ho tro skin_theo_canh (skin o 3D la mau da)")
            continue
        scenes = sorted(r.get("scenes") or [], key=scene_key)
        if not scenes:
            err.append(f"{ten}: skin_theo_canh can danh sach `scenes`")
            continue
        for s in stc:
            if s not in scenes:
                err.append(f"{ten}: skin_theo_canh co canh `{s}` khong nam trong scenes cua vai")
        allowed = set(card.get("trang_phuc", {}).values()) if card else None
        runs, cur = [], None
        for s in scenes:
            sk = stc.get(s)
            if sk is None:
                err.append(f"{ten}: canh {s} chua chot skin (skin_theo_canh phai ghi du moi canh cua vai)")
                continue
            if sk != GOC and sk not in cast["skins"]:
                err.append(f"{ten}: canh {s} skin `{sk}` khong co")
            if allowed is not None and sk not in allowed:
                err.append(f"{ten}: canh {s} skin `{sk}` khong nam trong trang_phuc cua ho so vai")
            if cur and cur[0] == sk:
                cur[1].append(s)
            else:
                cur = [sk, [s]]; runs.append(cur)
        if len({sk for sk, _ in runs}) > 3:
            warn.append(f"{ten}: hon 3 bo do trong mot video, nguoi xem de nham nguoi")
        if len(runs) > 1:
            for i, (sk, ss) in enumerate(runs):
                frm = "" if i == 0 else f"from: T.{ss[0]}"
                unt = "" if i == len(runs) - 1 else f"until: T.{runs[i + 1][1][0]}"
                opt = ", ".join(x for x in (f'skin: "{sk}"' if sk != GOC else "", frm, unt) if x)
                plan.append(f'{char} [{ss[0]}..{ss[-1]}]: add("{char}", {{ x, y, scale, {opt} }})')
    for w in warn:
        print(f"[CANH BAO] {w}")
    for e in err:
        print(f"[LOI] {e}")
    if plan and not err:
        print("Khung hien (doi skin theo canh; moi dong la mot ban cua nhan vat, them bang C.add hoac L.add):")
        for p in plan:
            print("  " + p)
    print(f"{len(roles)} vai, {len(err)} loi" if err else f"[OK] casting hop le ({len(roles)} vai)")
    return 1 if err else 0


def slug(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def cmd_xuat(a):
    cast = load_cast()
    data = json.loads(Path(a.casting).read_text(encoding="utf-8"))
    roles = data if isinstance(data, list) else data.get("roles") or data.get("vai") or []
    out = Path(a.thu_muc); out.mkdir(parents=True, exist_ok=True)
    lib = {c.get("id"): c for c in read_cards().values() if "_loi" not in c}
    ngay = a.ngay or dt.date.today().isoformat()
    n, bad = 0, 0
    for r in roles:
        if not (r.get("character") or r.get("model")):
            continue  # nguoi dan chuyen: chi co giong, khong luu ho so vai
        hs = r.get("ho_so") or {}
        vid = r.get("vai_id") or hs.get("id") or slug(hs.get("ho_ten") or r.get("role") or "")
        card = json.loads(json.dumps(lib.get(vid) or {}))
        moi = not card
        if moi:
            card = {"id": vid}
            for k in ("ho_ten", "cach_goi", "chuc_vu", "noi_lam", "tuoi", "tinh_cach", "xung_ho", "ghi_chu"):
                if k in hs:
                    card[k] = hs[k]
            card.setdefault("ho_ten", r.get("role", vid))
            card.setdefault("chuc_vu", r.get("role", ""))
            if r.get("character"):
                card["nhan_vat"] = r["character"]
            if r.get("model"):
                card["dien_vien_3d"] = hs.get("dien_vien_3d") or r.get("actor")
            if r.get("voice"):
                card["giong"] = r["voice"]
            card["kieu_hinh"] = [a.kieu] if a.kieu else hs.get("kieu_hinh", [])
            tp = dict(hs.get("trang_phuc") or {})
            if not tp and r.get("character"):
                skins = [r.get("skin") or GOC] + list((r.get("skin_theo_canh") or {}).values())
                for sk in dict.fromkeys(skins):
                    tp["mac-dinh" if not tp else sk] = sk
            card["trang_phuc"] = tp
            if hs.get("cu_chi"):
                card["cu_chi"] = hs["cu_chi"]
        else:
            if a.kieu and a.kieu not in card.get("kieu_hinh", []):
                card.setdefault("kieu_hinh", []).append(a.kieu)
            for sk in [r.get("skin")] + list((r.get("skin_theo_canh") or {}).values()):
                if sk and sk not in card.get("trang_phuc", {}).values():
                    card.setdefault("trang_phuc", {})[sk] = sk
        dd = card.setdefault("da_dong", [])
        if not any(x.get("video") == a.video for x in dd):
            dd.append({"video": a.video, "ngay": ngay})
        p = out / f"{vid}.json"
        p.write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        errs = check_card(card, cast, p.name)
        print(f"{'[MOI]' if moi else '[CAP NHAT]'} {p}" + ("" if not errs else "  LOI: " + "; ".join(errs)))
        n += 1; bad += bool(errs)
    print(f"Da ghi {n} ho so vai vao {out}" + (f", {bad} ho so con loi: sua truoc khi them vao repo" if bad else ""))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("danh-sach"); s.add_argument("--kieu", choices=KIEU); s.set_defaults(fn=cmd_danh_sach)
    s = sub.add_parser("kiem"); s.add_argument("files", nargs="*"); s.set_defaults(fn=cmd_kiem)
    s = sub.add_parser("kiem-casting"); s.add_argument("casting"); s.set_defaults(fn=cmd_kiem_casting)
    s = sub.add_parser("xuat"); s.add_argument("casting"); s.add_argument("thu_muc")
    s.add_argument("--video", required=True); s.add_argument("--ngay"); s.add_argument("--kieu", choices=KIEU)
    s.set_defaults(fn=cmd_xuat)
    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
