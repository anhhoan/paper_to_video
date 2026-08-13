import json
import re

def extract_and_parse_json(text: str) -> dict:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text).strip()
    text = re.sub(r',\s*([}\]])', r'\1', text)
    
    open_curly = text.count('{') - text.count('}')
    open_square = text.count('[') - text.count(']')
    text += ']' * max(0, open_square)
    text += '}' * max(0, open_curly)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("Failed to parse LLM output as JSON.")

def format_srt_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
