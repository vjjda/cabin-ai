# Path: src/cabin_app/services/translation/google.py
import logging
from typing import Dict
from cabin_app.config import get_settings
from .llm import LLMTranslator

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    import google.generativeai as genai
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

class GoogleTranslator(LLMTranslator):
    def __init__(self):
        if not HAS_GOOGLE_GENAI:
            logger.warning("⚠️ google-generativeai package missing. Run `pip install google-generativeai`")
            return

        if not settings.GOOGLE_API_KEY:
            logger.warning("⚠️ GOOGLE_API_KEY missing!")
            return
            
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        # Sử dụng model Gemini 1.5 Flash cho tốc độ và hiệu năng cao
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        if not HAS_GOOGLE_GENAI or not settings.GOOGLE_API_KEY:
            return "[Google AI chưa cấu hình]"

        if not text.strip(): return ""
        
        try:
            prompt = f"{self._build_system_prompt(glossary)}\n\nInput Text: {text}"
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Google Gemini Error: {e}")
            return f"[Lỗi dịch]: {text}"
