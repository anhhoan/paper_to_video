from config import GENRE_PRESETS
from core.models import ArticleSource, ContextAnalysis
from core.utils import extract_and_parse_json
from script_writer.gemini_client import GeminiClient

class ContextAnalyzer:
    def __init__(self, client: GeminiClient):
        self.client = client

    def analyze(self, article: ArticleSource) -> ContextAnalysis:
        prompt = f'''Analyze article and return JSON: "genre" ("TRUE_CRIME"|"BREAKING_NEWS"|"STORYTELLING"), "summary", "tone", "pace" ("Slower"|"Normal"|"Fast"), "sensitive" (bool), "keywords" (list). Article:\n{article.text[:3000]}'''
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
            return ctx