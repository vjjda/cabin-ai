# Path: src/cabin_app/services/translation/openai.py
import logging
from typing import Dict
from openai import AsyncOpenAI
from cabin_app.config import get_settings
from .llm import LLMTranslator

logger = logging.getLogger(__name__)
settings = get_settings()

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
