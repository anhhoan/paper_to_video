# 🎬 Automatic News & Story Video Generator

> Công cụ tự động chuyển đổi bài viết từ URL (Tin tức thời sự, Kể chuyện, Kỳ án/Vụ án) thành Video truyền thanh chuyên nghiệp với giọng đọc AI mượt mà và ảnh nền Thumbnail.

---

## 📋 Mục lục
1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Hướng dẫn cài đặt chi tiết](#2-hướng-dẫn-cài-đặt-chi-tiết)
3. [Cấu hình API Key](#3-cấu-hình-api-key)
4. [Hướng dẫn thực thi (Cách chạy app)](#4-hướng-dẫn-thực-thi-cách-chạy-app)
5. [Hướng dẫn Push code lên GitHub](#5-hướng-dẫn-push-code-lên-github)
6. [Xử lý sự cố khi cài đặt](#6-xử-lý-sự-cố-khi-cài-đặt)

---

## 1. Yêu cầu hệ thống

Trước khi cài đặt, đảm bảo máy tính của bạn đã đáp ứng các công cụ tiền đề sau:

- **Python:** Phiên bản **3.10 trở lên** (Khuyên dùng Python 3.10 hoặc 3.11).
  - *Kiểm tra:* `python --version` hoặc `python3 --version`
- **Git:** Đã cài đặt trên máy.
- **FFmpeg:** Bắt buộc cho việc xử lý âm thanh/video với MoviePy.
  - **Windows:** Tải bản build từ [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/), giải nén vào `C:\ffmpeg` và thêm `C:\ffmpeg\bin` vào **System PATH**.
  - **macOS:** `brew install ffmpeg`
  - **Linux (Ubuntu/Debian):** `sudo apt update && sudo apt install -y ffmpeg`
  - *Kiểm tra:* Chạy `ffmpeg -version` trên Terminal/CMD.

---

## 2. Hướng dẫn cài đặt chi tiết

Thực hiện lần lượt các bước sau trong Terminal / PowerShell:

### Bước 2.1: Clone dự án hoặc truy cập thư mục nguồn
```bash
git clone [https://github.com/username/paper-to-video.git](https://github.com/username/paper-to-video.git)

### Bước 2.2: Tạo Môi trường ảo (Virtual Environment)
Việc dùng môi trường ảo giúp tránh xung đột các phiên bản thư viện Python trên máy.

Trên Windows (PowerShell):

PowerShell
python -m venv .venv
.\.venv\Scripts\activate
Trên Windows (Command Prompt - CMD):

DOS
python -m venv .venv
.venv\Scripts\activate.bat
Trên macOS / Linux:

Bash
python3 -m venv .venv
source .venv/bin/activate
(Khi kích hoạt thành công, bạn sẽ thấy ký hiệu (.venv) xuất hiện ở đầu dòng lệnh).

### 2.3: Nâng cấp Pip & Cài đặt các thư viện từ requirements.txt
Chạy câu lệnh sau để tự động tải và cài đặt toàn bộ các gói phụ thuộc:

Bash
python -m pip install --upgrade pip
pip install -r requirements.txt
3. Cấu hình API Key
Dự án sử dụng Google Gemini API để biên tập kịch bản.

Lấy Gemini API Key miễn phí tại Google AI Studio.

Tạo file tên .env tại thư mục gốc của dự án (D:\Paper to Video\.env).

Dán đoạn mã sau vào file .env:

Đoạn mã
GEMINI_API_KEY=AIzaSyYourActualGeminiApiKeyHere
4. Hướng dẫn thực thi (Cách chạy app)
Cách 1: Chạy qua Giao diện Web (Streamlit UI) - Khuyên dùng
Mở Terminal (đã kích hoạt .venv) và chạy lệnh:

Bash
streamlit run ui/app.py
Hệ thống sẽ tự động mở giao diện trình duyệt tại địa chỉ: http://localhost:8501

Thao tác:

Dán đường dẫn URL bài viết (Báo chí, vụ án, blog).

Tải file Ảnh Thumbnail làm hình nền video.

Chọn Giọng đọc (vi-VN-NamMinhNeural hoặc vi-VN-HoaiMyNeural).

Nhấn "Bắt đầu tạo Video" và xem/tải kết quả trực tiếp trên trang.