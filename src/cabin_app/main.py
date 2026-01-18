# Path: src/cabin_app/main.py
import asyncio
import logging
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse, JSONResponse

from cabin_app.config import get_settings
from cabin_app.audio_core import AudioStreamer
from cabin_app.services import MockTranscriber, MockTranslator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CabinServer")

app = FastAPI()
settings = get_settings()

transcriber = MockTranscriber()
translator = MockTranslator()

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
TEMPLATE_PATH = TEMPLATE_DIR / "index.html"

logger.info(f"📂 Looking for template at: {TEMPLATE_PATH}")

@app.get("/")
async def get():
    if not TEMPLATE_PATH.exists():
        return HTMLResponse(content="<h1>Error: Template not found</h1>", status_code=404)
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# --- API MỚI: Lấy danh sách thiết bị ---
@app.get("/api/devices")
async def get_devices():
    """Trả về danh sách microphone để Frontend hiển thị"""
    # Khởi tạo tạm thời để lấy danh sách rồi đóng ngay
    temp_streamer = AudioStreamer()
    devices = temp_streamer.get_input_devices()
    temp_streamer.stop_stream() # Dọn dẹp
    return JSONResponse(content=devices)

# --- Update WebSocket: Nhận device_id ---
@app.websocket("/ws/cabin")
async def websocket_endpoint(
    websocket: WebSocket, 
    device_id: Optional[int] = Query(None) # Lấy param ?device_id=...
):
    await websocket.accept()
    logger.info(f"Client connected with Device ID: {device_id}")
    
    audio_streamer = AudioStreamer()
    
    try:
        # Truyền device_id vào hàm start_stream
        audio_generator = audio_streamer.start_stream(device_index=device_id)
    except Exception as e:
        logger.error(f"Failed to open Mic: {e}")
        await websocket.send_json({"type": "error", "text": f"Microphone Error: {str(e)}"})
        await websocket.close()
        return

    try:
        loop = asyncio.get_event_loop()
        for chunk in audio_generator:
            try:
                if websocket.client_state.name == "DISCONNECTED":
                    break
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
        logger.error(f"WebSocket Error: {e}")
    finally:
        audio_streamer.stop_stream()

def start():
    src_dir = BASE_DIR.parent 
    uvicorn.run(
        "cabin_app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=True,
        reload_dirs=[str(src_dir)]
    )

if __name__ == "__main__":
    start()