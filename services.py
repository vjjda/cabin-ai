# Path: services.py
import abc
import json
import asyncio
import random
from typing import Dict

# Interface chuẩn
class Transcriber(abc.ABC):
    @abc.abstractmethod
    async def process_audio(self, audio_chunk: bytes) -> str:
        """Nhận bytes, trả về text (nếu có)"""
        pass

class Translator(abc.ABC):
    @abc.abstractmethod
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        """Nhận text tiếng Anh, trả về tiếng Việt dựa trên glossary"""
        pass

# --- MOCK IMPLEMENTATION (Để chạy thử logic mà không cần API Key ngay) ---
class MockTranscriber(Transcriber):
    """Giả lập việc nghe và trả về text sau mỗi 5 chunk"""
    def __init__(self) -> None:
        self.counter = 0

    async def process_audio(self, audio_chunk: bytes) -> str:
        self.counter += 1
        # Giả lập: cứ 20 chunk (~1 giây) thì trả về một câu
        if self.counter % 20 == 0:
            return "The quick brown fox jumps over the lazy dog."
        return ""

class MockTranslator(Translator):
    """Giả lập dịch thuật"""
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        # Giả lập độ trễ mạng
        await asyncio.sleep(0.5) 
        return f"[Dịch]: Con cáo nâu nhanh nhẹn nhảy qua con chó lười. (Glossary terms: {len(glossary)})"

# --- REAL IMPLEMENTATION GUIDES (Placeholder) ---
# Bạn sẽ thay thế Mock bằng code gọi Deepgram/OpenAI ở đây.
# Ví dụ: DeepgramTranscriber sẽ dùng websockets client để gửi bytes lên server Deepgram.