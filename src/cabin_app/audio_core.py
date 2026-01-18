# Path: src/cabin_app/audio_core.py
import pyaudio
import logging
from typing import Generator, Optional, List, Dict
from cabin_app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class AudioStreamer:
    """
    Class chịu trách nhiệm duy nhất: Đọc dữ liệu từ Microphone
    và yield ra các chunk bytes.
    """
    def __init__(self) -> None:
        self.p = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None

    def get_input_devices(self) -> List[Dict]:
        """
        Liệt kê danh sách Microphone khả dụng trên hệ thống.
        """
        devices = []
        try:
            info = self.p.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            
            # Duyệt qua các device để tìm Microphone (input channels > 0)
            for i in range(0, numdevices):
                device_info = self.p.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxInputChannels') > 0:
                    devices.append({
                        "id": i,
                        "name": device_info.get('name'),
                        "channels": device_info.get('maxInputChannels')
                    })
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
        
        return devices

    def start_stream(self, device_index: Optional[int] = None) -> Generator[bytes, None, None]:
        """
        Mở mic và trả về generator chứa raw bytes.
        :param device_index: ID của microphone muốn dùng (None = Mặc định hệ thống)
        """
        try:
            # Ghi log thiết bị đang mở
            if device_index is not None:
                logger.info(f"🎤 Opening Microphone ID: {device_index}...")
            else:
                logger.info("🎤 Opening Default System Microphone...")

            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=settings.CHANNELS,
                rate=settings.RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=settings.CHUNK_SIZE
            )
            
            logger.info("🎤 Stream started successfully.")
            
            while True:
                if self.stream.is_active():
                    data = self.stream.read(settings.CHUNK_SIZE, exception_on_overflow=False)
                    yield data
                else:
                    break
        except Exception as e:
            logger.error(f"Audio Error: {e}")
            raise e
        finally:
            self.stop_stream()

    def stop_stream(self) -> None:
        """Đóng stream an toàn"""
        if self.stream:
            if self.stream.is_active():
                self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # Lưu ý: Thông thường ta nên terminate PyAudio, 
        # nhưng vì class này được khởi tạo liên tục trong request, 
        # ta terminate luôn để tránh leak resource.
        self.p.terminate()
        logger.info("Microphone stream closed.")