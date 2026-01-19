# Path: src/cabin_app/services/stt/google.py
import logging
import io
import wave
from cabin_app.config import get_settings
from ..base import Transcriber

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from google.cloud import speech
    HAS_GOOGLE_SPEECH = True
except ImportError:
    HAS_GOOGLE_SPEECH = False

class GoogleTranscriber(Transcriber):
    def __init__(self, buffer_duration: float = 3.0):
        if not HAS_GOOGLE_SPEECH:
            raise ImportError("Please install google-cloud-speech: pip install google-cloud-speech")
        
        # Google Client tự động tìm Credentials từ biến môi trường GOOGLE_APPLICATION_CREDENTIALS
        self.client = speech.SpeechClient()
        
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=settings.RATE,
            language_code="en-US",
            model="latest_long" # Model tối ưu cho video/audio dài
        )
        
        self.buffer = bytearray()
        self.buffer_threshold = int(settings.RATE * settings.CHANNELS * 2 * buffer_duration)
        logger.info(f"Initialized GoogleTranscriber with {buffer_duration}s buffer")

    async def process_audio(self, audio_chunk: bytes) -> str:
        self.buffer.extend(audio_chunk)
        if len(self.buffer) >= self.buffer_threshold:
            audio_data = bytes(self.buffer)
            self.buffer = bytearray()
            # Google Speech Sync API là blocking, nên tốt nhất chạy trong executor nếu blocking lâu.
            # Với audio ngắn < 10s, nó khá nhanh.
            return self._transcribe(audio_data)
        return ""

    def _transcribe(self, audio_data: bytes) -> str:
        try:
            # Google Speech nhận raw bytes trực tiếp không cần WAV header
            # nhưng cần config đúng encoding.
            audio = speech.RecognitionAudio(content=audio_data)
            
            response = self.client.recognize(config=self.config, audio=audio)
            
            # Ghép kết quả
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript + " "
            
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"Google STT Error: {e}")
            return ""
