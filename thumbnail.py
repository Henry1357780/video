"""Обложка YouTube из кадра сцены: название крупно золотом, подзаголовок курсивом.

    python thumbnail.py maharloka 4.13 "MAHARLOKA" "The World of the Sages · The Seven Worlds IV"
"""
import subprocess
import sys

import generate as g


def main():
    name, sid, title, sub = sys.argv[1:5]
    g.set_episode(name)
    src = g.FRAMES / f"scene_{sid}.png"
    out = g.FRAMES.parent / f"thumbnail_{name}.jpg"
    bold, ital = "C\\:/Windows/Fonts/palab.ttf", "C\\:/Windows/Fonts/palabi.ttf"
    vf = (
        "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
        "drawbox=x=0:y=500:w=1280:h=220:color=black@0.45:t=fill,"
        f"drawtext=fontfile='{bold}':text='{title}':fontsize=118:fontcolor=0xFFD877:"
        "borderw=4:bordercolor=0x3a2200:shadowx=4:shadowy=4:shadowcolor=black@0.7:"
        "x=(w-text_w)/2:y=505,"
        f"drawtext=fontfile='{ital}':text='{sub}':fontsize=38:fontcolor=white:"
        "borderw=2:bordercolor=black:x=(w-text_w)/2:y=645"
    )
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf, "-q:v", "2", str(out)],
                   check=True)
    print(f"готово: {out}")


if __name__ == "__main__":
    main()
