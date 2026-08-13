import os

# Định nghĩa cấu trúc các file và nội dung code
FILES = {
    "requirements.txt": """google-genai>=0.1.0
requests>=2.31.0
trafilatura>=1.6.0
newspaper3k>=0.2.8
beautifulsoup4>=4.12.0
edge-tts>=6.1.9
Pillow>=10.0.0
moviepy>=2.0.0.dev2
streamlit>=1.30.0
pydantic>=2.0.0
python-dotenv>=1.0.0""",

    ".env.example": "GEMINI_API_KEY=your_gemini_api_key_here",

    "config.py": """import os
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
}""",

    "core/__init__.py": "",
    "core/models.py": """import re
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
        cleaned = re.sub(r'\\b(cmd|logo|blood|gore|corpse)\\b', '', self.visual_prompt, flags=re.IGNORECASE)
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
    text: str""",

    "core/utils.py": """import json
import re

def extract_and_parse_json(text: str) -> dict:
    text = re.sub(r'```json\\s*', '', text)
    text = re.sub(r'```\\s*', '', text).strip()
    text = re.sub(r',\\s*([}\\]])', r'\\1', text)
    
    open_curly = text.count('{') - text.count('}')
    open_square = text.count('[') - text.count(']')
    text += ']' * max(0, open_square)
    text += '}' * max(0, open_curly)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\\{.*\\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("Failed to parse LLM output as JSON.")

def format_srt_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
""",

    "scrapers/__init__.py": "",
    "scrapers/article_scraper.py": """import requests
import re
from bs4 import BeautifulSoup
import trafilatura
from newspaper import Article
from core.models import ArticleSource

class ArticleScraper:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch(self, url: str) -> ArticleSource:
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(downloaded, include_links=False, include_images=False, output_format='txt')
                if result and len(result.strip()) > 100:
                    return ArticleSource(text=result.strip(), url=url, origin="trafilatura")
        except Exception:
            pass

        try:
            article = Article(url)
            article.download()
            article.parse()
            if article.text and len(article.text.strip()) > 100:
                return ArticleSource(text=article.text.strip(), title=article.title, url=url, origin="newspaper3k")
        except Exception:
            pass

        try:
            resp = requests.get(url, timeout=self.timeout, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                container = soup.find('div', class_=re.compile(r'(fck_detail|detail-content|content_detail|post-content)')) or soup.find('body')
                paragraphs = [p.get_text().strip() for p in container.find_all('p') if len(p.get_text().strip()) > 20]
                full_text = "\\n".join(paragraphs)
                if len(full_text) > 100:
                    return ArticleSource(text=full_text, url=url, origin="beautifulsoup")
        except Exception as e:
            raise RuntimeError(f"All scraper layers failed for URL {url}: {e}")

        raise ValueError(f"Could not extract content from {url}")""",

    "script_writer/__init__.py": "",
    "script_writer/gemini_client.py": """import requests
from config import GEMINI_API_KEY

class GeminiClient:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing in .env file.")

        url = f"{self.endpoint}?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
            ]
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]""",

    "script_writer/context_analyzer.py": """from config import GENRE_PRESETS
from core.models import ArticleSource, ContextAnalysis
from core.utils import extract_and_parse_json
from script_writer.gemini_client import GeminiClient

class ContextAnalyzer:
    def __init__(self, client: GeminiClient):
        self.client = client

    def analyze(self, article: ArticleSource) -> ContextAnalysis:
        prompt = f'''Analyze article and return JSON: "genre" ("TRUE_CRIME"|"BREAKING_NEWS"|"STORYTELLING"), "summary", "tone", "pace" ("Slower"|"Normal"|"Fast"), "sensitive" (bool), "keywords" (list). Article:\\n{article.text[:3000]}'''
        try:
            raw = self.client.generate(prompt, system_instruction="Return strict valid JSON only.")
            data = extract_and_parse_json(raw)
            genre = data.get("genre", "STORYTELLING")
            ctx = ContextAnalysis(genre=genre, summary=data.get("summary", ""), tone=data.get("tone", "Neutral"), pace=data.get("pace", "Normal"), keywords=data.get("keywords", []), sensitive=data.get("sensitive", False))
            ctx.apply_overrides(genre, GENRE_PRESETS)
            return ctx
        except Exception:
            text_lower = article.text.lower()
            genre = "TRUE_CRIME" if any(k in text_lower for k in ["vụ án", "sát hại", "cảnh sát"]) else ("BREAKING_NEWS" if any(k in text_lower for k in ["khẩn cấp", "mới nhất"]) else "STORYTELLING")
            ctx = ContextAnalysis(genre=genre, analysed_by="heuristic_fallback")
            ctx.apply_overrides(genre, GENRE_PRESETS)
            return ctx""",

    "script_writer/script_generator.py": """import math
from typing import List
from config import GENRE_PRESETS
from core.models import ContextAnalysis, Scene, VideoScript
from core.utils import extract_and_parse_json
from script_writer.gemini_client import GeminiClient

class ScriptGenerator:
    def __init__(self, client: GeminiClient):
        self.client = client

    def generate_script(self, text: str, context: ContextAnalysis, target_sec: float = 60.0) -> VideoScript:
        preset = GENRE_PRESETS.get(context.genre, GENRE_PRESETS["STORYTELLING"])
        num_scenes = max(3, math.ceil(target_sec / preset.sec_per_scene))

        system_prompt = f'''Generate JSON script with {num_scenes} scenes: {{"title": "", "description": "", "tags": [], "thumbnail_text": "", "scenes": [{{"scene_id": 1, "voiceover_text": "", "visual_prompt": "", "on_screen_text": "", "role": "hook"|"body"|"twist"|"outro"}}]}}'''
        user_prompt = f"Genre: {context.genre}\\nStyle: {preset.style}\\nContent:\\n{text[:4000]}"
        
        raw_resp = self.client.generate(user_prompt, system_instruction=system_prompt)
        data = extract_and_parse_json(raw_resp)

        scenes = []
        for idx, s in enumerate(data.get("scenes", [])):
            role = "hook" if idx == 0 else ("outro" if idx == len(data.get("scenes", []))-1 else s.get("role", "body"))
            scenes.append(Scene(scene_id=idx + 1, voiceover_text=s.get("voiceover_text", ""), visual_prompt=f"{s.get('visual_prompt', '')}, {preset.style}", on_screen_text=s.get("on_screen_text", ""), role=role))

        return VideoScript(title=data.get("title", "Untitled"), description=data.get("description", ""), tags=data.get("tags", []), scenes=scenes, context=context, thumbnail_text=data.get("thumbnail_text", "XEM NGAY"))""",

    "tts_engine/__init__.py": "",
    "tts_engine/synthesizer.py": """import os
import asyncio
import edge_tts
from typing import List, Tuple
from core.models import Scene, SubtitleLine

class TTSSynthesizer:
    def __init__(self, output_dir: str = "output/audio"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    async def _synth_scene_async(self, scene: Scene, voice: str, rate: str, pitch: str) -> Tuple[str, List[SubtitleLine]]:
        file_path = os.path.join(self.output_dir, f"scene_{scene.scene_id}.mp3")
        communicate = edge_tts.Communicate(scene.voiceover_text, voice, rate=rate, pitch=pitch)
        subtitles, sub_idx = [], 1
        
        with open(file_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start = chunk["offset"] / 10_000_000.0
                    end = (chunk["offset"] + chunk["duration"]) / 10_000_000.0
                    subtitles.append(SubtitleLine(index=sub_idx, start=start, end=end, text=chunk["text"]))
                    sub_idx += 1
        return file_path, subtitles

    def synthesize_scene(self, scene: Scene, voice: str, rate: str = "+0%", pitch: str = "+0Hz") -> Tuple[str, List[SubtitleLine]]:
        return asyncio.run(self._synth_scene_async(scene, voice, rate, pitch))""",

    "thumbnail_gen/__init__.py": "",
    "thumbnail_gen/pollinations.py": """import os
import time
import requests
from PIL import Image, ImageDraw

class PollinationsGen:
    def __init__(self, output_dir: str = "output/images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_image(self, prompt: str, scene_id: int, width: int = 1280, height: int = 720) -> str:
        safe_prompt = requests.utils.quote(prompt)
        file_path = os.path.join(self.output_dir, f"scene_{scene_id}.jpg")

        for attempt in range(3):
            url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={width}&height={height}&seed={int(time.time())+attempt}&model=flux"
            try:
                resp = requests.get(url, timeout=20)
                if resp.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(resp.content)
                    time.sleep(1.0)
                    return file_path
            except Exception:
                time.sleep(1.0)

        img = Image.new("RGB", (width, height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        draw.text((width // 4, height // 2), f"Placeholder Image Scene {scene_id}", fill=(200, 200, 200))
        img.save(file_path)
        return file_path""",

    "thumbnail_gen/composer.py": """import os
from PIL import Image, ImageDraw, ImageFont

class ThumbnailComposer:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_thumbnail(self, bg_image_path: str, text: str, badge_text: str, accent_color: tuple) -> str:
        img = Image.open(bg_image_path).convert("RGBA").resize((1280, 720))
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        for y in range(360, 720):
            alpha = int(210 * ((y - 360) / 360))
            draw_ov.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))
        
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 300, 100], fill=accent_color)
        draw.text((65, 62), badge_text, fill=(255, 255, 255))
        draw.text((50, 550), text, fill=(255, 255, 255))
        
        out_path = os.path.join(self.output_dir, "thumbnail.png")
        img.convert("RGB").save(out_path)
        return out_path""",

    "video_compositor/__init__.py": "",
    "video_compositor/bgm_library.py": """import os

class BGMLibrary:
    def __init__(self, music_dir: str = "assets/music"):
        self.music_dir = music_dir
        os.makedirs(music_dir, exist_ok=True)

    def get_track(self, mood: str) -> str:
        if os.path.exists(self.music_dir):
            for file in os.listdir(self.music_dir):
                if mood.lower() in file.lower() and file.endswith((".mp3", ".wav")):
                    return os.path.join(self.music_dir, file)
        return "" """,

    "video_compositor/compositor.py": """import os
import subprocess
from typing import List
from PIL import Image
import numpy as np
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from core.models import Scene

class VideoCompositor:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def build_video(self, scenes: List[Scene], bgm_path: str = "") -> str:
        clips = []
        for scene in scenes:
            if not scene.image_path or not scene.audio_path:
                continue
            audio_clip = AudioFileClip(scene.audio_path)
            duration = audio_clip.duration + scene.pause_duration
            
            img_clip = ImageClip(scene.image_path).with_duration(duration)
            def zoom_transform(get_frame, t):
                frame = get_frame(t)
                scale = 1.0 + 0.1 * np.sin(np.pi * t / duration)
                h, w, _ = frame.shape
                nh, nw = int(h * scale), int(w * scale)
                pil_img = Image.fromarray(frame).resize((nw, nh), Image.Resampling.LANCZOS)
                crop_x, crop_y = (nw - w) // 2, (nh - h) // 2
                return np.array(pil_img.crop((crop_x, crop_y, crop_x + w, crop_y + h)))

            img_clip = img_clip.transform(zoom_transform).with_audio(audio_clip)
            clips.append(img_clip)

        final_clip = concatenate_videoclips(clips, method="compose")
        raw_path = os.path.join(self.output_dir, "temp_raw.mp4")
        out_path = os.path.join(self.output_dir, "final_video.mp4")
        
        final_clip.write_videofile(raw_path, fps=24, codec="libx264", audio_codec="aac")

        if bgm_path and os.path.exists(bgm_path):
            cmd = f'ffmpeg -y -i "{raw_path}" -stream_loop -1 -i "{bgm_path}" -filter_complex "[1:a]volume=0.2[bgm];[0:a][bgm]sidechaincompress=threshold=0.03:ratio=5[aout]" -map 0:v -map "[aout]" -c:v copy -shortest "{out_path}"'
            subprocess.run(cmd, shell=True, check=True)
            return out_path

        return raw_path""",

    "core/pipeline.py": """from config import GENRE_PRESETS
from scrapers.article_scraper import ArticleScraper
from script_writer.gemini_client import GeminiClient
from script_writer.context_analyzer import ContextAnalyzer
from script_writer.script_generator import ScriptGenerator
from tts_engine.synthesizer import TTSSynthesizer
from thumbnail_gen.pollinations import PollinationsGen
from video_compositor.bgm_library import BGMLibrary
from video_compositor.compositor import VideoCompositor

class AutomationPipeline:
    def __init__(self):
        self.scraper = ArticleScraper()
        self.client = GeminiClient()
        self.analyzer = ContextAnalyzer(self.client)
        self.script_gen = ScriptGenerator(self.client)
        self.tts = TTSSynthesizer()
        self.img_gen = PollinationsGen()
        self.bgm_lib = BGMLibrary()
        self.compositor = VideoCompositor()

    def run_url(self, url: str) -> str:
        article = self.scraper.fetch(url)
        context = self.analyzer.analyze(article)
        script = self.script_gen.generate_script(article.text, context)
        
        preset = GENRE_PRESETS[context.genre]
        for scene in script.scenes:
            audio_file, _ = self.tts.synthesize_scene(scene, preset.voice, preset.rate, preset.pitch)
            scene.audio_path = audio_file
            scene.image_path = self.img_gen.generate_image(scene.visual_prompt, scene.scene_id)

        bgm = self.bgm_lib.get_track(context.bgm_mood)
        return self.compositor.build_video(script.scenes, bgm)""",

    "ui/__init__.py": "",
    "ui/app.py": """import streamlit as st
from core.pipeline import AutomationPipeline

st.set_page_config(page_title="Video Automation Tool", layout="wide")
st.title("🎬 True Crime & Storytelling Automation")

url = st.text_input("Dán đường dẫn bài báo (URL):")
if st.button("Tạo Video Tự Động"):
    if not url:
        st.error("Vui lòng nhập URL!")
    else:
        with st.spinner("Đang xử lý toàn bộ pipeline... (Cào bài, viết kịch bản, tạo audio, vẽ ảnh, dựng video)"):
            try:
                pipeline = AutomationPipeline()
                video_path = pipeline.run_url(url)
                st.success("Tạo Video Thành Công!")
                st.video(video_path)
            except Exception as e:
                st.error(f"Lỗi: {e}")"""
}

def create_project():
    print("🚀 Đang khởi tạo cấu trúc dự án...")
    for path, content in FILES.items():
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [+] Đã tạo file: {path}")
    print("\n✅ Hoàn tất tạo bộ mã nguồn dự án!")

if __name__ == "__main__":
    create_project()