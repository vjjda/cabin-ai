# Path: src/cabin_app/main.py
import asyncio
import logging
import json
from pathlib import Path
from typing import Optional, Dict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from cabin_app.config import get_settings
from cabin_app.audio_core import AudioStreamer
# Import các class mới
from cabin_app.services import (
    MockTranscriber, 
    MockTranslator, 
    GroqTranslator, 
    OpenAITranslator,
    Translator
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CabinServer")

app = FastAPI()
settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
TEMPLATE_PATH = TEMPLATE_DIR / "index.html"
STATIC_DIR = BASE_DIR / "static"
GLOSSARY_PATH = BASE_DIR / "glossary.json"

# --- HELPER: Load Glossary ---
def load_glossary() -> Dict[str, str]:
    if GLOSSARY_PATH.exists():
        try:
            with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"📚 Loaded Glossary with {len(data)} terms.")
                return data
        except Exception as e:
            logger.error(f"Failed to load glossary: {e}")
            return {}
    return {}

# --- HELPER: Factory Pattern cho Translator ---
def get_translator() -> Translator:
    provider = settings.TRANSLATION_PROVIDER.lower()
    logger.info(f"🚀 Initializing Translation Provider: {provider.upper()}")
    
    if provider == "groq":
        return GroqTranslator()
    elif provider == "openai":
        return OpenAITranslator()
    else:
        return MockTranslator()

# Khởi tạo Services
# Lưu ý: Transcriber hiện vẫn là Mock, bạn sẽ thay thế bằng Deepgram sau.
transcriber = MockTranscriber()
translator = get_translator()
global_glossary = load_glossary()

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def get():
    if not TEMPLATE_PATH.exists():
        return HTMLResponse(content="<h1>Error: Template not found</h1>", status_code=404)
    
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    # --- TEMPLATE INJECTION ---
    # Thay thế placeholder bằng giá trị từ config
    # UI_SCROLL_PADDING mặc định là 40, sẽ thành "40"
    html_content = html_content.replace(
        "{{UI_SCROLL_PADDING}}", 
        str(settings.UI_SCROLL_PADDING)
    )
        
    return HTMLResponse(content=html_content)

@app.get("/api/devices")
async def get_devices():
    temp_streamer = AudioStreamer()
    devices = temp_streamer.get_input_devices()
    temp_streamer.stop_stream()
    return JSONResponse(content=devices)

@app.websocket("/ws/cabin")
async def websocket_endpoint(
    websocket: WebSocket, 
    device_id: Optional[int] = Query(None)
):
    await websocket.accept()
    logger.info(f"Client connected. Device ID: {device_id}")
    
    audio_streamer = AudioStreamer()
    
    try:
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

            # 1. Speech to Text
            english_text = await transcriber.process_audio(chunk)

            if english_text:
                await websocket.send_json({"type": "transcript", "text": english_text})
                
                # 2. Text to Text (Translation) with Glossary
                # Gọi hàm translate thật (Groq/OpenAI)
                vietnamese_text = await translator.translate(english_text, global_glossary)
                
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