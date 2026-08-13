import os
from dataclasses import dataclass
from typing import Dict, Tuple
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

@dataclass(frozen=True)
class GenrePreset:
    name: str
    voice: str
    rate: str
    pitch: str
    bgm: str
    style: str
    negative: str
    thumb_style: str
    badge: str
    accent: Tuple[int, int, int]
    sec_per_scene: float

GENRE_PRESETS: Dict[str, GenrePreset] = {
    "TRUE_CRIME": GenrePreset(
        name="TRUE_CRIME",
        voice="vi-VN-NamMinhNeural",
        rate="-10%",
        pitch="-4Hz",
        bgm="mystery",
        style="dark noir cinematic, low-key lighting, deep shadows, 35mm film grain",
        negative="gore, blood, corpse, wound",
        thumb_style="dark_cinematic",
        badge="HỒ SƠ VỤ ÁN",
        accent=(214, 40, 40),
        sec_per_scene=12.0
    ),
    "BREAKING_NEWS": GenrePreset(
        name="BREAKING_NEWS",
        voice="vi-VN-HoaiMyNeural",
        rate="+8%",
        pitch="+2Hz",
        bgm="news",
        style="high contrast photojournalism, documentary photo, sharp focus",
        negative="gore, graphic injury, fake logos",
        thumb_style="bold_news",
        badge="TIN NÓNG",
        accent=(255, 186, 8),
        sec_per_scene=8.0
    ),
    "STORYTELLING": GenrePreset(
        name="STORYTELLING",
        voice="vi-VN-HoaiMyNeural",
        rate="-4%",
        pitch="+0Hz",
        bgm="emotional",
        style="warm cinematic, soft golden hour light, painterly grading",
        negative="gore, horror, distorted anatomy",
        thumb_style="warm_story",
        badge="CÂU CHUYỆN",
        accent=(244, 140, 6),
        sec_per_scene=10.0
    )
}