# Path: src/cabin_app/services/translation/llm.py
import json
from typing import Dict
from ..base import Translator

class LLMTranslator(Translator):
    def _build_system_prompt(self, glossary: Dict[str, str]) -> str:
        glossary_text = json.dumps(glossary, ensure_ascii=False, indent=2)
        return (
            "You are a professional simultaneous interpreter translating from English to Vietnamese. "
            "Your goal is to provide fast, accurate, and natural translations suitable for live captioning.
"
            "STRICT RULES:
"
            "1. Output ONLY the Vietnamese translation. Do not include original text or explanations.
"
            "2. Keep the translation concise.
"
            "3. Use the following Glossary for specific technical terms:
"
            f"{glossary_text}
"
            "4. If the input is incomplete or noise, output nothing."
        )
