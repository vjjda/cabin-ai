# Path: src/cabin_app/hallucinations.py

# Danh sách các câu/từ do Whisper "ảo giác" sinh ra khi gặp khoảng lặng hoặc nhiễu.
# Hệ thống sẽ lọc bỏ nếu kết quả STT trùng khớp với các mẫu này.

# 1. So sánh chính xác (Exact Match) - Case sensitive nhưng code sẽ xử lý strip()
HALLUCINATION_PHRASES = {
    "Thank you.", "Thank you", "Thanks.", "Thanks", "thank you", "thanks",
    "You", "you", ".", "?", "!", ",",
    "Bye.", "Bye", "bye",
    "Watching", "watching",
    "Okay.", "Okay", "OK.", "OK", "Amen", "amen",
}

# 2. So sánh tiền tố (Starts With) - Case insensitive (sẽ được lowercase khi so sánh)
HALLUCINATION_PREFIXES = [
    "subtitles by", 
    "translated by", 
    "captioned by",
    "amara.org",
    "provided by",
    "copyright",
    "all rights reserved"
]
