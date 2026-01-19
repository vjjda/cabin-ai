# Path: src/cabin_app/services/base.py
import abc
from typing import Dict

class Transcriber(abc.ABC):
    @abc.abstractmethod
    async def process_audio(self, audio_chunk: bytes) -> str:
        """
        Nhận vào chunk audio (raw bytes), trả về text nếu đã nhận diện xong,
        hoặc chuỗi rỗng nếu chưa đủ dữ liệu.
        """
        pass

class Translator(abc.ABC):
    @abc.abstractmethod
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        pass
