# Path: src/cabin_app/main.py
import asyncio
import logging
import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
# Dùng importlib.resources để lấy path an toàn hơn hoặc đường dẫn tương đối
from pathlib import Path

from cabin_app.config import get_settings
from cabin_app.audio_core import AudioStreamer
from cabin_app.services import MockTranscriber, MockTranslator

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CabinServer")

app = FastAPI()
settings = get_settings()

transcriber = MockTranscriber()
translator = MockTranslator()

# Xác định đường dẫn tới file template dựa trên vị trí file hiện tại
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"

@app.get("/")
async def get():
    template_path = TEMPLATE_DIR / "index.html"
    if not template_path.exists():
        return HTMLResponse(content="<h1>Error: Template not found</h1>")
        
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws/cabin")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected")
    
    audio_streamer = AudioStreamer()
    audio_generator = audio_streamer.start_stream()

    try:
        loop = asyncio.get_event_loop()
        for chunk in audio_generator:
            try:
                # Kiểm tra connection state trick (tuỳ chọn)
                pass 
            except Exception:
                break

            english_text = await transcriber.process_audio(chunk)

            if english_text:
                await websocket.send_json({"type": "transcript", "text": english_text})
                vietnamese_text = await translator.translate(english_text, {})
                await websocket.send_json({"type": "translation", "text": vietnamese_text})
            
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        audio_streamer.stop_stream()

# Hàm entry point cho script defined trong pyproject.toml
def start():
    """Entry point for command line"""
    uvicorn.run("cabin_app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

if __name__ == "__main__":
    start()