# Path: src/cabin_app/services.py
import abc
import asyncio
from typing import Dict

class Transcriber(abc.ABC):
    @abc.abstractmethod
    async def process_audio(self, audio_chunk: bytes) -> str:
        pass

class Translator(abc.ABC):
    @abc.abstractmethod
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        pass

# --- MOCK IMPLEMENTATION ---
class MockTranscriber(Transcriber):
    def __init__(self) -> None:
        self.counter = 0

    async def process_audio(self, audio_chunk: bytes) -> str:
        self.counter += 1
        if self.counter % 20 == 0:
            return "This is a streaming test from the new src layout."
        return ""

class MockTranslator(Translator):
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        await asyncio.sleep(0.5)
        return f"[Dịch]: Đây là bài test streaming từ cấu trúc src mới."