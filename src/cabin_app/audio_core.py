# Path: src/cabin_app/audio_core.py
import logging
from typing import Generator, Optional

import pyaudio

# Import absolute path từ root package
from cabin_app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class AudioStreamer:
    def __init__(self) -> None:
        self.p = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None

    def start_stream(self) -> Generator[bytes, None, None]:
        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16, # Hoặc dùng settings.FORMAT
                channels=settings.CHANNELS,
                rate=settings.RATE,
                input=True,
                frames_per_buffer=settings.CHUNK_SIZE
            )
            logger.info("🎤 Microphone stream started...")
            
            while True:
                if self.stream.is_active():
                    data = self.stream.read(settings.CHUNK_SIZE, exception_on_overflow=False)
                    yield data
                else:
                    break
        except Exception as e:
            logger.error(f"Audio Error: {e}")
        finally:
            self.stop_stream()

    def stop_stream(self) -> None:
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        logger.info("Microphone stream closed.")