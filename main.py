# Path: main.py
import asyncio
import logging
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from audio_core import AudioStreamer
from services import MockTranscriber, MockTranslator

# Cấu hình Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CabinServer")

app = FastAPI()
settings = get_settings()

# Glossary mẫu (Trong thực tế sẽ load từ Database hoặc File)
GLOSSARY = {
    "latency": "độ trễ",
    "streaming": "phát luồng",
    "LLM": "Mô hình ngôn ngữ lớn"
}

# Khởi tạo Services (Dependency Injection)
# Khi có API Key, hãy thay MockTranscriber() bằng DeepgramTranscriber()
transcriber = MockTranscriber()
translator = MockTranslator()

@app.get("/")
async def get():
    # Đọc file HTML thủ công để đơn giản hóa demo (thay vì template engine phức tạp)
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws/cabin")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to Cabin UI")
    
    audio_streamer = AudioStreamer()
    audio_generator = audio_streamer.start_stream()

    try:
        # Chạy vòng lặp vô tận để xử lý audio
        # Lưu ý: Đây là ví dụ đơn giản (blocking). 
        # Thực tế cần chạy audio stream trong Thread riêng hoặc dùng async library cho audio.
        
        loop = asyncio.get_event_loop()
        
        # Để demo chạy mượt trong 1 thread event loop, ta sẽ giả lập stream loop
        # Trong production: AudioStreamer nên push vào Queue, và Consumer loop sẽ đọc Queue này.
        for chunk in audio_generator:
            # 1. Kiểm tra xem client còn kết nối không
            try:
                # Ping nhẹ hoặc chờ message control (nếu cần)
                pass 
            except Exception:
                break

            # 2. Transcribe (STT)
            # Vì pyaudio là blocking, ta wrap vào run_in_executor nếu xử lý nặng
            english_text = await transcriber.process_audio(chunk)

            if english_text:
                # Gửi bản gốc cho UI ngay lập tức
                await websocket.send_json({
                    "type": "transcript",
                    "text": english_text
                })

                # 3. Translate (MT)
                vietnamese_text = await translator.translate(english_text, GLOSSARY)
                
                # Gửi bản dịch
                await websocket.send_json({
                    "type": "translation",
                    "text": vietnamese_text
                })
            
            # Yield control lại cho event loop để websocket không bị đơ
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        audio_streamer.stop_stream()