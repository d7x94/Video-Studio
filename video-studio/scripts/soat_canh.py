#!/usr/bin/env python3
"""Soat kich ban truoc khi dung hinh: bao nhung dau hieu video se thanh "trinh chieu" (cac canh na na nhau).

Dung:  python3 soat_canh.py PROJECT/scenes.json [--kieu 2d|line-art|chibi|ve-tay|ve-net|3d]

Chi dua tren chu trong scenes.json (truong visual, on_screen), nen chi la canh bao de bien kich xem lai,
khong thay duoc mat nguoi. Bao:
  - visual trong hoac qua ngan (duoi 8 tu): agent dung canh se phai tu doan
  - visual dung tu chung chung ("hinh minh hoa", "sinh dong", "hien dai"...): khong noi hinh gi
  - hai canh lien nhau mo ta hinh gan giong nhau (trung tu tren 60 phan tram)
  - ba canh lien nhau cung mot khuon hinh (cung tu khoa bo cuc nhu "danh sach", "bieu tuong", "so sanh")
  - qua nua so canh chi co chu (visual chi noi ve chu, tieu de)
  - ve-net: visual khong ghi thu tu but ve
Ma thoat 1 khi co muc "Nen sua"; muc "Goi y" khong lam that bai.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

GENERIC = ["hình minh họa", "hình ảnh minh họa", "sinh động", "hiện đại", "ấn tượng", "đẹp mắt", "bắt mắt",
           "chuyên nghiệp", "phù hợp", "hấp dẫn", "nổi bật", "đơn giản và rõ ràng", "phong cách tối giản"]
LAYOUT = {
    "danh sách": ["danh sách", "gạch đầu dòng", "liệt kê"],
    "biểu tượng": ["biểu tượng", "icon"],
    "so sánh": ["so sánh", "hai cột", "đối lập"],
    "số liệu": ["con số", "biểu đồ", "số liệu", "đồng hồ đếm"],
    "chữ lớn": ["chữ lớn", "tiêu đề lớn", "dòng chữ"],
    "nhân vật nói": ["nói", "giới thiệu", "giải thích"],
}
TEXT_ONLY = ["chữ", "tiêu đề", "dòng chữ", "câu"]
PICTURE_HINT = ["biểu tượng", "icon", "người", "nhân vật", "bàn tay", "tay", "nhà", "cây", "xe", "máy bay", "tàu", "muỗi", "nước", "bản đồ",
                "mũi tên", "vòng tròn", "hình", "khung", "điện thoại", "cốc", "thuốc", "bác sĩ", "trẻ", "phòng",
                "cửa", "đường", "biểu đồ", "đồng hồ", "giấy", "tranh", "cảnh", "bối cảnh"]


def norm(s):
    return unicodedata.normalize("NFC", (s or "").lower())


def words(s):
    return [w for w in re.findall(r"\w+", norm(s)) if len(w) > 1]


def has_any(text, keys):
    return any(re.search(rf"(?<!\w){re.escape(k)}(?!\w)", text) for k in keys)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenes")
    ap.add_argument("--kieu", default="2d")
    a = ap.parse_args()
    scenes = json.loads(Path(a.scenes).read_text(encoding="utf-8"))["scenes"]
    fix, hint = [], []

    layouts = []
    text_only = 0
    for sc in scenes:
        sid, vis = sc["id"], norm(sc.get("visual", ""))
        n = len(words(vis))
        if n == 0:
            fix.append(f"{sid}: visual trong")
        elif n < 8:
            fix.append(f"{sid}: visual qua ngan ({n} tu), ghi ro hinh gi, o dau, chuyen dong ra sao")
        bad = [g for g in GENERIC if g in vis]
        if bad:
            hint.append(f"{sid}: tu chung chung ({', '.join(bad)}): thay bang vat, nguoi, hanh dong cu the")
        layouts.append({k for k, keys in LAYOUT.items() if has_any(vis, keys)})
        if vis and has_any(vis, TEXT_ONLY) and not has_any(vis, PICTURE_HINT):
            text_only += 1
        if a.kieu == "ve-net":
            if n and not re.search(r"(trước|rồi|sau đó|tiếp theo|cuối cùng|đầu tiên|\d\))", vis):
                hint.append(f"{sid}: ve-net nen ghi thu tu but ve (dau tien, roi, cuoi cung) trung thu tu loi doc")

    for i in range(1, len(scenes)):
        A, B = set(words(scenes[i - 1].get("visual"))), set(words(scenes[i].get("visual")))
        if len(A) >= 5 and len(B) >= 5:
            j = len(A & B) / len(A | B)
            if j > 0.6:
                fix.append(f"{scenes[i - 1]['id']} va {scenes[i]['id']}: mo ta hinh gan giong nhau ({j:.0%} tu trung)")
    for i in range(2, len(scenes)):
        same = layouts[i - 2] & layouts[i - 1] & layouts[i]
        if same:
            hint.append(f"{scenes[i - 2]['id']} den {scenes[i]['id']}: ba canh lien cung khuon '{', '.join(sorted(same))}'")
    if scenes and text_only > len(scenes) / 2:
        fix.append(f"{text_only}/{len(scenes)} canh chi co chu: nguoi xem tat tieng can hinh de hieu, khong chi doc chu")

    print(f"Soat {len(scenes)} canh ({a.kieu})")
    for m in fix:
        print(f"[NEN SUA] {m}")
    for m in hint:
        print(f"[GOI Y] {m}")
    if not fix and not hint:
        print("Khong thay dau hieu lap canh.")
    sys.exit(1 if fix else 0)


if __name__ == "__main__":
    main()
