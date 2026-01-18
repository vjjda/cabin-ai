# Path: src/cabin_app/services.py
import abc
import asyncio
import json
import logging
from typing import Dict, Optional

# Import Clients
from groq import AsyncGroq
from openai import AsyncOpenAI

from cabin_app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# --- Interfaces ---
class Transcriber(abc.ABC):
    @abc.abstractmethod
    async def process_audio(self, audio_chunk: bytes) -> str:
        pass

class Translator(abc.ABC):
    @abc.abstractmethod
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        pass

# --- Base LLM Translator (Chứa logic Prompting chung) ---
class LLMTranslator(Translator):
    def _build_system_prompt(self, glossary: Dict[str, str]) -> str:
        """
        Tạo System Prompt để inject thuật ngữ (Context Injection).
        """
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

# --- Groq Implementation ---
class GroqTranslator(LLMTranslator):
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.warning("⚠️ GROQ_API_KEY missing! Translation will fail.")
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        if not text.strip():
            return ""
        
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self._build_system_prompt(glossary)},
                    {"role": "user", "content": text}
                ],
                model=self.model,
                temperature=0.3, # Thấp để đảm bảo tính chính xác
                max_tokens=1024,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq Error: {e}")
            return f"[Lỗi dịch]: {text}"

# --- OpenAI Implementation ---
class OpenAITranslator(LLMTranslator):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("⚠️ OPENAI_API_KEY missing!")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        if not text.strip():
            return ""

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
            logger.error(f"OpenAI Error: {e}")
            return f"[Lỗi dịch]: {text}"

# --- Mock Implementation (Fallback) ---
class MockTranscriber(Transcriber):
    def __init__(self) -> None:
        self.counter = 0

    async def process_audio(self, audio_chunk: bytes) -> str:
        self.counter += 1
        if self.counter % 30 == 0:
            return "I am testing the latency of the Groq API with specific technical terms."
        return ""

class MockTranslator(Translator):
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        await asyncio.sleep(0.5)
        return f"[Mock Dịch]: Tôi đang kiểm tra độ trễ (latency) của Groq API..."