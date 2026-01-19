# Path: src/cabin_app/services/stt/deepgram.py
import logging
import io
import wave
from cabin_app.config import get_settings
from ..base import Transcriber

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    from deepgram import DeepgramClient, PrerecordedOptions, FileSource
    HAS_DEEPGRAM = True
except ImportError:
    HAS_DEEPGRAM = False

class DeepgramTranscriber(Transcriber):
    def __init__(self, buffer_duration: float = 3.0):
        if not HAS_DEEPGRAM:
            raise ImportError("Please install deepgram-sdk: pip install deepgram-sdk")
        
        if not settings.DEEPGRAM_API_KEY:
            logger.warning("⚠️ DEEPGRAM_API_KEY missing!")
        
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        self.model = settings.DEEPGRAM_MODEL
        
        self.buffer = bytearray()
        self.buffer_threshold = int(settings.RATE * settings.CHANNELS * 2 * buffer_duration)
        logger.info(f"Initialized DeepgramTranscriber with {buffer_duration}s buffer")

    async def process_audio(self, audio_chunk: bytes) -> str:
        self.buffer.extend(audio_chunk)
        
        if len(self.buffer) >= self.buffer_threshold:
            audio_data = bytes(self.buffer)
            self.buffer = bytearray()
            return await self._transcribe(audio_data)
        return ""

    async def _transcribe(self, audio_data: bytes) -> str:
        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(settings.CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(settings.RATE)
                wf.writeframes(audio_data)
            wav_buffer.seek(0)
            
            payload: FileSource = {"buffer": wav_buffer}
            
            options = PrerecordedOptions(
                model=self.model,
                smart_format=True,
                language="en"
            )

            response = await self.client.listen.asyncprerecorded.v("1").transcribe_file(
                payload, options
            )
            
            return response.results.channels[0].alternatives[0].transcript
            
        except Exception as e:
            logger.error(f"Deepgram STT Error: {e}")
            return ""
