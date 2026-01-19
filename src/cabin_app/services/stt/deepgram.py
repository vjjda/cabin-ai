# Path: src/cabin_app/services/stt/deepgram.py
import logging
import io
import wave
import asyncio
from cabin_app.config import get_settings
from ..base import Transcriber

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from deepgram import DeepgramClient
    HAS_DEEPGRAM = True
except ImportError as e:
    logger.error(f"Failed to import deepgram: {e}")
    HAS_DEEPGRAM = False
except Exception as e:
    logger.error(f"Unexpected error importing deepgram: {e}")
    HAS_DEEPGRAM = False

class DeepgramTranscriber(Transcriber):
    def __init__(self, buffer_duration: float = 5.0, **kwargs):
        super().__init__(buffer_duration, **kwargs)
        
        if not HAS_DEEPGRAM:
            raise ImportError("Please install deepgram-sdk: pip install deepgram-sdk")
        
        if not settings.DEEPGRAM_API_KEY:
            logger.warning("⚠️ DEEPGRAM_API_KEY missing!")
        
        try:
            self.client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
        except TypeError:
             self.client = DeepgramClient()

        self.model = settings.DEEPGRAM_MODEL

    async def _transcribe(self, audio_data: bytes) -> str:
        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(settings.CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(settings.RATE)
                wf.writeframes(audio_data)
            wav_buffer.seek(0)
            
            options = {
                "model": self.model,
                "smart_format": True,
                "language": "en"
            }

            response = await asyncio.to_thread(
                self.client.listen.v1.media.transcribe_file,
                request=wav_buffer, 
                **options
            )
            
            return response.results.channels[0].alternatives[0].transcript
            
        except Exception as e:
            logger.error(f"Deepgram STT Error: {e}")
            return ""
