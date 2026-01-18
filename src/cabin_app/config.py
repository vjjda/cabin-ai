# Path: src/cabin_app/config.py
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Cabin AI Assistant"
    HOST: str = "0.0.0.0"
    # Thay đổi port mặc định tại đây
    PORT: int = 1309
    
    CHUNK_SIZE: int = 1024
    FORMAT: int = 8
    CHANNELS: int = 1
    RATE: int = 16000

    DEEPGRAM_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()