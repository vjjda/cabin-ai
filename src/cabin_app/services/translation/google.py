# Path: src/cabin_app/services/translation/google.py
import logging
from typing import Dict
from cabin_app.config import get_settings
from .llm import LLMTranslator

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    # Thử import thư viện mới google-genai
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    # Fallback hoặc thông báo lỗi nếu chưa cài
    HAS_GOOGLE_GENAI = False

class GoogleTranslator(LLMTranslator):
    def __init__(self):
        if not HAS_GOOGLE_GENAI:
            logger.warning("⚠️ google-genai package missing. Run `pip install google-genai`")
            return

        if not settings.GOOGLE_API_KEY:
            logger.warning("⚠️ GOOGLE_API_KEY missing!")
            return
            
        # Khởi tạo Client theo chuẩn mới của google-genai
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model_name = settings.GOOGLE_MODEL

    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        if not HAS_GOOGLE_GENAI or not settings.GOOGLE_API_KEY:
            return "[Google AI chưa cấu hình]"

        if not text.strip(): return ""
        
        try:
            # Xây dựng prompt
            system_instruction = self._build_system_prompt(glossary)
            
            # Gọi API (Async)
            # Thư viện google-genai mới dùng models.generate_content
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3
                )
            )
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Google Gemini Error: {e}")
            return f"[Lỗi dịch]: {text}"