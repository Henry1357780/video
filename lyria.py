"""Музыка через Lyria 3.5 на fal.ai ($0.10 за трек целиком).

    python lyria.py bhuloka          # промпт из music/bhuloka.txt -> audio/bhuloka.mp3
    python lyria.py bhuloka 0.1      # + кадр frames/scene_0.1 как подсказка настроения
"""
import sys
from pathlib import Path

from generate import FRAMES, download, load_key, run

ROOT = Path(__file__).parent


def main():
    name = sys.argv[1]
    prompt = (ROOT / "music" / f"{name}.txt").read_text(encoding="utf-8").strip()
    payload = {"prompt": prompt}
    if len(sys.argv) > 2:
        payload["image_url"] = (FRAMES / f"scene_{sys.argv[2]}.url").read_text(encoding="utf-8").strip()
    result = run("google/lyria/v3", payload, load_key(), name)
    out = ROOT / "audio" / f"{name}.mp3"
    out.parent.mkdir(exist_ok=True)
    if out.exists():
        n = 1
        while (old := out.with_name(f"{name}_v{n}.mp3")).exists():
            n += 1
        out.rename(old)
    download(result["audio"]["url"], out)
    print(f"готово: {out}")


if __name__ == "__main__":
    main()
