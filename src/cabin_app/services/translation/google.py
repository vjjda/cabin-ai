# Path: src/cabin_app/services/translation/google.py
import logging
import asyncio
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
    HAS_GOOGLE_GENAI = False

import time

class GoogleTranslator(LLMTranslator):
    def __init__(self, model_name: str = None):
        if not HAS_GOOGLE_GENAI:
            logger.warning("⚠️ google-genai package missing. Run `pip install google-genai`")
            return

        if not settings.GOOGLE_API_KEY:
            logger.warning("⚠️ GOOGLE_API_KEY missing!")
            return
            
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model_name = model_name or settings.GOOGLE_MODEL
        
        # Client-side Rate Limiting (Free Tier ~15 RPM -> Safe 10 RPM -> 6s interval)
        self.last_call_time = 0
        self.min_interval = 6.0 

    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        if not HAS_GOOGLE_GENAI or not settings.GOOGLE_API_KEY:
            return "[Google AI chưa cấu hình]"

        if not text.strip(): return ""
        
        # Enforce Rate Limit
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            # logger.info(f"⏳ Throttling Google API ({wait_time:.1f}s)...")
            await asyncio.sleep(wait_time)
            
        self.last_call_time = time.time() # Update timestamp BEFORE call to count wait time correctly
        
        system_instruction = self._build_system_prompt(glossary)
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
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
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = 5 * (attempt + 1) # Increase backoff: 5s, 10s...
                        logger.warning(f"⚠️ Google Rate Limit (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Google Gemini Quota Exceeded: {error_msg}")
                        return "[Lỗi Quota Google - Vui lòng đợi]"
                
                # Các lỗi khác (404, 500...)
                logger.error(f"Google Gemini Error: {e}")
                return f"[Lỗi dịch]: {text}"
        
        return ""
