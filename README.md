# 🎧 Cabin AI Assistant

**Cabin AI** là trợ lý ảo thời gian thực, có khả năng chuyển đổi giọng nói thành văn bản (Speech-to-Text) và dịch thuật/xử lý ngôn ngữ tự nhiên ngay lập tức. Dự án được thiết kế theo kiến trúc Modular, cho phép dễ dàng chuyển đổi giữa các nhà cung cấp AI như Groq, OpenAI, Google Gemini và Deepgram.

---

## 🚀 Tính năng nổi bật

- **Speech-to-Text (STT):** Hỗ trợ Deepgram (siêu nhanh), Groq Whisper và Google STT.
- **AI Processing:** Tích hợp Llama 3 (qua Groq), GPT-4o (OpenAI) và Gemini 2.0 (Google).
- **Real-time:** Phản hồi độ trễ thấp nhờ WebSockets.
- **Voice Activity Detection (VAD):** Tự động phát hiện khi bạn ngừng nói để xử lý, tối ưu hóa băng thông.
- **Giao diện hiện đại:** Web UI đơn giản, trực quan với hiệu ứng sóng âm.

---

## 🛠️ Yêu cầu hệ thống

- **Hệ điều hành:** macOS (Khuyến nghị), Linux, hoặc Windows.
- **Python:** Phiên bản 3.12 trở lên.
- **Công cụ:** `make`, `brew` (trên macOS).

---

## 🔑 Hướng dẫn lấy API Key

Để ứng dụng hoạt động, bạn cần đăng ký API Key từ các nhà cung cấp (Google, Groq, Deepgram).

👉 **[XEM HƯỚNG DẪN CHI TIẾT TỪNG BƯỚC TẠI ĐÂY](docs/HUONG_DAN_API.md)**

*(Tài liệu này hướng dẫn chi tiết cách tạo tài khoản và lấy key cho người mới bắt đầu)*

---

## ⚙️ Cài đặt

### Bước 1: Clone dự án
```bash
git clone https://github.com/your-username/cabin.ai.git
cd cabin.ai
```

### Bước 2: Cài đặt thư viện hệ thống
Dự án cần `portaudio` để xử lý microphone. Sử dụng lệnh sau (trên macOS):
```bash
make system-deps
```

### Bước 3: Cài đặt môi trường Python
Lệnh sau sẽ tạo môi trường ảo `.venv` và cài đặt tất cả thư viện cần thiết:
```bash
make install
```

### Bước 4: Cấu hình Environment
1. Sao chép file mẫu:
   ```bash
   cp .env.example .env
   ```
2. Mở file `.env` và điền các API Key bạn đã lấy ở phần trên:
   ```env
   GROQ_API_KEY="gsk_..."
   DEEPGRAM_API_KEY="..."
   # ...
   ```

---

## ▶️ Chạy ứng dụng

### Chế độ phát triển (Development)
Chế độ này sẽ tự động tải lại server khi bạn sửa code:
```bash
make dev
```
Truy cập: [http://localhost:1309](http://localhost:1309)

### Chế độ sản xuất (Production)
Chạy ổn định, không reload:
```bash
make run
```

---

## 🐛 Khắc phục sự cố thường gặp

**1. Lỗi không tìm thấy `portaudio` hoặc `pyaudio` install failed:**
Hãy chắc chắn bạn đã chạy `make system-deps`. Nếu vẫn lỗi, thử chạy thủ công:
```bash
brew install portaudio
pip install pyaudio
```

**2. Lỗi Microphone trên macOS:**
Nếu ứng dụng chạy nhưng không thu âm được, hãy kiểm tra: **System Settings** -> **Privacy & Security** -> **Microphone** và cấp quyền cho **Terminal** (hoặc IDE của bạn).

**3. Lỗi WebSocket connection failed:**
Kiểm tra lại xem server backend có đang chạy không và port 1309 có bị chiếm dụng không.

---

## 👨‍💻 Dành cho lập trình viên

Dự án cung cấp sẵn bộ công cụ để đảm bảo chất lượng code:

- **Format code:** `make format` (Black, Isort)
- **Kiểm tra lỗi:** `make lint` (Flake8, MyPy)
- **Dọn dẹp:** `make clean`
