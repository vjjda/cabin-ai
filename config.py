# Path: config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Cabin AI Assistant"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Cấu hình Audio
    CHUNK_SIZE: int = 1024
    FORMAT: int = 8  # paInt16 tương đương 8 trong pyaudio (cần import pyaudio để lấy giá trị chính xác nếu muốn dynamic)
    CHANNELS: int = 1
    RATE: int = 16000 # 16kHz là chuẩn tốt cho STT

    # API Keys (Để trống hoặc điền vào .env)
    DEEPGRAM_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()