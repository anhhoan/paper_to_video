import os
import streamlit as st
import sys
from pathlib import Path

# Thêm đường dẫn root dự án vào sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.pipeline import AutomationPipeline

st.set_page_config(page_title="Paper to Video", layout="centered")

st.title("🎬 Chuyển Bài Viết Thành Video (1 Thumbnail)")
st.write("Nhập URL bài viết và tải lên 1 bức ảnh duy nhất để làm nền cho toàn bộ video.")

# 1. Ô nhập URL
url_input = st.text_input("URL Bài viết:", placeholder="https://example.com/bai-viet")

# 2. Ô tải lên 1 bức ảnh duy nhất
uploaded_image = st.file_uploader("Tải lên 1 ảnh Thumbnail duy nhất (JPG/PNG):", type=["jpg", "jpeg", "png"])

# Hiển thị xem trước ảnh (nếu đã upload)
if uploaded_image:
    st.image(uploaded_image, caption="Ảnh nền sẽ dùng cho toàn bộ Video", use_column_width=True)

# 3. Chọn giọng đọc
voice_option = st.selectbox(
    "Chọn giọng đọc:",
    options=["vi-VN-NamMinhNeural", "vi-VN-HoaiMyNeural"],
    format_func=lambda x: "Nam Minh (Nam)" if "NamMinh" in x else "Hoài Mỹ (Nữ)"
)

# 4. Nút bấm thực thi
if st.button("🚀 Bắt đầu tạo Video", type="primary"):
    if not url_input.strip():
        st.error("Vui lòng nhập URL bài viết!")
    elif not uploaded_image:
        st.error("Vui lòng tải lên 1 bức ảnh Thumbnail!")
    else:
        try:
            with st.spinner("Hệ thống đang xử lý bài viết, tạo giọng đọc và ghép video..."):
                # Lưu ảnh người dùng upload vào thư mục tạm temp_thumbnail.png
                temp_thumb_path = "output/temp_thumbnail.png"
                os.makedirs("output", exist_ok=True)
                with open(temp_thumb_path, "wb") as f:
                    f.write(uploaded_image.getbuffer())

                # Gọi Pipeline
                pipeline = AutomationPipeline()
                output_mp4 = pipeline.run(
                    url=url_input,
                    thumbnail_path=temp_thumb_path,
                    voice=voice_option,
                    output_video_path="output/final_video.mp4"
                )

            st.success("Tạo Video thành công!")
            st.video(output_mp4)

        except Exception as e:
            st.error(f"Xảy ra lỗi trong quá trình xử lý: {e}")