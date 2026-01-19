# Path: src/cabin_app/services/translation/groq.py
import logging
from typing import Dict
from groq import AsyncGroq
from cabin_app.config import get_settings
from .llm import LLMTranslator

logger = logging.getLogger(__name__)
settings = get_settings()

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
