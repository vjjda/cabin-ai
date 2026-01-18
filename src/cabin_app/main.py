# Path: src/cabin_app/main.py
import asyncio
import logging
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pathlib import Path

# --- Import modules nội bộ ---
from cabin_app.config import get_settings
from cabin_app.audio_core import AudioStreamer
from cabin_app.services import MockTranscriber, MockTranslator

# --- Cấu hình Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CabinServer")

app = FastAPI()
settings = get_settings()

transcriber = MockTranscriber()
translator = MockTranslator()

# --- Cấu hình đường dẫn Templates ---
# Lấy đường dẫn thư mục chứa file main.py hiện tại
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
TEMPLATE_PATH = TEMPLATE_DIR / "index.html"

# In ra log để Debug vị trí file
logger.info(f"📂 Looking for template at: {TEMPLATE_PATH}")

@app.get("/")
async def get():
    if not TEMPLATE_PATH.exists():
        logger.error(f"❌ Template NOT found at: {TEMPLATE_PATH}")
        return HTMLResponse(
            content=f"<h1>Error: Template not found</h1><p>Expected path: {TEMPLATE_PATH}</p>", 
            status_code=404
        )
        
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws/cabin")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected")
    
    audio_streamer = AudioStreamer()
    # Kiểm tra mic có mở được không
    try:
        audio_generator = audio_streamer.start_stream()
    except Exception as e:
        logger.error(f"Failed to open Mic: {e}")
        await websocket.close()
        return

    try:
        loop = asyncio.get_event_loop()
        for chunk in audio_generator:
            try:
                # Kiểm tra kết nối còn sống không (trick)
                if websocket.client_state.name == "DISCONNECTED":
                    break
            except Exception:
                break

            # Process Audio
            english_text = await transcriber.process_audio(chunk)

            if english_text:
                # Gửi Transcript
                await websocket.send_json({"type": "transcript", "text": english_text})
                
                # Dịch và Gửi
                vietnamese_text = await translator.translate(english_text, {})
                await websocket.send_json({"type": "translation", "text": vietnamese_text})
            
            # Yield control (quan trọng để không chặn event loop)
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
    finally:
        audio_streamer.stop_stream()

def start():
    """Entry point for command line"""
    # reload=True chỉ hoạt động tốt nếu trỏ vào string path, không phải object app trực tiếp
    # Tuy nhiên khi chạy qua entry_point, reload đôi khi gặp vấn đề về path.
    # Để an toàn nhất khi dev, ta dùng chuỗi import string.
    uvicorn.run("cabin_app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

if __name__ == "__main__":
    start()