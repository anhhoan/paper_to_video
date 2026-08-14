import os
import json
import re
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

class GeminiClient:
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Chưa cấu hình GEMINI_API_KEY trong file .env!")
        self.client = genai.Client(api_key=self.api_key)

    def _get_prompt_template(self, article_text: str) -> str:
        return f"""
Bạn là một Biên tập viên Video Chuyên nghiệp (BTV Tin tức thế hệ mới). Nhiệm vụ của bạn là đọc bài báo đầu vào, TỰ ĐỘNG PHÂN LOẠI thể loại và viết kịch bản audio (200 - 300 từ) vừa chuẩn xác, vừa cực kỳ thu hút trên video ngắn.

HÃY THỰC HIỆN THEO QUY TRÌNH 2 BƯỚC:

BƯỚC 1: XÁC ĐỊNH THỂ LOẠI (Category Detection)
Dựa vào nội dung bài báo, chọn 1 trong 2 nhóm:
- Nhóm A: [TIN TỨC] (Kinh tế, Thời sự, Công nghệ, Xã hội, Thể thao, Chính sách, Đời sống...).
- Nhóm B: [CÂU CHUYỆN / VỤ ÁN] (Kỳ án, Tội phạm, Tâm lý, Drama, Trải nghiệm cá nhân...).

BƯỚC 2: VIẾT KỊCH BẢN THEO CHUẨN VĂN PHONG TƯƠNG ỨNG

🔴 NẾU LÀ [TIN TỨC] (Chuẩn mực nhưng Phải Thu hút & Cuốn hút):
- Nguyên tắc cốt lõi: Tôn trọng sự thật 100%, KHÔNG thêu dệt, KHÔNG phán xét hay giật gân rẻ tiền.
- Nghệ thuật thu hút (Cách làm tin hiện đại):
  1. HOOK: Đặt ngay câu hỏi về "Tác động của tin này đến người xem là gì?" hoặc "Số liệu/Sự thật bất ngờ nhất" lên đầu. Không chào hỏi, không đọc tiêu đề báo.
  2. Văn phong: Dùng văn phong nói (Spoken language) hiện đại, câu ngắn, nhịp điệu dồn dập, tự nhiên như BTV đang trò chuyện trực tiếp.
  3. Cấu trúc 4 phần:
     - hook: Điểm tin/Sự việc quan trọng nhất + Lý do người xem cần quan tâm (1-2 câu).
     - setup: Bối cảnh ngắn gọn, thời gian, nhân vật/đơn vị liên quan.
     - core_narrative: Chi tiết diễn biến chính và các con số/thông tin đắt giá.
     - outcome_or_insight: Tình hình hiện tại, tác động hoặc bước xử lý tiếp theo.

🔴 NẾU LÀ [CÂU CHUYỆN / VỤ ÁN] (Kể chuyện & Kịch tính):
- Văn phong: Hồi hộp, giàu hình ảnh, tập trung vào chi tiết đắt giá và diễn biến cảm xúc.
- Cấu trúc 5 phần: hook (Gây tò mò) -> setup (Bối cảnh) -> core_narrative (Cao trào) -> outcome_or_insight (Kết cục) -> cta (Tương tác).

BỘ LỌC TỪ NGỮ NGUY HẠI (BẮT BUỘC ÁP DỤNG BẤT KỂ THỂ LOẠI):
Thay thế các từ nhạy cảm để tránh bị bóp tương tác:
- Giết / Sát hại -> Ra tay, tước đoạt mạng sống
- Chặt / Cắt -> Bay đầu, làm tổn thương
- Máu -> Vết đỏ, siro dâu
- Thi thể -> Người xấu số
- Tự tử -> Tự kết thúc hành trình
- Hiếp dâm / Tấn công tình dục -> Hành vi xâm phạm

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ):
BẮT BUỘC trả về JSON theo đúng cấu trúc dưới đây, không kèm bất kỳ văn bản nào bên ngoài.

{{
  "analysis": {{
    "category": "TIN TỨC hoặc CÂU CHUYỆN",
    "core_topic": "1 câu tóm tắt nội dung chính",
    "tone": "Chính xác & Cuốn hút / Hồi hộp / Trầm lắng"
  }},
  "metadata": {{
    "title": "Tiêu đề ngắn gọn, giật giật nhẹ, < 65 ký tự",
    "hashtags": ["3-5 hashtag liên quan"]
  }},
  "script": {{
    "hook": "Nội dung phần hook thu hút người xem",
    "setup": "Nội dung phần bối cảnh",
    "core_narrative": "Nội dung diễn biến chính",
    "outcome_or_insight": "Nội dung kết quả / tác động",
    "cta": "Câu hỏi ngắn nhẹ nhàng thu hút comment (nếu có)"
  }}
}}

NỘI DUNG BÀI BÁO CẦN XỬ LÝ:
{article_text}
"""

    def generate(self, article_text: str) -> dict:
        prompt = self._get_prompt_template(article_text)
        models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash']

        for model_name in models_to_try:
            try:
                print(f"--> Đang gửi prompt cho Gemini model: {model_name}...")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json" # Ép Gemini trả về JSON
                    )
                )
                
                # Clean JSON String
                raw_json = response.text.strip()
                raw_json = re.sub(r'^```json\s*', '', raw_json)
                raw_json = re.sub(r'\s*```$', '', raw_json)
                
                data = json.loads(raw_json)
                
                # Nối 5 phần kịch bản thành 1 đoạn voiceover duy nhất
                script = data.get("script", {})
                full_voiceover = f"{script.get('hook', '')} {script.get('setup', '')} {script.get('core_narrative', '')} {script.get('outcome_or_insight', '')} {script.get('cta', '')}"
                
                data["full_voiceover"] = re.sub(r'\s+', ' ', full_voiceover).strip()
                return data

            except Exception as e:
                print(f"Lỗi với model {model_name}: {e}")
                continue

        raise RuntimeError("Không thể tạo kịch bản JSON từ Gemini.")