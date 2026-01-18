# Path: src/cabin_app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Cabin AI Assistant"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    CHUNK_SIZE: int = 1024
    # Pyaudio format thường là 8 (paInt16)
    FORMAT: int = 8
    CHANNELS: int = 1
    RATE: int = 16000

    DEEPGRAM_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        # Cho phép đọc .env ở root dự án dù code nằm trong src/
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()