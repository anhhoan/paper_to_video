import os
from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip
from scrapers.article_scraper import ArticleScraper
from script_writer.gemini_client import GeminiClient
from tts_engine.synthesizer import TTSSynthesizer

class AutomationPipeline:
    def __init__(self):
        self.scraper = ArticleScraper()
        self.gemini = GeminiClient()
        self.tts = TTSSynthesizer()

    def _create_subtitles_clips(self, subtitles, video_width=1080, video_height=1920):
        """Tạo danh sách các TextClip phụ đề chạy theo từng từ/cụm từ"""
        sub_clips = []
        for sub in subtitles:
            # Tạo TextClip phụ đề màu vàng chữ viền đen
            try:
                txt_clip = (
                    TextClip(
                        font="Arial-Bold",
                        text=sub.text,
                        font_size=60,
                        color='yellow',
                        stroke_color='black',
                        stroke_width=3,
                        method='caption',
                        size=(video_width - 100, None)
                    )
                    .with_start(sub.start)
                    .with_duration(max(0.1, sub.end - sub.start))
                    .with_position(('center', video_height * 0.75)) # Đặt chữ ở 3/4 chiều cao video
                )
                sub_clips.append(txt_clip)
            except Exception as e:
                # Bỏ qua nếu lỗi font/ký tự đặc biệt
                continue
        return sub_clips

    def run(self, url: str, thumbnail_path: str, voice: str = "vi-VN-NamMinhNeural", output_video_path: str = "output/final_video.mp4") -> str:
        print("--> 1. Cào dữ liệu bài viết...")
        article_source = self.scraper.fetch(url)
        article_text = article_source.text if hasattr(article_source, 'text') else str(article_source)

        print("--> 2. Gemini phân tích & xuất JSON Kịch bản...")
        script_data = self.gemini.generate(article_text)
        voiceover_text = script_data.get("full_voiceover", "")

        print(f"📌 TIÊU ĐỀ VIDEO: {script_data.get('metadata', {}).get('title', '')}")
        print("--> 3. Đang đọc Voiceover & Tạo mốc thời gian Phụ đề (Subtitles)...")
        # synthesize_full_text cần trả về (audio_path, subtitles)
        audio_path, subtitles = self.tts.synthesize_full_text(voiceover_text, voice=voice)

        print("--> 4. Ghép Video + Audio + Chèn Phụ đề...")
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        
        audio_clip = AudioFileClip(audio_path)
        
        # Load Ảnh nền (mặc định dạng dọc 1080x1920 cho TikTok/Shorts)
        base_image = ImageClip(thumbnail_path)
        if hasattr(base_image, 'resized'):
            base_image = base_image.resized(height=1920)
        elif hasattr(base_image, 'resize'):
            base_image = base_image.resize(height=1920)

        video_clip = base_image.with_duration(audio_clip.duration).with_audio(audio_clip)

        # Chèn danh sách Phụ đề lên Video
        sub_clips = self._create_subtitles_clips(subtitles, video_width=1080, video_height=1920)
        if sub_clips:
            final_video = CompositeVideoClip([video_clip] + sub_clips)
        else:
            final_video = video_clip

        print("--> 5. Đang Xuất Video (Render)...")
        final_video.write_videofile(
            output_video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )

        # Dọn dẹp RAM
        final_video.close()
        audio_clip.close()
        base_image.close()

        print(f"✅ HOÀN TẤT! Video có phụ đề đã xuất tại: {output_video_path}")
        return output_video_path