# Path: src/cabin_app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal

class Settings(BaseSettings):
    APP_NAME: str = "Cabin AI Assistant"
    HOST: str = "0.0.0.0"
    PORT: int = 1309
    
    # Audio Settings
    CHUNK_SIZE: int = 1024
    FORMAT: int = 8
    CHANNELS: int = 1
    RATE: int = 16000

    # AI Settings (Default values)
    TRANSLATION_PROVIDER: Literal["groq", "openai", "mock"] = "groq"
    
    # Text Translation Models
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Speech-to-Text (STT) Configuration
    STT_PROVIDER: Literal["groq", "deepgram", "mock"] = "groq"
    GROQ_STT_MODEL: str = "whisper-large-v3-turbo"
    DEEPGRAM_MODEL: str = "nova-2"
    
    DEEPGRAM_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = "" # For Gemini
    GOOGLE_PROJECT_ID: str = "" # For Google Cloud STT
    
    # UI UX CONFIG
    # Mặc định khoảng trống bên dưới là 30% (30vh)
    UI_SCROLL_PADDING: int = 30 
    
    # Buffer Settings (Seconds)
    BUFFER_DEFAULT: float = 3.0
    BUFFER_MIN: float = 1.0
    BUFFER_MAX: float = 10.0
    BUFFER_STEP: float = 0.5

    class Config:
        # Tự động tìm .env ở root project (cách config.py 2 cấp thư mục: src/cabin_app/../../.env)
        from pathlib import Path
        _BASE_DIR = Path(__file__).resolve().parent
        _ROOT_DIR = _BASE_DIR.parent.parent
        env_file = str(_ROOT_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore" # Bỏ qua các biến thừa trong .env nếu có

@lru_cache()
def get_settings() -> Settings:
    return Settings()