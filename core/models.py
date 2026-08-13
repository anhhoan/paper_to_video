import re
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ArticleSource:
    text: str
    title: str = ""
    url: str = ""
    site_name: str = ""
    author: str = ""
    published: str = ""
    origin: str = "web"

@dataclass
class ContextAnalysis:
    genre: str = "STORYTELLING"
    genre_confidence: float = 0.8
    summary: str = ""
    tone: str = "Neutral"
    pace: str = "Normal"
    bgm_mood: str = "mystery"
    thumbnail_style: str = "dark_cinematic"
    visual_style: str = ""
    voice: str = "vi-VN-NamMinhNeural"
    rate: str = "0%"
    pitch: str = "0Hz"
    keywords: List[str] = field(default_factory=list)
    sensitive: bool = False
    notes: str = ""
    analysed_by: str = "gemini-2.0-flash"

    def apply_overrides(self, genre_name: str, presets_map):
        if genre_name in presets_map:
            p = presets_map[genre_name]
            self.genre = p.name
            self.voice = p.voice
            self.rate = p.rate
            self.pitch = p.pitch
            self.bgm_mood = p.bgm
            self.thumbnail_style = p.thumb_style
            self.visual_style = p.style

@dataclass
class Scene:
    scene_id: int
    voiceover_text: str
    visual_prompt: str
    pause_duration: float = 0.5
    on_screen_text: str = ""
    role: str = "body"
    audio_path: Optional[str] = None
    audio_duration: float = 0.0
    image_path: Optional[str] = None
    start_time: float = 0.0

    def __post_init__(self):
        cleaned = re.sub(r'\b(cmd|logo|blood|gore|corpse)\b', '', self.visual_prompt, flags=re.IGNORECASE)
        self.visual_prompt = " ".join(cleaned.split())

@dataclass
class VideoScript:
    title: str
    description: str
    tags: List[str]
    scenes: List[Scene]
    context: Optional[ContextAnalysis] = None
    thumbnail_text: str = ""
    source_url: str = ""

@dataclass
class SubtitleLine:
    index: int
    start: float
    end: float
    text: str