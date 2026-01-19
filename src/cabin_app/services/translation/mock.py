# Path: src/cabin_app/services/translation/mock.py
import asyncio
from typing import Dict
from ..base import Translator

class MockTranslator(Translator):
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        await asyncio.sleep(0.1)
        return f"[Mock]: {text}"
