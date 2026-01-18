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
    GroqTranscriber,
    DeepgramTranscriber, # Import class mới
    MockTranslator, 
    GroqTranslator, 
    OpenAITranslator,
    Translator,
    Transcriber,
    HAS_DEEPGRAM
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

# --- 2. Initialize Translators & Transcriber ---
translators_map: Dict[str, Translator] = {
    "mock": MockTranslator(),
    "groq": GroqTranslator(),
    "openai": OpenAITranslator()
}

# Chọn Transcriber (STT) dựa trên config STT_PROVIDER
transcriber: Transcriber
stt_provider = settings.STT_PROVIDER.lower()

if stt_provider == "deepgram":
    if HAS_DEEPGRAM and settings.DEEPGRAM_API_KEY:
        transcriber = DeepgramTranscriber()
        logger.info(f"🎙️ STT Engine: Deepgram ({settings.DEEPGRAM_MODEL})")
    else:
        logger.warning("⚠️ Deepgram configured but SDK/Key missing. Falling back to Groq.")
        # Fallback to Groq
        if settings.GROQ_API_KEY:
            transcriber = GroqTranscriber()
            logger.info(f"🎙️ STT Engine: Groq Whisper ({settings.GROQ_STT_MODEL})")
        else:
            transcriber = MockTranscriber()

elif stt_provider == "groq":
    if settings.GROQ_API_KEY:
        transcriber = GroqTranscriber()
        logger.info(f"🎙️ STT Engine: Groq Whisper ({settings.GROQ_STT_MODEL})")
    else:
        logger.warning("⚠️ Groq API Key missing. Falling back to Mock.")
        transcriber = MockTranscriber()

else:
    transcriber = MockTranscriber()
    logger.info("🎙️ STT Engine: Mock")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def get():
    if not TEMPLATE_PATH.exists():
        return HTMLResponse(content="Error", status_code=404)
    
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    html_content = html_content.replace(
        "{{UI_SCROLL_PADDING}}", 
        str(settings.UI_SCROLL_PADDING)
    )
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

# --- 3. WebSocket with Dynamic Provider & Pause Logic ---
@app.websocket("/ws/cabin")
async def websocket_endpoint(
    websocket: WebSocket, 
    device_id: Optional[int] = Query(None),
    provider: str = Query("mock")
):
    await websocket.accept()
    
    selected_translator = translators_map.get(provider.lower(), translators_map["mock"])
    
    logger.info(f"🔗 Connected | Mic: {device_id} | AI: {selected_translator.__class__.__name__}")
    
    audio_streamer = AudioStreamer()
    
    # Pause Control Logic
    pause_event = asyncio.Event()
    pause_event.set() # Start in RUNNING state (not paused)

    async def listen_for_commands():
        """Task chạy nền để nhận lệnh từ Client (Pause/Resume)"""
        try:
            async for raw_msg in websocket.iter_json():
                command = raw_msg.get("command")
                if command == "pause":
                    pause_event.clear()
                    logger.info("⏸️ Paused")
                    await websocket.send_json({"type": "status", "paused": True})
                elif command == "resume":
                    pause_event.set()
                    logger.info("▶️ Resumed")
                    await websocket.send_json({"type": "status", "paused": False})
        except Exception:
            pass # Connection closed or error

    command_task = asyncio.create_task(listen_for_commands())
    
    try:
        audio_generator = audio_streamer.start_stream(device_index=device_id)
        
        for chunk in audio_generator:
            if websocket.client_state.name == "DISCONNECTED":
                break

            # Kiểm tra trạng thái Pause
            if not pause_event.is_set():
                await asyncio.sleep(0.1) # Nhường CPU khi pause
                continue

            # STT Processing
            english_text = await transcriber.process_audio(chunk)

            if english_text:
                await websocket.send_json({"type": "transcript", "text": english_text})
                
                # Translation
                vietnamese_text = await selected_translator.translate(english_text, global_glossary)
                
                await websocket.send_json({"type": "translation", "text": vietnamese_text})
            
            # Quan trọng: sleep(0) để event loop có thể chuyển sang command_task xử lý tin nhắn
            await asyncio.sleep(0)

    except WebSocketDisconnect:
        logger.info("Disconnected")
    except Exception as e:
        logger.error(f"WS Error: {e}")
    finally:
        command_task.cancel()
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