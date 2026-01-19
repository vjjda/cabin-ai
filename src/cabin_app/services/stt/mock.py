# Path: src/cabin_app/services/stt/mock.py
from ..base import Transcriber

class MockTranscriber(Transcriber):
    def __init__(self, buffer_duration: float = 3.0) -> None:
        self.counter = 0

    async def process_audio(self, audio_chunk: bytes) -> str:
        self.counter += 1
        if self.counter % 50 == 0: 
            return "I am testing the latency of the system."
        return ""
