# 🔑 Hướng dẫn lấy API Key (Chi tiết từng bước)

Tài liệu này dành cho các bạn biên dịch viên hoặc người dùng không chuyên về kỹ thuật. Để sử dụng **Cabin AI**, bạn cần có "chìa khóa" (API Key) từ các nhà cung cấp dịch vụ.

Hãy tưởng tượng **Cabin AI** là cái xe, còn **API Key** là xăng. Bạn cần đổ xăng thì xe mới chạy được.

Dưới đây là hướng dẫn lấy 3 loại Key quan trọng nhất. Bạn chỉ cần làm 1 lần duy nhất.

---

## 1. Google Gemini (Nên làm đầu tiên - Dễ nhất)
Google Gemini vừa nghe hiểu tốt, vừa dịch thuật rất hay.

1.  **Bước 1:** Truy cập vào trang: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2.  **Bước 2:** Đăng nhập bằng tài khoản **Gmail** của bạn.
3.  **Bước 3:** Bấm vào nút màu xanh **Create API key** (Tạo khóa API).
4.  **Bước 4:** Một bảng hiện ra, chọn **"Create API key in new project"**.
5.  **Bước 5:** Chờ vài giây, một đoạn mã dài bắt đầu bằng `AIza...` sẽ hiện ra.
6.  **Bước 6:** Bấm nút **Copy** bên cạnh đoạn mã đó và lưu lại vào file `.env` (mục `GOOGLE_API_KEY`).

---

## 2. Groq (Quan trọng - Giúp app chạy siêu nhanh)
Groq giúp AI trả lời "nhanh như chớp". Hiện tại nó đang miễn phí.

1.  **Bước 1:** Truy cập: [https://console.groq.com/keys](https://console.groq.com/keys)
2.  **Bước 2:** Bấm **Login** và chọn đăng nhập bằng Google (Gmail) cho nhanh.
3.  **Bước 3:** Nhìn bên menu trái, chọn mục **API Keys**.
4.  **Bước 4:** Bấm nút **Create API Key**.
5.  **Bước 5:** Một hộp thoại hiện ra, bạn có thể đặt tên (ví dụ: `cabin-ai`) hoặc để trống rồi bấm **Submit**.
6.  **Bước 6:** **QUAN TRỌNG:** Một đoạn mã bắt đầu bằng `gsk_...` hiện ra. Bạn phải **Copy ngay lập tức** vì tắt bảng này đi là không xem lại được nữa.
7.  **Bước 7:** Dán vào file `.env` (mục `GROQ_API_KEY`).

---

## 3. Deepgram (Bắt buộc để nghe giọng nói)
Đây là "đôi tai" của ứng dụng. Deepgram nghe giọng nói cực chuẩn.

1.  **Bước 1:** Truy cập: [https://console.deepgram.com/signup](https://console.deepgram.com/signup)
2.  **Bước 2:** Đăng ký tài khoản (Sign up with Google).
3.  **Bước 3:** Sau khi vào trang quản lý (Dashboard), nhìn menu bên trái, tìm mục **API Keys**.
4.  **Bước 4:** Bấm **Create a New API Key**.
5.  **Bước 5:**
    - Phần "Friendly Name": Điền `cabin-ai`.
    - Phần "Role": Để nguyên là `Member`.
    - Bấm **Create Key**.
6.  **Bước 6:** Copy đoạn mã hiện ra và dán vào file `.env` (mục `DEEPGRAM_API_KEY`).

---

## 4. OpenAI (Tùy chọn)
Nếu bạn có tài khoản ChatGPT Plus hoặc muốn dùng GPT-4o. Lưu ý là OpenAI tính phí và cần thẻ Visa.

1.  Truy cập: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2.  Đăng nhập và bấm **Create new secret key**.
3.  Copy và dán vào mục `OPENAI_API_KEY`.

---

## 📝 Tóm tắt cách điền vào file cấu hình

Sau khi có các mã trên, bạn mở file `.env` trong thư mục dự án và điền vào như sau:

```env
# Dán mã của Deepgram vào đây
DEEPGRAM_API_KEY="...mã-của-bạn..."

# Dán mã của Groq vào đây
GROQ_API_KEY="gsk_...mã-của-bạn..."

# Dán mã của Google vào đây
GOOGLE_API_KEY="AIza...mã-của-bạn..."
```

Sau khi điền xong và lưu file (`Ctrl + S` hoặc `Command + S`), bạn hãy khởi động lại ứng dụng để áp dụng "xăng" mới nhé!
