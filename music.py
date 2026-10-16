"""Музыка к ролику через ElevenLabs Music на fal.ai.

Длительность частей совпадает с монтажом: клипы по 10 с, кроссфейд 1 с,
значит каждая сцена занимает 9 с, а последняя — 10 с. Итого 253 с.

    python music.py            # сохранит audio/music.mp3
"""
import urllib.request
from pathlib import Path

from generate import load_key, run

ROOT = Path(__file__).parent
OUT = ROOT / "audio" / "music.mp3"

GLOBAL = [
    "slow meditative Indian classical instrumental", "Hindustani raga ambient",
    "constant tanpura drone on the same tonic Sa throughout", "bansuri bamboo flute", "soft sitar",
    "deep calm", "spacious reverb", "relaxing", "no tempo pulse",
    "the melody slowly ascends in pitch from section to section like climbing a scale",
    "smooth seamless transitions between sections",
]
NEGATIVE = [
    "vocals", "singing", "choir", "lyrics", "drums", "tabla", "percussion beat",
    "electronic", "EDM", "synth bass", "western orchestra", "pop", "rock",
    "sudden loud changes", "harsh",
]

# (название, секунды, стили) — по разделам scenario.md.
# Восхождение по регистрам: мелодия опирается на очередную свару
# (Са → Ре → Га → Ма → Па → Дха → Ни → верхняя Са), тампура всё время на Са.
SECTIONS = [
    ("Bhuloka - dawn on the Ganges", 36,
     ["lowest register (mandra saptak)", "melody rests on low Sa, the tonic",
      "tanpura drone alone at first", "gentle water ambience", "soft morning bird calls",
      "solo low bansuri enters slowly", "alap-like free unmetered opening"]),
    ("Bhuvarloka - rising to the sun", 27,
     ["melody rises into the middle register", "melodic focus on Re, the second degree",
      "airy wind texture", "soft bells", "bansuri and sitar in dialogue", "gradual brightening"]),
    ("Svarloka - the heaven of Indra", 45,
     ["middle register", "melodic focus on Ga, the third degree",
      "warm and radiant", "sitar and santoor shimmering", "celestial bells",
      "gentle veena", "majestic but calm", "slightly fuller texture"]),
    ("Maharloka - realm of the sages", 36,
     ["upper middle register melody", "melodic focus on Ma, the fourth degree",
      "sarod", "very slow", "contemplative", "deep drone underneath"]),
    ("Janaloka - pure sons of Brahma", 27,
     ["melodic focus on Pa, the fifth degree", "higher and lighter",
      "crystal singing bowls", "high gentle bansuri", "transparent"]),
    ("Tapoloka - realm of austerity", 27,
     ["entering the high register", "melodic focus on Dha, the sixth degree",
      "sparse", "breath-like swells", "deep stillness"]),
    ("Satyaloka - beyond the universe", 36,
     ["high register (tara saptak)", "melody climbs through Ni and resolves on high Sa, the octave",
      "fullest harmony", "all instruments gently together", "luminous", "climax of serenity",
      "then gradually dissolving into pure drone"]),
    ("Return - morning on the river", 19,
     ["melody descends gently from high Sa back down to low Sa",
      "only tanpura and water ambience", "last soft low bansuri phrase", "fade out to silence"]),
]


def main():
    plan = {
        "positive_global_styles": GLOBAL,
        "negative_global_styles": NEGATIVE,
        "sections": [
            {"section_name": name, "positive_local_styles": styles,
             "negative_local_styles": [], "duration_ms": sec * 1000, "lines": []}
            for name, sec, styles in SECTIONS
        ],
    }
    total = sum(sec for _, sec, _ in SECTIONS)
    print(f"Всего {total} с")
    result = run("fal-ai/elevenlabs/music",
                 {"composition_plan": plan, "respect_sections_durations": True},
                 load_key(), "music")
    OUT.parent.mkdir(exist_ok=True)
    if OUT.exists():
        OUT.rename(OUT.with_name(f"music_old_{int(OUT.stat().st_mtime)}.mp3"))
    urllib.request.urlretrieve(result["audio"]["url"], OUT)
    print(f"готово: {OUT}")


if __name__ == "__main__":
    main()
