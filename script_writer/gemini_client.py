import os
from google import genai
from config import GEMINI_API_KEY

class GeminiClient:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Chưa cấu hình GEMINI_API_KEY trong file .env!")
            
        # Khởi tạo Client chuẩn theo SDK google-genai
        self.client = genai.Client(api_key=self.api_key)

    def _build_prompt(self, article_text: str, content_type: str = "news") -> str:
        if content_type == "story":
            return f"""
Bạn là một người kể chuyện truyền cảm chuyên về các câu chuyện hấp dẫn, vụ án và kỳ án. 
Hãy chuyển thể bài viết/hồ sơ dưới đây thành một kịch bản thoại đọc video (Voiceover) đầy kịch tính, lôi cuốn.

Yêu cầu biên tập:
1. Phong cách kể chuyện:
   - Dùng văn phong nói, mở đầu lôi cuốn (Hook) kéo người nghe vào bối cảnh.
   - Diễn đạt tình tiết logic, xây dựng cao trào (nếu là vụ án/kỳ án) và chốt lại bằng kết thúc lắng đọng.
   - Nhịp điệu câu từ linh hoạt, truyền cảm, tự nhiên như lời kể trực tiếp.
2. Định dạng văn bản:
   - Viết thành các đoạn văn thuần túy nối tiếp nhau, liền mạch.
   - Tuyệt đối KHÔNG dùng ký tự định dạng (**, #, *), KHÔNG gạch đầu dòng, KHÔNG ghi chú kịch bản ([Âm nhạc], [Cảnh 1], [Tiếng động]).
   - Chuyển các con số hoặc từ viết tắt phức tạp thành chữ đọc được.

Nội dung gốc:
{article_text}
"""
        else: # Tin tức
            return f"""
Bạn là một Biên tập viên Thời sự chuyên nghiệp. Hãy chuyển hóa bài viết dưới đây thành một bản tin truyền thanh mượt mà để đọc voiceover video.

Yêu cầu biên tập:
1. Cấu trúc 3 phần: Mở đầu gây chú ý -> Thân bài tóm tắt ý chính liền mạch -> Kết thúc chốt vấn đề.
2. Dùng văn phong nói tự nhiên, nhịp điệu mượt mà.
3. Tuyệt đối KHÔNG dùng ký tự định dạng (**, #, *), KHÔNG gạch đầu dòng, KHÔNG ghi chú kịch bản ([Cảnh 1], [Âm nhạc]).
4. Viết thành đoạn văn thuần thúy, liền mạch.

Nội dung gốc:
{article_text}
"""

    def generate(self, article_text: str, content_type: str = "news") -> str:
        prompt = self._build_prompt(article_text, content_type)
        
        # Danh sách model ưu tiên
        models_to_try = [
            'gemini-3.6-flash',
            'gemini-2.5-flash',
            'gemini-2.0-flash'
        ]

        last_error = None
        for model_name in models_to_try:
            try:
                print(f"--> Đang gọi Gemini API với model: {model_name}...")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response.text:
                    print(f"✅ Biên tập văn bản thành công bằng model: {model_name}")
                    return response.text
            except Exception as e:
                last_error = e
                print(f"Model {model_name} gặp lỗi: {e}. Đang chuyển sang model dự phòng...")
                continue

        raise RuntimeError(f"Lỗi khi gọi Gemini API với toàn bộ các models fallback: {last_error}")

    # Các hàm Alias dự phòng tương thích ngược với code cũ
    def generate_script(self, article_text: str, content_type: str = "news") -> str:
        return self.generate(article_text, content_type)

    def generate_script_from_text(self, article_text: str) -> str:
        return self.generate(article_text)