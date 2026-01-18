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

# --- 1. Load Resources ---
def load_glossary() -> Dict[str, str]:
    if GLOSSARY_PATH.exists():
        try:
            with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

global_glossary = load_glossary()

# --- 2. Initialize Translators Map ---
# Khởi tạo sẵn các translator để switch nhanh
translators_map: Dict[str, Translator] = {
    "mock": MockTranslator(),
    "groq": GroqTranslator(),
    "openai": OpenAITranslator()
}
transcriber = MockTranscriber()

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def get():
    if not TEMPLATE_PATH.exists():
        return HTMLResponse(content="Error", status_code=404)
    
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Inject giá trị mặc định vào HTML để JS đọc
    html_content = html_content.replace(
        "{{UI_SCROLL_PADDING}}", 
        str(settings.UI_SCROLL_PADDING)
    )
    # Inject provider mặc định
    html_content = html_content.replace(
        "{{TRANSLATION_PROVIDER}}", 
        settings.TRANSLATION_PROVIDER
    )
    
    return HTMLResponse(content=html_content)

@app.get("/api/devices")
async def get_devices():
    temp = AudioStreamer()
    devices = temp.get_input_devices()
    temp.stop_stream()
    return JSONResponse(content=devices)

# --- 3. WebSocket with Dynamic Provider ---
@app.websocket("/ws/cabin")
async def websocket_endpoint(
    websocket: WebSocket, 
    device_id: Optional[int] = Query(None),
    provider: str = Query("mock") # Nhận tham số provider từ Client
):
    await websocket.accept()
    
    # Chọn translator dựa trên request của user
    # Nếu provider không hợp lệ, fallback về Mock
    selected_translator = translators_map.get(provider.lower(), translators_map["mock"])
    
    logger.info(f"🔗 Connected | Mic: {device_id} | AI: {selected_translator.__class__.__name__}")
    
    audio_streamer = AudioStreamer()
    
    try:
        audio_generator = audio_streamer.start_stream(device_index=device_id)
    except Exception as e:
        logger.error(f"Mic Error: {e}")
        await websocket.close()
        return

    try:
        for chunk in audio_generator:
            if websocket.client_state.name == "DISCONNECTED":
                break

            # STT
            english_text = await transcriber.process_audio(chunk)

            if english_text:
                await websocket.send_json({"type": "transcript", "text": english_text})
                
                # Translation (Dùng translator đã chọn)
                vietnamese_text = await selected_translator.translate(english_text, global_glossary)
                
                await websocket.send_json({"type": "translation", "text": vietnamese_text})
            
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        logger.info("Disconnected")
    except Exception as e:
        logger.error(f"WS Error: {e}")
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