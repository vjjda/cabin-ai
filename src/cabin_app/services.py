# Path: src/cabin_app/services.py
import abc
import asyncio
import json
import logging
import io
import wave
from typing import Dict, Optional, List

# Import Clients
from groq import AsyncGroq
from openai import AsyncOpenAI
from cabin_app.config import get_settings

# Optional Deepgram Import
try:
    from deepgram import (
        DeepgramClient,
        PrerecordedOptions,
        FileSource,
    )
HAS_DEEPGRAM = True
except ImportError:
    HAS_DEEPGRAM = False

logger = logging.getLogger(__name__)
settings = get_settings()

# --- Interfaces ---
class Transcriber(abc.ABC):
    @abc.abstractmethod
    async def process_audio(self, audio_chunk: bytes) -> str:
        """
        Nhận vào chunk audio (raw bytes), trả về text nếu đã nhận diện xong,
        hoặc chuỗi rỗng nếu chưa đủ dữ liệu.
        """
        pass

class Translator(abc.ABC):
    @abc.abstractmethod
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        pass

# --- Base LLM Translator ---
class LLMTranslator(Translator):
    def _build_system_prompt(self, glossary: Dict[str, str]) -> str:
        glossary_text = json.dumps(glossary, ensure_ascii=False, indent=2)
        return (
            "You are a professional simultaneous interpreter translating from English to Vietnamese. "
            "Your goal is to provide fast, accurate, and natural translations suitable for live captioning.\n"
            "STRICT RULES:\n"
            "1. Output ONLY the Vietnamese translation. Do not include original text or explanations.\n"
            "2. Keep the translation concise.\n"
            "3. Use the following Glossary for specific technical terms:\n"
            f"{glossary_text}\n"
            "4. If the input is incomplete or noise, output nothing."
        )

# --- Groq Implementation (Translator) ---
class GroqTranslator(LLMTranslator):
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.warning("⚠️ GROQ_API_KEY missing! Translation will fail.")
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        if not text.strip(): return ""
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self._build_system_prompt(glossary)},
                    {"role": "user", "content": text}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq Translate Error: {e}")
            return f"[Lỗi dịch]: {text}"

# --- OpenAI Implementation (Translator) ---
class OpenAITranslator(LLMTranslator):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("⚠️ OPENAI_API_KEY missing!")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        if not text.strip(): return ""
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self._build_system_prompt(glossary)},
                    {"role": "user", "content": text}
                ],
                model=self.model,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI Translate Error: {e}")
            return f"[Lỗi dịch]: {text}"

# --- Groq Transcriber (Real STT) ---
class GroqTranscriber(Transcriber):
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.warning("⚠️ GROQ_API_KEY missing! STT will fail.")
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_STT_MODEL # Load from Config
        
        self.buffer = bytearray()
        self.buffer_threshold = 48000 # ~1.5s (16000Hz * 2 bytes * 1.5)

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

# --- Deepgram Transcriber (Real STT) ---
class DeepgramTranscriber(Transcriber):
    def __init__(self):
        if not HAS_DEEPGRAM:
            raise ImportError("Please install deepgram-sdk: pip install deepgram-sdk")
        
        if not settings.DEEPGRAM_API_KEY:
            logger.warning("⚠️ DEEPGRAM_API_KEY missing!")
        
        self.client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        self.model = settings.DEEPGRAM_MODEL # Load from Config
        
        self.buffer = bytearray()
        self.buffer_threshold = 48000 

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


# --- Mock Implementation ---
class MockTranscriber(Transcriber):
    def __init__(self) -> None:
        self.counter = 0

    async def process_audio(self, audio_chunk: bytes) -> str:
        self.counter += 1
        if self.counter % 50 == 0: 
            return "I am testing the latency of the system."
        return ""

class MockTranslator(Translator):
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        await asyncio.sleep(0.1)
        return f"[Mock]: {text}"