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

    # AI Settings
    TRANSLATION_PROVIDER: Literal["groq", "openai", "mock"] = "mock"
    GROQ_MODEL: str = "llama3-8b-8192"
    OPENAI_MODEL: str = "gpt-4o-mini"
    DEEPGRAM_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # --- UI UX CONFIG ---
    # Khoảng trống thừa bên dưới (tính theo % chiều cao màn hình - vh)
    # 40 nghĩa là dòng chữ mới nhất sẽ nằm ở khoảng 60% màn hình từ trên xuống.
    UI_SCROLL_PADDING: int = 40 

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()