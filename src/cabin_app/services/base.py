# Path: src/cabin_app/services/base.py
import abc
import logging
import struct
import math
from typing import Dict
from cabin_app.config import get_settings
from cabin_app.hallucinations import HALLUCINATION_PHRASES, HALLUCINATION_PREFIXES

settings = get_settings()
logger = logging.getLogger(__name__)

# Thay thế audioop.rms (đã bị xóa trong Python 3.13+)
def calculate_rms(audio_chunk: bytes) -> int:
    """Tính Root Mean Square (RMS) amplitude cho 16-bit PCM data"""
    if not audio_chunk:
        return 0
        
    count = len(audio_chunk) // 2
    if count == 0:
        return 0
    
    try:
        # Unpack bytes thành list các số integer 16-bit (signed short: 'h')
        # '<' = little-endian (chuẩn của wav/pcm thông thường)
        shorts = struct.unpack(f"<{count}h", audio_chunk)
        
        sum_squares = sum(s**2 for s in shorts)
        rms = math.sqrt(sum_squares / count)
        return int(rms)
    except Exception:
        return 0

class Transcriber(abc.ABC):
    def __init__(self, buffer_duration: float = 5.0, vad_threshold: int = None, vad_silence: float = None):
        # Default fallback to settings if None
        self.vad_threshold = vad_threshold if vad_threshold is not None else settings.VAD_THRESHOLD
        self.vad_silence = vad_silence if vad_silence is not None else settings.VAD_SILENCE_DURATION
        
        # Buffer Duration đóng vai trò là Max Duration (Fallback)
        self.buffer_threshold = int(settings.RATE * settings.CHANNELS * 2 * buffer_duration)
        self.buffer = bytearray()
        
        # VAD State
        self.silence_chunks_count = 0
        chunk_duration = settings.CHUNK_SIZE / settings.RATE
        self.required_silence_chunks = int(self.vad_silence / chunk_duration)
        
        # Log init info
        logger.info(f"Initialized {self.__class__.__name__} | VAD: {settings.VAD_ENABLED} | Thr: {self.vad_threshold} | Sil: {self.vad_silence}s | MaxBuf: {buffer_duration}s")

    async def process_audio(self, audio_chunk: bytes) -> str:
        self.buffer.extend(audio_chunk)
        
        # 1. Tính RMS
        rms = calculate_rms(audio_chunk)
            
        # 2. Logic VAD (Use instance variable)
        if rms < self.vad_threshold:
            self.silence_chunks_count += 1
        else:
            self.silence_chunks_count = 0 
            
        # 3. Quyết định gửi đi hay không
        should_send = False
        reason = ""
        
        # Điều kiện 1: Phát hiện khoảng lặng đủ dài (VAD)
        if settings.VAD_ENABLED and self.silence_chunks_count >= self.required_silence_chunks:
            # Chỉ gửi nếu buffer có dữ liệu "đủ dùng"
            if len(self.buffer) > (settings.RATE * 2 * 0.5):
                should_send = True
                reason = "VAD_Pause"
        
        # Điều kiện 2: Buffer đầy (Fallback)
        if len(self.buffer) >= self.buffer_threshold:
            should_send = True
            reason = "Max_Buffer"
            
        if should_send:
            # logger.debug(f"Transcribing trigger: {reason} (Buf: {len(self.buffer)} bytes)")
            data = bytes(self.buffer)
            self.buffer = bytearray() # Clear ngay lập tức
            self.silence_chunks_count = 0
            
            raw_text = await self._transcribe(data)
            if not raw_text:
                return ""
                
            clean_text = raw_text.strip()
            
            # Filter Hallucinations (Exact Match)
            if clean_text in HALLUCINATION_PHRASES:
                return ""
                
            # Filter Subtitle Credits (Prefix Match)
            lower_text = clean_text.lower()
            for prefix in HALLUCINATION_PREFIXES:
                if lower_text.startswith(prefix):
                    return ""
                
            return clean_text
            
        return ""

    @abc.abstractmethod
    async def _transcribe(self, audio_data: bytes) -> str:
        """
        Logic gọi API cụ thể của từng Provider.
        Nhận vào cục data bytes đã được cắt gọn gàng.
        """
        pass

class Translator(abc.ABC):
    @abc.abstractmethod
    async def translate(self, text: str, glossary: Dict[str, str]) -> str:
        pass
