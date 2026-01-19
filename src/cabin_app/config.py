# Path: src/cabin_app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal, List, Dict

class Settings(BaseSettings):
    APP_NAME: str = "Cabin AI Assistant"
    HOST: str = "0.0.0.0"
    PORT: int = 1309
    
    # Audio Settings
    CHUNK_SIZE: int = 1024
    FORMAT: int = 8
    CHANNELS: int = 1
    RATE: int = 16000

    # API Keys
    DEEPGRAM_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = "" 
    GOOGLE_PROJECT_ID: str = ""

    # --- MODEL CONFIGURATION ---
    # Default Selections
    TRANSLATION_PROVIDER: str = "groq"
    STT_PROVIDER: str = "groq"

    # Specific Model IDs (Internal)
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    OPENAI_MODEL: str = "gpt-4o-mini"
    GOOGLE_MODEL: str = "gemini-1.5-flash-001" # Fix 404: Use specific version
    
    GROQ_STT_MODEL: str = "whisper-large-v3-turbo"
    DEEPGRAM_MODEL: str = "nova-2"

    # --- UI REGISTRY (Data-Driven Frontend) ---
    # Danh sách này sẽ được gửi xuống Frontend để tạo Dropdown
    AI_OPTIONS: List[Dict[str, str]] = [
        {"id": "groq", "name": "⚡ Groq (Llama 3.1)"},
        {"id": "openai", "name": "🧠 OpenAI (GPT-4o)"},
        {"id": "google", "name": "✨ Google Gemini 1.5"},
        {"id": "mock", "name": "🧪 Mock Test"},
    ]

    STT_OPTIONS: List[Dict[str, str]] = [
        {"id": "groq", "name": "⚡ Groq Whisper"},
        {"id": "deepgram", "name": "🌊 Deepgram Nova-2"},
        {"id": "google", "name": "☁️ Google Cloud STT"},
        {"id": "mock", "name": "🧪 Mock Test"},
    ]

    # Buffer Settings (Seconds)
    BUFFER_DEFAULT: float = 3.0
    BUFFER_MIN: float = 1.0
    BUFFER_MAX: float = 10.0
    BUFFER_STEP: float = 0.5
    
    # UI UX
    UI_SCROLL_PADDING: int = 30 

    class Config:
        from pathlib import Path
        _BASE_DIR = Path(__file__).resolve().parent
        _ROOT_DIR = _BASE_DIR.parent.parent
        env_file = str(_ROOT_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
