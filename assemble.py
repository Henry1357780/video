"""Сборка финального ролика: клипы по порядку сценария, плавные переходы, музыка.

    python assemble.py              # -> output/astral_journey.mp4
    python assemble.py --preview    # быстрый черновик 720p
"""
import argparse
import subprocess
import sys
from pathlib import Path

import generate as g

ROOT = Path(__file__).parent
MUSIC = ROOT / "audio" / "music.mp3"
OUT_DIR = ROOT / "output"
FADE = 1.0           # кроссфейд между сценами, с (совпадает с расчётом в music.py)
INTRO, OUTRO = 1.5, 4.0  # появление из чёрного и уход в чёрное
MUSIC_LUFS = -16     # мягкая громкость для релакс-ролика


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--episode", help="ролик серии из episodes/<имя>; музыка audio/<имя>.mp3")
    args = parser.parse_args()
    music, name = MUSIC, "astral_journey"
    if args.episode:
        g.set_episode(args.episode)
        music, name = ROOT / "audio" / f"{args.episode}.mp3", args.episode

    _, _, scenes = g.load_scenario()
    # REUSE — готовый клип из первого ролика, путь указан в промпте
    clips = [ROOT / prompt.split()[1] if prompt.startswith("REUSE") else g.CLIPS / f"scene_{sid}.mp4"
             for sid, (_, prompt) in scenes.items()]
    missing = [c.name for c in clips if not c.exists()]
    if missing:
        sys.exit(f"Нет клипов: {', '.join(missing)}")

    w, h = (1280, 720) if args.preview else (1920, 1080)
    inputs, chains = [], []
    for i, clip in enumerate(clips):
        inputs += ["-i", str(clip)]
        # Kling Pro отдаёт 1928x1072 — приводим всё к одному размеру и частоте
        chains.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
                      f"crop={w}:{h},fps=24,setsar=1,format=yuv420p[v{i}]")

    last, offset = "v0", 0.0
    for i in range(1, len(clips)):
        offset += duration(clips[i - 1]) - FADE
        out = f"x{i}"
        chains.append(f"[{last}][v{i}]xfade=transition=fade:duration={FADE}:offset={offset:.3f}[{out}]")
        last = out
    total = offset + duration(clips[-1])
    chains.append(f"[{last}]fade=t=in:d={INTRO},fade=t=out:st={total - OUTRO:.3f}:d={OUTRO}[vout]")

    m = len(clips)
    inputs += ["-i", str(music)]
    chains.append(f"[{m}:a]loudnorm=I={MUSIC_LUFS}:TP=-1.5:LRA=11,apad,atrim=0:{total:.3f},"
                  f"afade=t=in:d=2,afade=t=out:st={total - OUTRO:.3f}:d={OUTRO}[aout]")

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / (f"{name}_preview.mp4" if args.preview else f"{name}.mp4")
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats", *inputs,
           "-filter_complex", ";".join(chains), "-map", "[vout]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "veryfast" if args.preview else "slow",
           "-crf", "23" if args.preview else "17", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)]
    print(f"{len(clips)} сцен, итог {total:.1f} с -> {out}")
    subprocess.run(cmd, check=True)
    print("готово")


if __name__ == "__main__":
    main()
