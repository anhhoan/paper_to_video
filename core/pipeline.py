import os
import glob
import random
from moviepy import (
    ImageClip, 
    AudioFileClip, 
    CompositeAudioClip, 
    TextClip, 
    CompositeVideoClip,
    afx
)
from scrapers.article_scraper import ArticleScraper
from script_writer.gemini_client import GeminiClient
from tts_engine.synthesizer import TTSSynthesizer

class AutomationPipeline:
    def __init__(self, bgm_base_dir: str = "assets/audio"):
        self.scraper = ArticleScraper()
        self.gemini = GeminiClient()
        self.tts = TTSSynthesizer()
        self.bgm_base_dir = bgm_base_dir

    def _select_auto_bgm(self, category: str) -> str | None:
        """Tự động chọn 1 file nhạc ngẫu nhiên trong thư mục tương ứng với thể loại"""
        category_clean = str(category).upper().strip()
        
        # Xác định thư mục con tương ứng
        if "STORY" in category_clean or "CÂU CHUYỆN" in category_clean or "VỤ ÁN" in category_clean:
            folder_name = "story"
        else:
            folder_name = "news"

        target_dir = os.path.join(self.bgm_base_dir, folder_name)
        
        # Quét tất cả file .mp3 trong thư mục thể loại đó
        music_files = glob.glob(os.path.join(target_dir, "*.mp3"))
        
        if not music_files:
            print(f"[Warning] Không tìm thấy file mp3 nào trong thư mục: {target_dir}. Sẽ bỏ qua nhạc nền.")
            return None

        selected_music = random.choice(music_files)
        print(f"🎵 Nhạc nền tự động chọn ({folder_name.upper()}): {os.path.basename(selected_music)}")
        return selected_music

    def _prepare_background_music(self, bgm_path: str, target_duration: float, volume: float = 0.10):
        """Xử lý nhạc nền: lặp lại nếu thiếu, cắt đúng độ dài thoại, giảm âm lượng"""
        if not bgm_path or not os.path.exists(bgm_path):
            return None

        try:
            bgm = AudioFileClip(bgm_path)
            
            # Lặp lại nếu nhạc ngắn hơn thoại
            if bgm.duration < target_duration:
                loop_count = int(target_duration // bgm.duration) + 1
                if hasattr(afx, 'audio_loop'):
                    bgm = afx.audio_loop(bgm, n=loop_count)
                elif hasattr(bgm, 'loop'):
                    bgm = bgm.loop(n=loop_count)

            # Cắt nhạc vừa bằng thoại
            bgm = bgm.with_section(0, target_duration) if hasattr(bgm, 'with_section') else bgm.subclip(0, target_duration)
            
            # Giảm âm lượng nhạc nền xuống 10% để không đè giọng đọc
            if hasattr(bgm, 'with_effects'):
                bgm = bgm.with_effects([afx.MultiplyVolume(volume)])
            elif hasattr(bgm, 'volumex'):
                bgm = bgm.volumex(volume)
                
            return bgm
        except Exception as e:
            print(f"[Warning] Lỗi khi xử lý nhạc nền: {e}")
            return None

    def run(
        self, 
        url: str, 
        thumbnail_path: str, 
        voice: str = "vi-VN-NamMinhNeural", 
        enable_bgm: bool = True,  # Bật/Tắt nhạc nền tự động
        output_video_path: str = "output/final_video.mp4"
    ) -> str:
        
        print("--> 1. Cào dữ liệu bài viết...")
        article_source = self.scraper.fetch(url)
        article_text = article_source.text if hasattr(article_source, 'text') else str(article_source)

        print("--> 2. Gemini phân tích & xuất JSON Kịch bản...")
        script_data = self.gemini.generate(article_text)
        
        # Lấy thể loại Gemini tự phân loại (TIN TỨC hoặc CÂU CHUYỆN)
        category = script_data.get("analysis", {}).get("category", "TIN TỨC")
        voiceover_text = script_data.get("full_voiceover", "")

        print("--> 3. Tạo Giọng đọc & Phụ đề...")
        voice_audio_path, subtitles = self.tts.synthesize_full_text(voiceover_text, voice=voice)
        voice_clip = AudioFileClip(voice_audio_path)

        # 4. Tự động chọn & Trộn nhạc nền theo thể loại
        bgm_clip = None
        if enable_bgm:
            selected_bgm_path = self._select_auto_bgm(category)
            if selected_bgm_path:
                bgm_clip = self._prepare_background_music(
                    selected_bgm_path, 
                    target_duration=voice_clip.duration, 
                    volume=0.10 # Giữ mức 10%
                )

        if bgm_clip:
            final_audio = CompositeAudioClip([voice_clip, bgm_clip])
        else:
            final_audio = voice_clip

        print("--> 5. Dựng Video & Chèn Phụ đề...")
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        
        base_image = ImageClip(thumbnail_path)
        if hasattr(base_image, 'resized'):
            base_image = base_image.resized(height=1920)
        elif hasattr(base_image, 'resize'):
            base_image = base_image.resize(height=1920)

        video_clip = base_image.with_duration(final_audio.duration).with_audio(final_audio)

        # Chèn danh sách Phụ đề
        sub_clips = self._create_subtitles_clips(subtitles, video_width=1080, video_height=1920)
        final_video = CompositeVideoClip([video_clip] + sub_clips) if sub_clips else video_clip

        print("--> 6. Đang Xuất Video (Render)...")
        final_video.write_videofile(
            output_video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )

        # Dọn dẹp tài nguyên
        final_video.close()
        voice_clip.close()
        if bgm_clip: 
            bgm_clip.close()
        base_image.close()

        print(f"✅ HOÀN TẤT! Video tại: {output_video_path}")
        return output_video_path