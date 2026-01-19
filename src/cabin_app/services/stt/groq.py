# Path: src/cabin_app/services/stt/groq.py
import logging
import io
import wave
from groq import AsyncGroq
from cabin_app.config import get_settings
from ..base import Transcriber

logger = logging.getLogger(__name__)
settings = get_settings()

class GroqTranscriber(Transcriber):
    def __init__(self, buffer_duration: float = 5.0, **kwargs):
        super().__init__(buffer_duration, **kwargs)
        
        if not settings.GROQ_API_KEY:
            logger.warning("⚠️ GROQ_API_KEY missing! STT will fail.")
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_STT_MODEL 

    async def _transcribe(self, audio_data: bytes) -> str:
        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(settings.CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(settings.RATE)
                wf.writeframes(audio_data)
            
            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav" 

            transcription = await self.client.audio.transcriptions.create(
                file=wav_buffer,
                model=self.model,
                response_format="text",
                language="en"
            )
            return transcription.strip()
        except Exception as e:
            logger.error(f"Groq STT Error: {e}")
            return ""