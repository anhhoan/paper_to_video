import math
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
        user_prompt = f"Genre: {context.genre}\nStyle: {preset.style}\nContent:\n{text[:4000]}"
        
        raw_resp = self.client.generate(user_prompt, system_instruction=system_prompt)
        data = extract_and_parse_json(raw_resp)

        scenes = []
        for idx, s in enumerate(data.get("scenes", [])):
            role = "hook" if idx == 0 else ("outro" if idx == len(data.get("scenes", []))-1 else s.get("role", "body"))
            scenes.append(Scene(scene_id=idx + 1, voiceover_text=s.get("voiceover_text", ""), visual_prompt=f"{s.get('visual_prompt', '')}, {preset.style}", on_screen_text=s.get("on_screen_text", ""), role=role))

        return VideoScript(title=data.get("title", "Untitled"), description=data.get("description", ""), tags=data.get("tags", []), scenes=scenes, context=context, thumbnail_text=data.get("thumbnail_text", "XEM NGAY"))