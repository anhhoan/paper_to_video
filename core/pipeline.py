import os
from moviepy import ImageClip, AudioFileClip

from scrapers.article_scraper import ArticleScraper
from script_writer.gemini_client import GeminiClient
from tts_engine.synthesizer import TTSSynthesizer

class AutomationPipeline:
    def __init__(self):
        self.scraper = ArticleScraper()
        self.gemini = GeminiClient()
        self.tts = TTSSynthesizer()

    def run(
        self, 
        url: str, 
        thumbnail_path: str, 
        voice: str = "vi-VN-NamMinhNeural", 
        content_type: str = "news",  # Mặc định 'news' (tin tức), có thể truyền 'story' (kể chuyện/vụ án)
        output_video_path: str = "output/final_video.mp4"
    ) -> str:
        """
        Quy trình tạo Video từ URL và 1 Ảnh Thumbnail duy nhất (Đã tối ưu siêu tốc).
        """
        if not os.path.exists(thumbnail_path):
            raise FileNotFoundError(f"Không tìm thấy file ảnh tại: {thumbnail_path}")

        print("--> Bước 1: Lấy nội dung bài viết...")
        article_source = self.scraper.fetch(url)
        article_text = article_source.text if hasattr(article_source, 'text') else str(article_source)

        print(f"--> Bước 2: Dùng Gemini biên tập văn bản ({content_type})...")
        voiceover_text = self.gemini.generate(article_text, content_type=content_type)

        print("--> Bước 3: Tạo 1 file giọng đọc Edge-TTS duy nhất...")
        audio_path, _ = self.tts.synthesize_full_text(voiceover_text, voice=voice)

        print("--> Bước 4: Render Video hoàn chỉnh (1 Ảnh Thumbnail + Voice)...")
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        
        audio_clip = AudioFileClip(audio_path)
        
        # Đọc ảnh và resize về chuẩn 1080p
        base_image = ImageClip(thumbnail_path)
        if hasattr(base_image, 'resized'):
            base_image = base_image.resized(height=1080)
        elif hasattr(base_image, 'resize'):
            base_image = base_image.resize(height=1080)

        # Ghép ảnh với audio theo đúng thời lượng giọng đọc
        video_clip = base_image.with_duration(audio_clip.duration).with_audio(audio_clip)

        # Render siêu tốc (2 FPS, mã hóa ultrafast)
        video_clip.write_videofile(
            output_video_path,
            fps=2,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )

        # Giải phóng bộ nhớ RAM
        video_clip.close()
        audio_clip.close()
        base_image.close()

        print(f"✅ Hoàn tất! Video đã lưu tại: {output_video_path}")
        return output_video_path