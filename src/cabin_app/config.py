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

    # AI Translation Settings
    # Lựa chọn: "groq", "openai", "mock"
    TRANSLATION_PROVIDER: Literal["groq", "openai", "mock"] = "mock"
    
    # Models
    # Groq: "llama3-8b-8192" (nhanh nhất), "mixtral-8x7b-32768" (thông minh hơn)
    GROQ_MODEL: str = "llama3-8b-8192"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # API Keys (Load từ .env)
    DEEPGRAM_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()