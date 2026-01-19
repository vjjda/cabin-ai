# Path: src/cabin_app/services/stt/google.py
import logging
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
    def __init__(self, buffer_duration: float = 5.0, **kwargs):
        super().__init__(buffer_duration, **kwargs)
        
        if not HAS_GOOGLE_SPEECH:
            raise ImportError("Please install google-cloud-speech: pip install google-cloud-speech")
        
        self.client = speech.SpeechClient()
        
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=settings.RATE,
            language_code="en-US",
            model="latest_long" 
        )

    async def _transcribe(self, audio_data: bytes) -> str:
        try:
            audio = speech.RecognitionAudio(content=audio_data)
            response = self.client.recognize(config=self.config, audio=audio)
            
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript + " "
            
            return transcript.strip()
            
        except Exception as e:
            logger.error(f"Google STT Error: {e}")
            return ""