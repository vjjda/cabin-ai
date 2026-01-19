# Path: src/cabin_app/services/translation/llm.py
import json
from typing import Dict
from ..base import Translator
from cabin_app.prompts import SYSTEM_PROMPT_TEMPLATE

class LLMTranslator(Translator):
    def _build_system_prompt(self, glossary: Dict[str, str]) -> str:
        """
        Tạo System Prompt để inject thuật ngữ (Context Injection)
        sử dụng template từ cabin_app.prompts
        """
        glossary_text = json.dumps(glossary, ensure_ascii=False, indent=2)
        return SYSTEM_PROMPT_TEMPLATE.format(glossary_json=glossary_text)