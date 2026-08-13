import os
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
        return file_path