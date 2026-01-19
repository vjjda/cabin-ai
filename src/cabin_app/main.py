# Path: src/cabin_app/main.py
import asyncio
import logging
import json
import warnings
# Suppress Pydantic V1 warnings from Deepgram SDK running on newer Python versions
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality isn't compatible")

from pathlib import Path
from typing import Optional, Dict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from cabin_app.config import get_settings
from cabin_app.audio_core import AudioStreamer
from cabin_app.model_manager import ModelManager

# --- NEW SERVICES IMPORT STRUCTURE ---
from cabin_app.services import (
    Transcriber, Translator,
    # STT
    GroqTranscriber, DeepgramTranscriber, GoogleTranscriber, MockTranscriber,
    HAS_DEEPGRAM, HAS_GOOGLE_SPEECH,
    # Translation
    GroqTranslator, OpenAITranslator, GoogleTranslator, MockTranslator,
    HAS_GOOGLE_GENAI
)

# --- CONFIG LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CabinServer")

# Suppress noisy HTTP logs from libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("google.auth").setLevel(logging.WARNING) # Suppress Google Auth logs

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
# Khởi tạo sẵn các Translator (trừ khi cần tham số động)
translators_map: Dict[str, Translator] = {
    "mock": MockTranslator(),
    "groq": GroqTranslator(),
    "openai": OpenAITranslator(),
    "google": GoogleTranslator() if HAS_GOOGLE_GENAI else MockTranslator()
}

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    if (STATIC_DIR / "favicon.svg").exists():
        return FileResponse(STATIC_DIR / "favicon.svg")
    return HTMLResponse("") # Fallback

@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
async def devtools_probe():
    return JSONResponse(content={})

@app.get("/")
async def get():
    if not TEMPLATE_PATH.exists():
        return HTMLResponse(content="Error", status_code=404)
    
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Inject Configs
    html_content = html_content.replace("{{UI_SCROLL_PADDING}}", str(settings.UI_SCROLL_PADDING))
    html_content = html_content.replace("{{TRANSLATION_PROVIDER}}", settings.TRANSLATION_PROVIDER)
    html_content = html_content.replace("{{STT_PROVIDER}}", settings.STT_PROVIDER)
    
    # Inject Buffer Configs
    html_content = html_content.replace("{{BUFFER_DEFAULT}}", str(settings.BUFFER_DEFAULT))
    html_content = html_content.replace("{{BUFFER_MIN}}", str(settings.BUFFER_MIN))
    html_content = html_content.replace("{{BUFFER_MAX}}", str(settings.BUFFER_MAX))
    html_content = html_content.replace("{{BUFFER_STEP}}", str(settings.BUFFER_STEP))
    
    # Inject VAD Configs
    html_content = html_content.replace("{{VAD_THRESHOLD}}", str(settings.VAD_THRESHOLD))
    html_content = html_content.replace("{{VAD_SILENCE}}", str(settings.VAD_SILENCE_DURATION))
    
    # Inject Options Registry
    html_content = html_content.replace("{{AI_OPTIONS}}", json.dumps(settings.AI_OPTIONS))
    html_content = html_content.replace("{{STT_OPTIONS}}", json.dumps(settings.STT_OPTIONS))
    
    return HTMLResponse(content=html_content)

@app.get("/api/devices")
async def get_devices():
    temp = AudioStreamer()
    devices = temp.get_input_devices()
    temp.stop_stream()
    return JSONResponse(content=devices)

@app.get("/api/models")
async def get_models():
    """Dynamic Model Fetching"""
    # 1. Fetch Google Models
    google_models = ModelManager.get_google_models()
    
    # 2. Merge with Default Options
    # Tạo danh sách options mới, thay thế mục 'google' tĩnh bằng danh sách động
    ai_options = []
    
    # Add Static/Default Providers first
    for opt in settings.AI_OPTIONS:
        if opt['id'] != 'google':
            ai_options.append(opt)
    
    # Add Dynamic Google Models
    # Mỗi model sẽ có id="google:gemini-..." để frontend biết provider là google
    for gm in google_models:
        ai_options.append({
            "id": f"google:{gm['id']}", # Format: provider:model_id
            "name": gm['name']
        })
        
    if not google_models:
         # Fallback if fetch fails
         ai_options.append({"id": "google", "name": "✨ Google Gemini (Default)"})

    return JSONResponse(content={"ai": ai_options, "stt": settings.STT_OPTIONS})


# --- 3. WebSocket with Dynamic Provider & Pause Logic ---
@app.websocket("/ws/cabin")
async def websocket_endpoint(
    websocket: WebSocket, 
    device_id: Optional[int] = Query(None),
    provider: str = Query("mock"), # Can be "google:gemini-2.0" or just "groq"
    stt_provider: str = Query("groq"), # STT Model
    buffer: float = Query(settings.BUFFER_DEFAULT), # Buffer Duration (seconds)
    vad_threshold: int = Query(settings.VAD_THRESHOLD),
    vad_silence: float = Query(settings.VAD_SILENCE_DURATION)
):
    await websocket.accept()
    
    # 0. Parse Provider & Model
    if ":" in provider:
        provider_type, model_id = provider.split(":", 1)
    else:
        provider_type = provider
        model_id = None

    # 1. Chọn Translator
    selected_translator: Translator
    
    if provider_type == "google":
        selected_translator = GoogleTranslator(model_name=model_id)
    elif provider_type == "openai":
        selected_translator = OpenAITranslator() # Add model support later if needed
    elif provider_type == "groq":
        selected_translator = GroqTranslator()
    else:
        selected_translator = MockTranslator()
    
    # 2. Chọn Transcriber (Dynamic instantiation per connection)
    current_transcriber: Transcriber
    stt_choice = stt_provider.lower()
    
    # VAD Params for Transcriber
    t_kwargs = {
        "buffer_duration": buffer,
        "vad_threshold": vad_threshold,
        "vad_silence": vad_silence
    }

    if stt_choice == "deepgram":
        if HAS_DEEPGRAM and settings.DEEPGRAM_API_KEY:
            try:
                current_transcriber = DeepgramTranscriber(**t_kwargs)
            except Exception as e:
                logger.error(f"Deepgram Init Error: {e}")
                current_transcriber = MockTranscriber(**t_kwargs)
        else:
            reason = "SDK missing" if not HAS_DEEPGRAM else "API Key missing"
            logger.warning(f"Deepgram request failed: {reason}. Fallback to Mock.")
            current_transcriber = MockTranscriber(**t_kwargs)
            
    elif stt_choice == "google":
        if HAS_GOOGLE_SPEECH: # Google Client tự tìm Credential
            try:
                current_transcriber = GoogleTranscriber(**t_kwargs)
            except Exception as e:
                logger.error(f"Failed to init Google STT: {e}")
                current_transcriber = MockTranscriber(**t_kwargs)
        else:
            logger.warning("Google STT request but google-cloud-speech missing. Fallback to Mock.")
            current_transcriber = MockTranscriber(**t_kwargs)

    elif stt_choice == "groq":
        if settings.GROQ_API_KEY:
            current_transcriber = GroqTranscriber(**t_kwargs)
        else:
            logger.warning("Groq STT request but Key missing. Fallback to Mock.")
            current_transcriber = MockTranscriber(**t_kwargs)
            
    else:
        current_transcriber = MockTranscriber(**t_kwargs)
    
    logger.info(f"🔗 Connected | Mic: {device_id} | STT: {stt_choice} (Buf: {buffer}s VAD: {vad_threshold}) | AI: {provider}")
    
    audio_streamer = AudioStreamer()
    
    # Pause Control Logic
    pause_event = asyncio.Event()
    # Default to PAUSED state (event not set)

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
            pass 

    command_task = asyncio.create_task(listen_for_commands())
    
    try:
        audio_generator = audio_streamer.start_stream(device_index=device_id)
        
        for chunk in audio_generator:
            if websocket.client_state.name == "DISCONNECTED":
                break

            # Kiểm tra trạng thái Pause
            if not pause_event.is_set():
                await asyncio.sleep(0.1) 
                continue

            # STT Processing
            english_text = await current_transcriber.process_audio(chunk)

            if english_text:
                await websocket.send_json({"type": "transcript", "text": english_text})
                
                # Translation
                vietnamese_text = await selected_translator.translate(english_text, global_glossary)
                
                await websocket.send_json({"type": "translation", "text": vietnamese_text})
            
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