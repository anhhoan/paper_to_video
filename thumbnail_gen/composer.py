import os
from PIL import Image, ImageDraw, ImageFont

class ThumbnailComposer:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_thumbnail(self, bg_image_path: str, text: str, badge_text: str, accent_color: tuple) -> str:
        img = Image.open(bg_image_path).convert("RGBA").resize((1280, 720))
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        for y in range(360, 720):
            alpha = int(210 * ((y - 360) / 360))
            draw_ov.line([(0, y), (1280, y)], fill=(0, 0, 0, alpha))
        
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 300, 100], fill=accent_color)
        draw.text((65, 62), badge_text, fill=(255, 255, 255))
        draw.text((50, 550), text, fill=(255, 255, 255))
        
        out_path = os.path.join(self.output_dir, "thumbnail.png")
        img.convert("RGB").save(out_path)
        return out_path