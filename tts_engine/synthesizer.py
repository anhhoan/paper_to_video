import os
import re
import asyncio
import edge_tts
from gtts import gTTS
from core.models import SubtitleLine

class TTSSynthesizer:
    def __init__(self, output_dir: str = "output/audio"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Bỏ ghi chú ngoặc, Markdown, HTML, icon/ký tự lạ gây nghẽn Edge-TTS
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'[\*\#\_\~\`\"“”\”\“\‘\’\']', '', text)
        text = re.sub(r'[%$&@+=/\\|<>:~]', ' ', text)
        text = re.sub(r'[\r\n\t]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _fallback_gtts(self, text: str, output_path: str) -> list[SubtitleLine]:
        """Dự phòng gTTS và tự tạo timestamp cho phụ đề dựa trên độ dài từ"""
        print("-> Đang dùng Google TTS (gTTS) dự phòng...")
        tts = gTTS(text=text, lang='vi', slow=False)
        tts.save(output_path)

        words = text.split()
        duration_per_word = 0.35  # Thời lượng trung bình 1 từ tiếng Việt
        subtitles = []
        for idx, word in enumerate(words):
            start = idx * duration_per_word
            end = start + duration_per_word
            subtitles.append(SubtitleLine(index=idx + 1, start=start, end=end, text=word))
        return subtitles

    async def _synth_full_async(self, text: str, voice: str, output_path: str) -> tuple[str, list[SubtitleLine]]:
        clean_text = self._clean_text(text)
        if not clean_text:
            clean_text = "Nội dung văn bản rỗng."

        clean_voice = str(voice).strip() if voice else "vi-VN-NamMinhNeural"
        if "HoaiMy" in clean_voice:
            clean_voice = "vi-VN-HoaiMyNeural"
        else:
            clean_voice = "vi-VN-NamMinhNeural"

        # Thử Edge-TTS tối đa 3 lần với delay linh hoạt
        for attempt in range(1, 4):
            temp_file = output_path + ".tmp"
            subtitles = []
            sub_idx = 1
            try:
                communicate = edge_tts.Communicate(text=clean_text, voice=clean_voice)
                
                with open(temp_file, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                        # Bắt sự kiện WordBoundary để lấy mốc thời gian phụ đề
                        elif chunk["type"] == "WordBoundary":
                            start = chunk["offset"] / 10_000_000.0
                            end = (chunk["offset"] + chunk["duration"]) / 10_000_000.0
                            subtitles.append(SubtitleLine(index=sub_idx, start=start, end=end, text=chunk["text"]))
                            sub_idx += 1

                if os.path.exists(temp_file) and os.path.getsize(temp_file) > 1024:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    os.rename(temp_file, output_path)
                    return output_path, subtitles
                else:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)

            except Exception as e:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
                
                if attempt < 3:
                    await asyncio.sleep(attempt * 1.5)
                    continue
                print(f"[Warning] Edge-TTS không phản hồi ({e}). Chuyển sang Google TTS dự phòng...")

        # Fallback sang Google TTS (gTTS)
        subtitles = self._fallback_gtts(clean_text, output_path)
        return output_path, subtitles

    def synthesize_full_text(self, text: str, voice: str = "vi-VN-NamMinhNeural") -> tuple[str, list[SubtitleLine]]:
        output_path = os.path.join(self.output_dir, "full_voice.mp3")
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                res_path, subtitles = loop.run_until_complete(self._synth_full_async(text, voice, output_path))
            else:
                res_path, subtitles = loop.run_until_complete(self._synth_full_async(text, voice, output_path))
        except Exception:
            res_path, subtitles = asyncio.run(self._synth_full_async(text, voice, output_path))

        return res_path, subtitles

    # Alias giữ tương thích nếu code cũ còn gọi
    def synthesize_scene(self, scene, voice: str = "vi-VN-NamMinhNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        text = getattr(scene, 'voiceover_text', str(scene))
        path, subtitles = self.synthesize_full_text(text, voice)
        return path, subtitles