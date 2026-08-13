import os
import re
import asyncio
import edge_tts
from gtts import gTTS

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

    async def _synth_full_async(self, text: str, voice: str, output_path: str) -> str:
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
            try:
                communicate = edge_tts.Communicate(text=clean_text, voice=clean_voice)
                
                with open(temp_file, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])

                if os.path.exists(temp_file) and os.path.getsize(temp_file) > 1024:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    os.rename(temp_file, output_path)
                    return output_path
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
        print(f"-> Đang dùng Google TTS (gTTS) dự phòng...")
        tts = gTTS(text=clean_text, lang='vi', slow=False)
        tts.save(output_path)
        return output_path

    def synthesize_full_text(self, text: str, voice: str = "vi-VN-NamMinhNeural") -> tuple[str, str]:
        output_path = os.path.join(self.output_dir, "full_voice.mp3")
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                res_path = loop.run_until_complete(self._synth_full_async(text, voice, output_path))
            else:
                res_path = loop.run_until_complete(self._synth_full_async(text, voice, output_path))
        except Exception:
            res_path = asyncio.run(self._synth_full_async(text, voice, output_path))

        return res_path, "edge-tts"

    # Alias giữ tương thích nếu code cũ còn gọi
    def synthesize_scene(self, scene, voice: str = "vi-VN-NamMinhNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        text = getattr(scene, 'voiceover_text', str(scene))
        path, provider = self.synthesize_full_text(text, voice)
        return path, []