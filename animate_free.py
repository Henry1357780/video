"""Бесплатное оживление кадров (без Kling): движение камеры + золотые частицы.

Движение берётся из последней колонки сценария: free:zoom-in, free:zoom-out,
free:pan-right, free:pan-left, free:pan-down, free:pan-up, free:rotate.
Длительность — из колонки «Сек».

    python animate_free.py bhuloka           # все free-сцены, которых ещё нет в clips/
    python animate_free.py bhuloka 1.06      # одна сцена (перезаписать)
"""
import re
import subprocess
import sys

import generate as g

FPS = 24
W, H = 1920, 1080


def motion_filter(motion, sec):
    """Исходник сначала увеличиваем, чтобы медленное движение шло без дрожания."""
    n = sec * FPS
    return {
        "zoom-in": f"scale=3840:-2,zoompan=z='1+0.10*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
                   f":d={n}:s={W}x{H}:fps={FPS}",
        "zoom-out": f"scale=3840:-2,zoompan=z='1.10-0.10*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
                    f":d={n}:s={W}x{H}:fps={FPS}",
        # кадр шире экрана на 12%, камера едет слева направо / справа налево
        "pan-right": f"fps={FPS},scale=2150:-2,crop={W}:{H}:'(iw-{W})*t/{sec}':'(ih-{H})/2'",
        "pan-left": f"fps={FPS},scale=2150:-2,crop={W}:{H}:'(iw-{W})*(1-t/{sec})':'(ih-{H})/2'",
        # кадр выше экрана, камера опускается сверху вниз (с севера на юг)
        "pan-down": f"fps={FPS},scale=2300:-2,crop={W}:{H}:'(iw-{W})/2':'(ih-{H})*t/{sec}'",
        # камера поднимается снизу вверх (подъём души)
        "pan-up": f"fps={FPS},scale=2300:-2,crop={W}:{H}:'(iw-{W})/2':'(ih-{H})*(1-t/{sec})'",
        # медленный поворот (~0.7° в секунду) с запасом по краям
        "rotate": f"fps={FPS},scale=2700:-2,rotate=a='t*0.012':c=black,crop={W}:{H}",
        # отъезд камеры, кадр гаснет в глубокую синеву (наступает ночь)
        "night": f"scale=3840:-2,zoompan=z='1.10-0.10*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
                 f":d={n}:s={W}x{H}:fps={FPS},fade=t=out:st=1.5:d={sec - 2}:color=0x060a24",
    }[motion]


PARTICLES = (f"nullsrc=s={W}x1600:r={FPS},geq=lum='if(gt(random(1),0.9993),255,0)':cb=128:cr=128,"
             "gblur=sigma=1.6,lutyuv=y='min(val*6,255)',"
             f"crop={W}:{H}:0:'400-t*14',colorchannelmixer=rr=1:gg=0.85:bb=0.5")


def motions():
    """{сцена: (движение, секунды)} для всех free-сцен сценария."""
    text = g.SCENARIO.read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\d+\.\d+) \| (\d+) \|.*\| free:([\w-]+) \|\s*$", text, re.M)
    return {sid: (motion, int(sec)) for sid, sec, motion in rows}


def render(sid, motion, sec):
    src = g.FRAMES / f"scene_{sid}.png"
    out = g.CLIPS / f"scene_{sid}.mp4"
    g.CLIPS.mkdir(parents=True, exist_ok=True)
    graph = (f"[0]{motion_filter(motion, sec)},trim=duration={sec},format=gbrp[bg];"
             f"{PARTICLES},trim=duration={sec},format=gbrp[p];"
             "[bg][p]blend=all_mode=screen:all_opacity=0.9,format=yuv420p")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(src),
                    "-filter_complex", graph, "-t", str(sec), "-c:v", "libx264", "-crf", "17",
                    "-preset", "medium", str(out)], check=True)
    print(f"[{sid}] {motion} {sec}s -> {out}")


def main():
    g.set_episode(sys.argv[1])
    todo = motions()
    if len(sys.argv) > 2:
        todo = {sid: todo[sid] for sid in sys.argv[2].split(",")}
    else:
        todo = {s: m for s, m in todo.items() if not (g.CLIPS / f"scene_{s}.mp4").exists()}
    for sid, (motion, sec) in todo.items():
        render(sid, motion, sec)


if __name__ == "__main__":
    main()
