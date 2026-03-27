from __future__ import annotations
import asyncio, io, json, os, re, time, uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

# ── Config ─────────────────────────────────────────────────────────────────
OLLAMA_BASE   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME    = os.getenv("MODEL_NAME",      "qwen2.5:1.5b")
MAX_TOKENS    = int(os.getenv("MAX_TOKENS",  "400"))
MAX_HISTORY   = int(os.getenv("MAX_HISTORY", "20"))
MAX_CONCURRENT = 4

# ── Concurrency semaphore ──────────────────────────────────────────────────
voice_semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# ── City knowledge base (from Assignment 2) ────────────────────────────────
class City(str, Enum):
    istanbul="istanbul"; lahore="lahore"; islamabad="islamabad"
    paris="paris"; bangkok="bangkok"; tokyo="tokyo"
    dubai="dubai"; barcelona="barcelona"; singapore="singapore"

CITY_KB = {
    "istanbul":  {"name":"Istanbul","country":"Turkey","best_season":"Apr-Jun, Sep-Oct","activities":["Hagia Sophia","Blue Mosque","Grand Bazaar","Bosphorus cruise"],"foods":["Kebab","Baklava","Simit"],"safety":"High"},
    "lahore":    {"name":"Lahore","country":"Pakistan","best_season":"Oct-Mar","activities":["Badshahi Mosque","Lahore Fort","Food Street"],"foods":["Nihari","Biryani","Seekh kebab"],"safety":"High"},
    "islamabad": {"name":"Islamabad","country":"Pakistan","best_season":"Mar-May, Sep-Nov","activities":["Faisal Mosque","Margalla Hills","Daman-e-Koh"],"foods":["BBQ","Chapli kebab"],"safety":"Very High"},
    "paris":     {"name":"Paris","country":"France","best_season":"Apr-Jun, Sep-Oct","activities":["Eiffel Tower","Louvre","Montmartre"],"foods":["Croissants","Escargots","Macarons"],"safety":"High"},
    "bangkok":   {"name":"Bangkok","country":"Thailand","best_season":"Nov-Feb","activities":["Grand Palace","Wat Pho","Floating markets"],"foods":["Pad Thai","Green curry","Tom yum"],"safety":"High"},
    "tokyo":     {"name":"Tokyo","country":"Japan","best_season":"Mar-May, Sep-Nov","activities":["Senso-ji","Shibuya Crossing","Akihabara"],"foods":["Sushi","Ramen","Takoyaki"],"safety":"Very High"},
    "dubai":     {"name":"Dubai","country":"UAE","best_season":"Oct-Apr","activities":["Burj Khalifa","Desert safari","Gold Souk"],"foods":["Shawarma","Hummus","Dates"],"safety":"Very High"},
    "barcelona": {"name":"Barcelona","country":"Spain","best_season":"Apr-May, Sep-Oct","activities":["Sagrada Familia","Park Guell","Gothic Quarter"],"foods":["Paella","Tapas","Sangria"],"safety":"High"},
    "singapore": {"name":"Singapore","country":"Singapore","best_season":"Feb-Apr, Jul-Sep","activities":["Marina Bay Sands","Gardens by the Bay","Sentosa"],"foods":["Laksa","Chicken rice","Chili crab"],"safety":"Very High"},
}

# ── Conversation memory ────────────────────────────────────────────────────
class ConversationMemory:
    def __init__(self):
        self.history: List[Dict[str,str]] = []
        self.destination: Optional[str] = None
    def add(self, role, content):
        self.history.append({"role": role, "content": content})
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]
    def detect_city(self, text):
        for c in City:
            if c.value in text.lower():
                self.destination = c.value
                return

def build_system_prompt(mem):
    city = mem.destination
    if city and city in CITY_KB:
        kb = CITY_KB[city]
        info = f"DESTINATION: {kb['name']}, {kb['country']}\nBest season: {kb['best_season']}\nActivities: {', '.join(kb['activities'])}\nFoods: {', '.join(kb['foods'])}"
    else:
        info = "No city selected. Available: " + ", ".join(c.value.title() for c in City)
    return f"""You are a friendly Travel Itinerary Planner Assistant.\n{info}\nBe concise, warm, and helpful. Reference earlier conversation context."""

# ── ASR (Moonshine) ────────────────────────────────────────────────────────
print("Loading Moonshine ASR...")
from moonshine import load_model as load_moonshine, ASSETS_DIR
import tokenizers as hf_tokenizers
import keras

_asr_model = load_moonshine("moonshine/tiny")
_asr_tokenizer = hf_tokenizers.Tokenizer.from_file(str(ASSETS_DIR / "tokenizer.json"))
print("  ASR ready.")

def transcribe_audio(audio: np.ndarray, sr: int = 16000) -> str:
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    if sr != 16000:
        audio = resample(audio, int(len(audio)*16000/sr)).astype(np.float32)
    tensor = keras.ops.expand_dims(keras.ops.convert_to_tensor(audio), 0)
    tokens = _asr_model.generate(tensor)
    return _asr_tokenizer.decode_batch(tokens)[0].strip()

# ── TTS (Piper - fast) ────────────────────────────────────────────────────
print("Loading Piper TTS...")
from piper.voice import PiperVoice
import urllib.request

_PIPER_DIR = os.path.join(os.path.expanduser("~"), ".cache", "piper_tts")
os.makedirs(_PIPER_DIR, exist_ok=True)

_MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
_CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
_MODEL_FILE = os.path.join(_PIPER_DIR, "en_US-lessac-medium.onnx")
_CONFIG_FILE = os.path.join(_PIPER_DIR, "en_US-lessac-medium.onnx.json")

if not os.path.exists(_MODEL_FILE):
    print("  Downloading Piper model...")
    urllib.request.urlretrieve(_MODEL_URL, _MODEL_FILE)
if not os.path.exists(_CONFIG_FILE):
    print("  Downloading Piper config...")
    urllib.request.urlretrieve(_CONFIG_URL, _CONFIG_FILE)

_tts_model = PiperVoice.load(_MODEL_FILE, config_path=_CONFIG_FILE)
print(f"  TTS ready. Model: en_US-lessac-medium (Piper)")

def synthesize_text(text: str, voice: str = None) -> tuple:
    import tempfile
    import wave
    # Use a temp file for WAV output
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        # synthesize_wav() needs wave.Wave_write object, not plain file
        with wave.open(tmp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(_tts_model.config.sample_rate)
            _tts_model.synthesize_wav(text, wf)
        
        # Read back the audio data
        from scipy.io import wavfile as scipy_wavfile
        sr, samples = scipy_wavfile.read(tmp_path)
        
        # Ensure int16 format
        if samples.dtype != np.int16:
            if samples.dtype in [np.float32, np.float64]:
                samples = np.clip(samples, -1.0, 1.0)
                samples = (samples * 32767).astype(np.int16)
            else:
                samples = samples.astype(np.int16)
        
        return samples, sr
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# ── LLM streaming ──────────────────────────────────────────────────────────
async def stream_ollama_tokens(messages):
    payload = {"model": MODEL_NAME, "messages": messages, "stream": True,
               "options": {"num_predict": MAX_TOKENS, "temperature": 0.75}}
    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream("POST", f"{OLLAMA_BASE}/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line: continue
                chunk = json.loads(line)
                tok = chunk.get("message",{}).get("content","")
                if tok: yield tok
                if chunk.get("done"): break

# ── FastAPI app ────────────────────────────────────────────────────────────
app = FastAPI(title="Voice Travel Planner", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

conversations: Dict[str, ConversationMemory] = {}

@app.get("/", include_in_schema=False)
async def serve_ui():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index_voice.html"), media_type="text/html")

@app.get("/BG.png", include_in_schema=False)
async def serve_bg():
    # Try parent dir first, then same dir
    for base in [os.path.join(os.path.dirname(__file__), ".."), os.path.dirname(__file__)]:
        p = os.path.normpath(os.path.join(base, "BG.png"))
        if os.path.isfile(p):
            return FileResponse(p, media_type="image/png")
    return JSONResponse({"error": "BG.png not found"}, status_code=404)

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "model": MODEL_NAME, "asr": "moonshine/tiny",
            "tts": "piper-en_US-lessac-medium", "max_concurrent": MAX_CONCURRENT}

@app.get("/api/test-tts", include_in_schema=False)
async def test_tts():
    """Quick TTS test — open in browser to hear audio directly."""
    try:
        loop = asyncio.get_event_loop()
        samples, sr = await loop.run_in_executor(None, synthesize_text, "Hello! Travel Buddy voice test.", None)
        if samples.dtype == np.float32 or samples.dtype == np.float64:
            samples = np.clip(samples, -1.0, 1.0)
            samples = (samples * 32767).astype(np.int16)
        buf = io.BytesIO()
        wavfile.write(buf, sr, samples)
        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/wav")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ── POST /api/transcribe ───────────────────────────────────────────────────
@app.post("/api/transcribe")
async def api_transcribe(audio: UploadFile = File(...)):
    async with voice_semaphore:
        data = await audio.read()
        buf = io.BytesIO(data)
        sr, samples = wavfile.read(buf)
        # Handle stereo
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        t0 = time.time()
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, transcribe_audio, samples, sr)
        latency = (time.time() - t0) * 1000
        return {"text": text, "latency_ms": round(latency,1)}

# ── POST /api/synthesize ───────────────────────────────────────────────────
@app.post("/api/synthesize")
async def api_synthesize(text: str = Form(...), voice: str = Form(default=None)):
    async with voice_semaphore:
        try:
            t0 = time.time()
            loop = asyncio.get_event_loop()
            samples, sr = await loop.run_in_executor(None, synthesize_text, text, voice)
            latency = (time.time() - t0) * 1000
            # Piper already outputs int16, no conversion needed
            if samples.dtype != np.int16:
                if samples.dtype == np.float32 or samples.dtype == np.float64:
                    samples = np.clip(samples, -1.0, 1.0)
                    samples = (samples * 32767).astype(np.int16)
            buf = io.BytesIO()
            wavfile.write(buf, sr, samples)
            buf.seek(0)
            return StreamingResponse(buf, media_type="audio/wav",
                headers={"X-Latency-Ms": str(round(latency,1))})
        except Exception as e:
            print(f"[TTS ERROR] {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

# ── WebSocket /ws/chat ─────────────────────────────────────────────────────
@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    conv_id = str(uuid.uuid4())
    mem = ConversationMemory()
    conversations[conv_id] = mem
    await ws.send_text(json.dumps({"type":"hello","conversation_id":conv_id}))

    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"type":"error","code":"bad_json","message":"Invalid JSON"}))
                continue

            msg = data.get("message","").strip()
            if not msg:
                await ws.send_text(json.dumps({"type":"error","code":"empty","message":"Empty message"}))
                continue

            if data.get("city"): mem.destination = data["city"]
            mem.detect_city(msg)
            mem.add("user", msg)

            system_text = build_system_prompt(mem)
            messages = [{"role":"system","content":system_text}] + mem.history[-MAX_HISTORY:]

            full_reply = ""
            idx = 0
            async for token in stream_ollama_tokens(messages):
                full_reply += token
                await ws.send_text(json.dumps({"type":"token","conversation_id":conv_id,"token":token,"index":idx}))
                idx += 1

            mem.add("assistant", full_reply)
            await ws.send_text(json.dumps({"type":"final","conversation_id":conv_id,"message":full_reply}))

    except WebSocketDisconnect:
        conversations.pop(conv_id, None)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_voice:app", host="0.0.0.0", port=8000, reload=False, log_level="info")