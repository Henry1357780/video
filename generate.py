"""Генерация сцен из scenario.md на fal.ai.

Два пути:
  text    — Kling 3.0 рисует видео сразу из текста
  frame   — Nano Banana 2 рисует кадр-картину в frames/ (дёшево, можно утвердить)
  animate — Kling 3.0 оживляет готовый кадр из frames/ (стиль картины сохраняется)

Примеры:
    python generate.py 2.1 --mode frame              # кадр для сцены 2.1
    python generate.py 2.1 --mode animate --duration 5
    python generate.py all --mode frame              # кадры для всех сцен, которых ещё нет
    python generate.py 2.1 --mode text --model standard
"""
import argparse
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# без таймаута скачивание может зависнуть навсегда (так и случилось в первом прогоне)
socket.setdefaulttimeout(180)

ROOT = Path(__file__).parent
CLIPS = ROOT / "clips"
FRAMES = ROOT / "frames"
SCENARIO = ROOT / "scenario.md"
VIDEO_MODELS = {
    "standard": "fal-ai/kling-video/v3/standard/{}",
    "pro": "fal-ai/kling-video/v3/pro/{}",
}
IMAGE_MODEL = "fal-ai/nano-banana-2"
ANIMATE_HINT = (
    "Bring this painting gently to life, preserve the exact painterly oil-painting style, "
    "brushstrokes and colors, subtle slow motion, slow dreamlike camera movement"
)


def load_key():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("FAL_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("FAL_KEY не найден в .env")


def set_episode(name):
    """Ролики серии живут в episodes/<name>/ со своими scenario.md, frames/ и clips/."""
    global CLIPS, FRAMES, SCENARIO
    base = ROOT / "episodes" / name
    CLIPS, FRAMES, SCENARIO = base / "clips", base / "frames", base / "scenario.md"


def load_scenario():
    text = SCENARIO.read_text(encoding="utf-8")
    style = re.search(r"\*\*Единый стиль:?\*\*.*?\n> (.+)", text).group(1).strip()
    negative = re.search(r"\*\*Негативный промпт:\*\*\n> (.+)", text).group(1).strip()
    scenes = {}
    for sid, dur, prompt in re.findall(r"^\| (\d+\.\d+) \| (\d+) \| (.+?) \|", text, re.M):
        scenes[sid] = (int(dur), prompt.strip())
    return style, negative, scenes


def request(url, key, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Authorization", f"Key {key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"fal.ai ответил {e.code}: {e.read().decode(errors='replace')}")


def download(url, out, attempts=5):
    """Скачивание с повторами: fal иногда рвёт соединение посреди файла."""
    for n in range(1, attempts + 1):
        try:
            _, headers = urllib.request.urlretrieve(url, out)
            expected = int(headers.get("Content-Length", 0))
            if not expected or out.stat().st_size == expected:
                return
            print(f"файл неполный ({out.stat().st_size} из {expected}), повтор {n}")
        except OSError as e:
            print(f"обрыв скачивания: {e}, повтор {n}")
        time.sleep(5)
    sys.exit(f"не удалось скачать {url}")


def run(endpoint, payload, key, sid):
    job = request(f"https://queue.fal.run/{endpoint}", key, payload)
    print(f"[{sid}] в очереди, request_id={job['request_id']}")
    while True:
        time.sleep(5)
        status = request(job["status_url"], key)["status"]
        print(f"[{sid}] {status}")
        if status == "COMPLETED":
            return request(job["response_url"], key)
        if status not in ("IN_QUEUE", "IN_PROGRESS"):
            sys.exit(f"[{sid}] ошибка: {status}")


def edit_frame(sid, instruction, key):
    """Точечная правка готового кадра (например, добавить бивни), остальное не трогаем."""
    src = FRAMES / f"scene_{sid}.png"
    payload = {
        "prompt": f"{instruction}. Change nothing else: same composition, style, colors and figures.",
        "image_urls": [src.with_suffix(".url").read_text(encoding="utf-8").strip()],
        "aspect_ratio": "16:9", "resolution": "2K", "output_format": "png",
    }
    url = run(f"{IMAGE_MODEL}/edit", payload, key, sid)["images"][0]["url"]
    src.rename(FRAMES / "rejected" / f"scene_{sid}_before_edit.png")
    download(url, src)
    src.with_suffix(".url").write_text(url, encoding="utf-8")
    print(f"[{sid}] кадр исправлен: {src}")


def make_frame(sid, prompt, style, key, ref=None):
    text = (f"A single still painting, wide 16:9 composition: {prompt}. {style}. "
            "Full-bleed image filling the entire canvas edge to edge, no border, no frame, "
            "no decorative margin. No signature, no text, no letters, no watermark. "
            "Show only the figures explicitly described; do not add any other people, "
            "flying figures, celestial musicians or dancers. No figure has wings. "
            "Do not add any buildings, temples, cities, villages, landscape, ground or pedestals "
            "that are not explicitly described. If buildings are described, they are Hindu temples "
            "and palaces with shikhara towers and chhatris; "
            "no mosques, no minarets, no Islamic or Mughal architecture.")
    payload = {"aspect_ratio": "16:9", "resolution": "2K", "output_format": "png"}
    endpoint = IMAGE_MODEL
    if ref:
        # тот же персонаж, что на кадре-образце (например, йогин из 0.2)
        payload["image_urls"] = [(FRAMES / f"scene_{ref}.url").read_text(encoding="utf-8").strip()]
        text = ("Keep exactly the same person as in the reference image: same face, hair, "
                f"beard, body and clothing. New scene: {text}")
        endpoint = f"{IMAGE_MODEL}/edit"
    payload["prompt"] = text
    url = run(endpoint, payload, key, sid)["images"][0]["url"]
    FRAMES.mkdir(exist_ok=True)
    out = FRAMES / f"scene_{sid}.png"
    download(url, out)
    # Kling берёт кадр по ссылке — сохраняем её рядом с картинкой
    out.with_suffix(".url").write_text(url, encoding="utf-8")
    print(f"[{sid}] кадр готов: {out}")


def make_video(sid, duration, prompt, style, negative, key, model, animate):
    payload = {
        "negative_prompt": negative,
        "duration": str(duration),
        "generate_audio": False,
    }
    if animate:
        url_file = FRAMES / f"scene_{sid}.url"
        if not url_file.exists():
            sys.exit(f"[{sid}] нет кадра — сначала --mode frame")
        payload["start_image_url"] = url_file.read_text(encoding="utf-8").strip()
        payload["prompt"] = f"{prompt}. {ANIMATE_HINT}"
        endpoint = VIDEO_MODELS[model].format("image-to-video")
    else:
        payload["prompt"] = f"{prompt}. {style}"
        payload["aspect_ratio"] = "16:9"
        endpoint = VIDEO_MODELS[model].format("text-to-video")
    url = run(endpoint, payload, key, sid)["video"]["url"]
    CLIPS.mkdir(exist_ok=True)
    out = CLIPS / f"scene_{sid}.mp4"
    download(url, out)
    print(f"[{sid}] видео готово: {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scene", help="номер сцены (например 2.1), список через запятую или all")
    parser.add_argument("--mode", choices=["text", "frame", "animate"], default="animate")
    parser.add_argument("--duration", type=int, help="переопределить длительность, сек")
    parser.add_argument("--model", choices=VIDEO_MODELS, default="pro")
    parser.add_argument("--ref", help="сцена-образец персонажа для --mode frame (например 0.2)")
    parser.add_argument("--edit", help="точечная правка готового кадра: текст инструкции")
    parser.add_argument("--episode", help="ролик серии из episodes/<имя>, например bhuloka")
    args = parser.parse_args()
    if args.episode:
        set_episode(args.episode)

    key = load_key()
    if args.edit:
        edit_frame(args.scene, args.edit, key)
        return
    style, negative, scenes = load_scenario()
    ids = list(scenes) if args.scene == "all" else args.scene.split(",")
    for sid in ids:
        if sid not in scenes:
            sys.exit(f"Сцена {sid} не найдена в scenario.md")
        duration, prompt = scenes[sid]
        if prompt.startswith("REUSE"):
            continue  # готовый клип из первого ролика, генерировать нечего
        if args.mode == "frame":
            if args.scene == "all" and (FRAMES / f"scene_{sid}.png").exists():
                continue
            make_frame(sid, prompt, style, key, args.ref)
        else:
            if args.scene == "all" and (CLIPS / f"scene_{sid}.mp4").exists():
                continue
            make_video(sid, args.duration or duration, prompt, style, negative, key,
                       args.model, animate=args.mode == "animate")


if __name__ == "__main__":
    main()
