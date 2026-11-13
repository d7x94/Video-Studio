#!/usr/bin/env python3
"""Dong goi thanh pham vao PROJECT/output/.

Dung:  python3 package.py PROJECT --thumb-at 2.5

Lay tu PROJECT:
  renders/final_landscape.mp4  -> <slug>_youtube_16x9.mp4
  renders/final_portrait.mp4   -> <slug>_tiktok_9x16.mp4
  phu-de.srt, metadata.md, kich-ban.md, kiem-chung.md, credits.md (file nao co thi chep)
Tao thumbnail:
  thumbnail_16x9.png (1280x720) tu ban ngang, hoac thumbnail_9x16.png tu ban doc neu chi co ban doc
In danh sach file de goi SendUserFile tung file.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--thumb-at", type=float, default=1.5, help="Giay lay khung hinh lam thumbnail")
    a = ap.parse_args()

    p = Path(a.project)
    slug = p.resolve().name   # goi voi "." thi p.name rong
    out = p / "output"
    out.mkdir(exist_ok=True)
    made = []

    videos = {"landscape": (p / "renders/final_landscape.mp4", f"{slug}_youtube_16x9.mp4"),
              "portrait": (p / "renders/final_portrait.mp4", f"{slug}_tiktok_9x16.mp4")}
    for src, name in videos.values():
        if src.exists():
            shutil.copy2(src, out / name)
            made.append(out / name)
    if not made:
        sys.exit("Chua co renders/final_*.mp4")

    for name in ["phu-de.srt", "metadata.md", "kich-ban.md", "kiem-chung.md", "credits.md"]:
        if (p / name).exists():
            shutil.copy2(p / name, out / name)
            made.append(out / name)

    land = videos["landscape"][0]
    if land.exists():
        thumb, vf, src = out / "thumbnail_16x9.png", "scale=1280:720", land
    else:
        thumb, vf, src = out / "thumbnail_9x16.png", "scale=1080:1920", videos["portrait"][0]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.thumb_at), "-i", str(src), "-frames:v", "1",
                    "-vf", vf, str(thumb)], check=True)
    made.append(thumb)

    for f in made:
        print(f)


if __name__ == "__main__":
    main()
