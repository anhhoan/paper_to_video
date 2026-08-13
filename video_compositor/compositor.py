import os
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

        return raw_path