# Path: audio_core.py
import pyaudio
import logging
from typing import Generator, Optional
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class AudioStreamer:
    """
    Class chịu trách nhiệm duy nhất: Đọc dữ liệu từ Microphone
    và yield ra các chunk bytes.
    """
    def __init__(self) -> None:
        self.p = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None

    def start_stream(self) -> Generator[bytes, None, None]:
        """Mở mic và trả về generator chứa raw bytes"""
        try:
            # paInt16 = 8. Hardcode để tránh dependency vòng, nhưng tốt nhất nên dùng pyaudio.paInt16
            self.stream = self.p.open(
                format=pyaudio.paInt16,
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