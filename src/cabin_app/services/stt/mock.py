# Path: src/cabin_app/services/stt/mock.py
from ..base import Transcriber

class MockTranscriber(Transcriber):
    def __init__(self, buffer_duration: float = 5.0, **kwargs) -> None:
        super().__init__(buffer_duration, **kwargs)
        self.counter = 0

    async def _transcribe(self, audio_data: bytes) -> str:
        self.counter += 1
        return f"This is a simulated sentence number {self.counter} triggered by smart VAD."