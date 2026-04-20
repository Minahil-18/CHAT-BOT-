from __future__ import annotations
import asyncio, io, json, os, re, time, uuid
import datetime
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

from rag.retriever import LocalVectorRetriever
from tool_orchestrator import ToolOrchestrator

# ── Config ─────────────────────────────────────────────────────────────────
OLLAMA_BASE    = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME     = os.getenv("MODEL_NAME",      "qwen2.5:1.5b")
MAX_TOKENS     = int(os.getenv("MAX_TOKENS",  "500"))
MAX_HISTORY    = int(os.getenv("MAX_HISTORY", "4"))
MAX_CONCURRENT = 4
RAG_ENABLED          = os.getenv("RAG_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
RAG_TOP_K            = max(3, int(os.getenv("RAG_TOP_K", "2")))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "1500"))
TOOL_PROMPT_ENABLED  = os.getenv("TOOL_PROMPT_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
TOOL_TIMEOUT_SECONDS = float(os.getenv("TOOL_TIMEOUT_SECONDS", "2.0"))
MAX_CITIES_PER_QUERY = max(1, int(os.getenv("MAX_CITIES_PER_QUERY", "3")))
RAG_INDEX_PATH       = os.getenv(
    "RAG_INDEX_PATH",
    os.path.join(os.path.dirname(__file__), "rag", "index", "travel_index.json"),
)

# ── Tools Configuration ─────────────────────────────────────────────────────
TOOLS_ENABLED = os.getenv("TOOLS_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
TOOLS_DB_PATH = os.getenv("TOOLS_DB_PATH", "data/users.db")

# ── Concurrency semaphore ───────────────────────────────────────────────────
voice_semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# ── City knowledge base ─────────────────────────────────────────────────────
class City(str, Enum):
    istanbul  = "istanbul";  lahore    = "lahore";    islamabad = "islamabad"
    paris     = "paris";     bangkok   = "bangkok";   tokyo     = "tokyo"
    dubai     = "dubai";     barcelona = "barcelona"; singapore = "singapore"
    newyork   = "newyork";   hongkong  = "hongkong";  seoul     = "seoul"
    andros    = "andros";    srilanka  = "srilanka";  fraser    = "fraser"
    rio       = "rio"

CITY_KB = {
    "istanbul":  {
        "name": "Istanbul", "country": "Turkey",
        "best_season": "Apr-Jun, Sep-Oct",
        "activities": ["Hagia Sophia", "Blue Mosque", "Grand Bazaar", "Bosphorus cruise"],
        "foods": [
            "Nusr-Et (famous salt bae steaks)",
            "Balikci Sabahattin (fresh seafood in Sultanahmet)",
            "Hamdi Restaurant (kebab with Bosphorus views)",
        ],
        "safety": "High",
    },
    "lahore": {
        "name": "Lahore", "country": "Pakistan",
        "best_season": "Oct-Mar",
        "activities": ["Badshahi Mosque", "Lahore Fort", "Food Street"],
        "foods": [
            "Haveli Restaurant (rooftop dining in Walled City)",
            "Karim's (authentic nihari and parathas)",
            "Food Street Gawalmandi (street kebabs and biryani)",
            "Asha's Lahore (BBQ)",
        ],
        "safety": "High",
    },
    "islamabad": {
        "name": "Islamabad", "country": "Pakistan",
        "best_season": "Mar-May, Sep-Nov",
        "activities": ["Faisal Mosque", "Margalla Hills", "Daman-e-Koh"],
        "foods": [
            "Monal Restaurant (city views and Pakistani cuisine)",
            "Basti: Food Market (contemporary Pakistani)",
            "Hanif Rajput Rooftop Grill (sizzling grills, stunning rooftop view of the city and BBQ)",
            "TLT - The Last Tribe (authentic Pakistani desi food)",
        ],
        "safety": "Very High",
    },
    "paris": {
        "name": "Paris", "country": "France",
        "best_season": "Apr-Jun, Sep-Oct",
        "activities": ["Eiffel Tower", "Louvre", "Montmartre"],
        "foods": [
            "L'Ami Jean (classic French bistro)",
            "Maison Ladurée (macarons and pastries)",
            "Du Pain et des Idées (croissants)",
            "Arpège (Michelin-starred)",
        ],
        "safety": "High",
    },
    "bangkok": {
        "name": "Bangkok", "country": "Thailand",
        "best_season": "Nov-Feb",
        "activities": ["Grand Palace", "Wat Pho", "Floating markets"],
        "foods": [
            "Nahm (authentic Thai cuisine)",
            "Jay Fai (famous crab omelettes)",
            "Victory Monument (street pad thai)",
            "Yaowarat Road (seafood and Chinese-Thai)",
        ],
        "safety": "High",
    },
    "tokyo": {
        "name": "Tokyo", "country": "Japan",
        "best_season": "Mar-May, Sep-Nov",
        "activities": ["Senso-ji", "Shibuya Crossing", "Akihabara"],
        "foods": [
            "Sukiyabashi Jiro (legendary sushi, formerly Michelin 3-star)",
            "Ichiran (authentic ramen)",
            "Ippudo (tonkotsu ramen)",
            "Takoyaki Kiji (takoyaki)",
        ],
        "safety": "Very High",
    },
    "dubai": {
        "name": "Dubai", "country": "UAE",
        "best_season": "Oct-Apr",
        "activities": ["Burj Khalifa", "Desert safari", "Gold Souk"],
        "foods": [
            "Al Mallah (famous shawarma and meat)",
            "Zaroob (Emirati cuisine)",
            "Bu Qtair Fish (fresh grilled seafood and spicy fish curry)",
            "Nobu (Japanese-Peruvian fine dining)",
        ],
        "safety": "Very High",
    },
    "barcelona": {
        "name": "Barcelona", "country": "Spain",
        "best_season": "Apr-May, Sep-Oct",
        "activities": ["Sagrada Familia", "Park Guell", "Gothic Quarter"],
        "foods": [
            "Cervecería Catalana (tapas and vermouth)",
            "El Xampanyet (pintxos in Born)",
            "Botafumeiro (paella)",
            "Moments (Michelin-starred)",
        ],
        "safety": "High",
    },
    "singapore": {
        "name": "Singapore", "country": "Singapore",
        "best_season": "Feb-Apr, Jul-Sep",
        "activities": ["Marina Bay Sands", "Gardens by the Bay", "Sentosa"],
        "foods": [
            "Tian Tian Chicken Rice (Maxwell Food Centre)",
            "Burnt Ends (Australian BBQ in Tanjong Pagar)",
            "Good Bites (local hawker center)",
        ],
        "safety": "Very High",
    },
    "newyork": {
        "name": "New York City", "country": "USA",
        "best_season": "Apr-Jun, Sep-Nov",
        "activities": ["Statue of Liberty", "Central Park", "Times Square", "Broadway shows"],
        "foods": [
            "Katz's Delicatessen (famous pastrami)",
            "Di Fara Pizza (Brooklyn)",
            "Russ & Daughters (bagels with lox)",
            "Eleven Madison Park (fine dining American)",
        ],
        "safety": "High",
    },
    "hongkong": {
        "name": "Hong Kong", "country": "China",
        "best_season": "Oct-Dec, Mar-Apr",
        "activities": ["Victoria Peak", "Disneyland", "Temples", "Macao casinos"],
        "foods": [
            "Lung King Heen (dim sum)",
            "Mott 32 (modern Cantonese)",
            "Yat Lok (roast goose)",
            "Star Ferry Pier area (street food)",
        ],
        "safety": "Very High",
    },
    "seoul": {
        "name": "Seoul", "country": "South Korea",
        "best_season": "Mar-May, Sep-Nov",
        "activities": ["Gyeongbokgung Palace", "N Seoul Tower", "Myeongdong shopping", "Gangnam"],
        "foods": [
            "Mingles (modern Korean fine dining)",
            "Gujje House (Korean BBQ)",
            "Bonchon (Korean fried chicken)",
            "Gwangjang Market (tteokbokki and bindaetteok)",
        ],
        "safety": "Very High",
    },
    "andros": {
        "name": "Andros", "country": "Greece",
        "best_season": "May-Oct",
        "activities": ["Beach hopping", "Ancient ruins", "Hiking waterfalls", "Island villages"],
        "foods": [
            "Chora tavernas (moussaka and souvlaki)",
            "Batsi seafood taverns (grilled octopus)",
            "Family-run restaurants (Greek salad and feta)",
        ],
        "safety": "Very High",
    },
    "srilanka": {
        "name": "Sri Lanka", "country": "Sri Lanka",
        "best_season": "Dec-Mar (west coast), Jul-Sep (east coast)",
        "activities": ["Temple of the Tooth", "Safari in Yala", "Tea plantations", "Beach relaxing"],
        "foods": [
            "Ministry of Crab (seafood)",
            "Street stalls (kottu roti and lamprais)",
            "Tea plantation restaurants (local cuisine)",
            "Beach shacks (seafood curry)",
        ],
        "safety": "High",
    },
    "fraser": {
        "name": "Fraser Island (K'gari)", "country": "Australia",
        "best_season": "Apr-Oct (avoid Feb-Mar cyclone season)",
        "activities": ["4WD beach driving", "Lake McKenzie", "Shipwreck exploration", "Dingo spotting"],
        "foods": [
            "Fresh barramundi and coral trout (island restaurants)",
            "Local bakeries (meat pies and sausage rolls)",
            "Beachside cafes (fish and chips)",
            "Island resorts (fresh prawns)",
        ],
        "safety": "High",
    },
    "rio": {
        "name": "Rio de Janeiro", "country": "Brazil",
        "best_season": "Apr-Jun, Aug-Oct",
        "activities": ["Christ the Redeemer", "Copacabana Beach", "Sugarloaf Mountain", "Carnival (Feb/Mar)"],
        "foods": [
            "Confeitaria Colombo (Brazilian pastries)",
            "Boteco Belmonte (feijoada and churrasco)",
            "Bracarense (classic Brazilian churrascaria)",
            "Zaza Bistro (fine dining in Ipanema)",
        ],
        "safety": "Medium",
    },
}

# ── Conversation memory ─────────────────────────────────────────────────────
class ConversationMemory:
    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.destination: Optional[str] = None
        self.destinations: List[str] = []
        self.user_preferences: Dict[str, str] = {}
        self.user_id: Optional[str] = None
        self.user_name: Optional[str] = None

    def add(self, role: str, content: str):
        if role == "user":
            self._extract_preferences(content)
        self.history.append({"role": role, "content": content})
        if len(self.history) > MAX_HISTORY:
            if self.history[0]["role"] == "user":
                self.history = [self.history[0]] + self.history[2:]
            else:
                self.history = self.history[-MAX_HISTORY:]

    def _extract_preferences(self, text: str):
        t = text.lower()
        for s in ["spring", "summer", "fall", "autumn", "winter"]:
            if s in t:
                self.user_preferences["season"] = s
        if any(w in t for w in ["budget", "cheap", "affordable"]):
            self.user_preferences["budget"] = "budget-conscious"
        if any(w in t for w in ["luxury", "expensive", "5 star"]):
            self.user_preferences["budget"] = "luxury"
        if any(w in t for w in ["adventure", "hiking"]):
            self.user_preferences["style"] = "adventure"
        if any(w in t for w in ["relax", "beach"]):
            self.user_preferences["style"] = "relaxation"
        if any(w in t for w in ["family", "kids", "children"]):
            self.user_preferences["style"] = "family-friendly"

    def get_context_summary(self) -> str:
        if not self.user_preferences:
            return ""
        parts = []
        if "season" in self.user_preferences:
            parts.append(f"prefers {self.user_preferences['season']}")
        if "budget" in self.user_preferences:
            parts.append(self.user_preferences["budget"])
        if "style" in self.user_preferences:
            parts.append(f"{self.user_preferences['style']} traveler")
        return ("User preferences: " + ", ".join(parts)) if parts else ""

    def detect_city(self, text: str):
        cities = _extract_all_cities_from_text(text)
        if cities:
            self.destinations = cities[:MAX_CITIES_PER_QUERY]
            self.destination = self.destinations[0]


def build_system_prompt(
    mem: ConversationMemory,
    rag_context: str = "",
    rag_sources: Optional[List[str]] = None,
    tool_context: str = "",
) -> str:
    city = mem.destination
    food_recommendations = ""
    today = datetime.date.today().isoformat()

    foods_lines = []
    for city_key in mem.destinations[:MAX_CITIES_PER_QUERY]:
        if city_key in CITY_KB:
            kb_city = CITY_KB[city_key]
            foods_lines.append(f"{kb_city['name']}:")
            for f in kb_city["foods"]:
                foods_lines.append(f"  - {f}")
    if not foods_lines and city and city in CITY_KB:
        kb = CITY_KB[city]
        foods_lines = [f"{kb['name']}:", *[f"  - {f}" for f in kb["foods"]]]
    food_recommendations = "\n".join(foods_lines) if foods_lines else "No city selected"

    if rag_context:
        info = (
            "RETRIEVED TRAVEL KNOWLEDGE:\n"
            f"{rag_context}\n\n"
            "When useful, cite bracket labels like [1], [2] from the retrieved snippets."
        )
        if city and city in CITY_KB:
            kb = CITY_KB[city]
            info += (
                f"\n\nKNOWN RESTAURANTS IN {kb['name'].upper()}:\n"
                + "\n".join(f"  • {food}" for food in kb["foods"])
            )
    elif city and city in CITY_KB:
        kb = CITY_KB[city]
        info = (
            f"DESTINATION: {kb['name']}, {kb['country']}\n"
            f"Best season: {kb['best_season']}\n"
            f"Activities: {', '.join(kb['activities'])}\n"
            f"Foods: {', '.join(kb['foods'])}"
        )
    else:
        info = "No city selected. Available: " + ", ".join(c.value.title() for c in City)
        food_recommendations = "No city selected"

    prefs = mem.get_context_summary()
    if prefs:
        info += f"\n{prefs}"
    if rag_sources:
        info += "\nRetrieved sources: " + ", ".join(rag_sources)

    # Inject live tool data if available (used for itinerary requests)
    if tool_context:
        info += f"\n\nLIVE DATA FOR THIS TRIP:{tool_context}"

    user_line = f"\nKnown user name: {mem.user_name}" if mem.user_name else ""

    return f"""You are a Travel Planning Assistant.
TODAY: {today}

Rules:
- Use provided tool results and retrieved context when present.
- Do not invent weather, prices, flight details, or restaurants.
- Keep responses concise, practical, and travel-focused.
- If sources are present, cite snippet labels like [1], [2] when useful.
- For food, mention specific known places only.
- For multiple destinations, provide clearly separated sections per city.
- Default response length: short and complete (around 120-170 words).
- Format travel planning answers as 3 sections only: Flights, Weather, Food.
- Do not generate long day-by-day itineraries unless the user explicitly asks.
- When the user asks to "plan" a trip or requests an itinerary, generate a full
  day-by-day plan using the live data provided. Include morning, afternoon, and
  evening activities for each day. Mention specific restaurants from the food list.

Allowed destination food options:
{food_recommendations}

Context:
{info}{user_line}"""


# ── Travel question filter ──────────────────────────────────────────────────
_BANNED_KEYWORDS = {
    "sick", "medicine", "drug", "disease", "symptom", "doctor", "hospital",
    "pain", "headache", "fever", "covid", "vaccine", "prescription",
    "treatment", "diagnosis", "allergy", "injury", "tired", "fatigue",
    "exhausted", "sleep", "illness", "unhealthy", "health",
    "calculate", "equation", "formula", "homework", "solve", "math",
    "algebra", "geometry", "integration", "derivative", "theorem", "proof",
    "code", "program", "python", "javascript", "function", "class",
    "variable", "syntax", "debug", "error", "script", "algorithm",
    "database", "api", "html", "css", "server", "software",
    "election", "president", "government", "politics", "congress",
    "senate", "vote", "war", "conflict", "protest", "news",
    "workout", "exercise", "gym", "stock", "invest", "cryptocurrency", "bitcoin",
    "personal", "advice", "relationship", "love", "dating",
}

_TRAVEL_KEYWORDS = {
    "travel", "trip", "visit", "tour", "vacation", "holiday", "destination",
    "hotel", "flight", "airport", "visa", "passport", "booking",
    "beach", "mountain", "city", "country", "island", "museum", "temple",
    "restaurant", "food", "cuisine", "activity", "attraction", "sightseeing",
    "itinerary", "budget", "packing", "weather", "season", "guide",
    "plan", "days", "explore", "recommend",
    "paris", "tokyo", "dubai", "bangkok", "istanbul", "barcelona", "singapore",
    "lahore", "islamabad", "newyork", "hongkong", "seoul", "andros", "srilanka",
    "fraser", "rio", "new york", "hong kong", "sri lanka", "fraser island",
}


def is_travel_related(question: str) -> tuple[bool, str]:
    q = question.lower()
    q_simple = re.sub(r"[^a-z\s]", " ", q).strip()
    greeting_tokens = {"hi", "hello", "hey", "thanks", "thank", "ok", "yes", "no"}
    if q_simple and all(tok in greeting_tokens for tok in q_simple.split()):
        return True, ""
    for kw in _TRAVEL_KEYWORDS:
        if kw in q:
            return True, ""
    for kw in _BANNED_KEYWORDS:
        if kw in q:
            print(f"[FILTER] Rejected: '{question}' (keyword: {kw})")
            return False, "I'm a travel planning assistant. I can only help with destinations, itineraries, hotels, flights, and travel tips. Please ask a travel-related question! ✈️"
    print(f"[FILTER] Rejected: '{question}' (no travel keywords found)")
    return False, "I'm a travel planning assistant. I can only help with destinations, itineraries, hotels, flights, and travel tips. Please ask a travel-related question! ✈️"


def _contains_travel_keyword(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _TRAVEL_KEYWORDS)


# ── ASR (Moonshine) ─────────────────────────────────────────────────────────
print("Loading Moonshine ASR...")
from moonshine import load_model as load_moonshine, ASSETS_DIR
import tokenizers as hf_tokenizers
import keras

_asr_model     = load_moonshine("moonshine/tiny")
_asr_tokenizer = hf_tokenizers.Tokenizer.from_file(str(ASSETS_DIR / "tokenizer.json"))
print("  ASR ready.")


def transcribe_audio(audio: np.ndarray, sr: int = 16000) -> str:
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    if sr != 16000:
        audio = resample(audio, int(len(audio) * 16000 / sr)).astype(np.float32)
    tensor = keras.ops.expand_dims(keras.ops.convert_to_tensor(audio), 0)
    tokens = _asr_model.generate(tensor)
    return _asr_tokenizer.decode_batch(tokens)[0].strip()


# ── TTS (Piper) ─────────────────────────────────────────────────────────────
print("Loading Piper TTS...")
from piper.voice import PiperVoice
import urllib.request

_PIPER_DIR  = os.path.join(os.path.expanduser("~"), ".cache", "piper_tts")
os.makedirs(_PIPER_DIR, exist_ok=True)

_MODEL_URL  = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
_CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
_MODEL_FILE  = os.path.join(_PIPER_DIR, "en_US-lessac-medium.onnx")
_CONFIG_FILE = os.path.join(_PIPER_DIR, "en_US-lessac-medium.onnx.json")

if not os.path.exists(_MODEL_FILE):
    print("  Downloading Piper model...")
    urllib.request.urlretrieve(_MODEL_URL, _MODEL_FILE)
if not os.path.exists(_CONFIG_FILE):
    print("  Downloading Piper config...")
    urllib.request.urlretrieve(_CONFIG_URL, _CONFIG_FILE)

_tts_model = PiperVoice.load(_MODEL_FILE, config_path=_CONFIG_FILE)
print("  TTS ready. Model: en_US-lessac-medium (Piper)")


def synthesize_text(text: str, voice: str = None) -> tuple:
    import tempfile, wave
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(_tts_model.config.sample_rate)
            _tts_model.synthesize_wav(text, wf)
        from scipy.io import wavfile as scipy_wavfile
        sr, samples = scipy_wavfile.read(tmp_path)
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


# ── LLM streaming ───────────────────────────────────────────────────────────
async def stream_ollama_tokens(messages: list):
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "options": {
            "num_predict": MAX_TOKENS,
            "temperature": 0.5,
            "top_k": 40,
            "top_p": 0.9,
        },
    }
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", f"{OLLAMA_BASE}/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                tok = chunk.get("message", {}).get("content", "")
                if tok:
                    yield tok
                if chunk.get("done"):
                    break


# ── FastAPI app ─────────────────────────────────────────────────────────────
app = FastAPI(title="Voice Travel Planner", version="3.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversations:    Dict[str, ConversationMemory] = {}
rag_retriever   = LocalVectorRetriever(index_path=RAG_INDEX_PATH)
tool_orchestrator = ToolOrchestrator(db_path=TOOLS_DB_PATH) if TOOLS_ENABLED else None


@app.on_event("startup")
async def startup_event():
    if not RAG_ENABLED:
        print("[RAG] Disabled by environment setting")
    else:
        ok = rag_retriever.load()
        if ok:
            print(f"[RAG] Loaded index with {rag_retriever.size} chunks")
            print("[RAG] Pre-warming embedding model...")
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: rag_retriever.retrieve("travel planning", "travel", top_k=1),
                )
                print("[RAG] Model warm-up complete")
            except Exception as e:
                print(f"[RAG] Warm-up skipped: {e}")
        else:
            print(f"[RAG] Index unavailable: {rag_retriever.last_error}")

    if not TOOLS_ENABLED:
        print("[TOOLS] Disabled by environment setting")
    elif tool_orchestrator:
        print(f"[TOOLS] Initialized with {len(tool_orchestrator.get_tool_schemas())} tools")


@app.get("/", include_in_schema=False)
async def serve_ui():
    return FileResponse(
        os.path.join(os.path.dirname(__file__), "index_voice.html"),
        media_type="text/html",
    )


@app.get("/BG.png", include_in_schema=False)
async def serve_bg():
    for base in [os.path.join(os.path.dirname(__file__), ".."), os.path.dirname(__file__)]:
        p = os.path.normpath(os.path.join(base, "BG.png"))
        if os.path.isfile(p):
            return FileResponse(p, media_type="image/png")
    return JSONResponse({"error": "BG.png not found"}, status_code=404)


@app.get("/healthz")
async def healthz():
    return {
        "status": "ok", "model": MODEL_NAME,
        "asr": "moonshine/tiny", "tts": "piper-en_US-lessac-medium",
        "max_concurrent": MAX_CONCURRENT,
        "rag_enabled": RAG_ENABLED, "rag_ready": rag_retriever.is_ready,
        "rag_chunks": rag_retriever.size,
    }


@app.get("/api/rag/status")
async def rag_status():
    return {
        "enabled": RAG_ENABLED, "ready": rag_retriever.is_ready,
        "index_path": RAG_INDEX_PATH, "chunks": rag_retriever.size,
        "last_error": rag_retriever.last_error,
        "top_k": RAG_TOP_K, "max_context_chars": RAG_MAX_CONTEXT_CHARS,
    }


@app.get("/api/tools/status")
async def tools_status():
    if not TOOLS_ENABLED or not tool_orchestrator:
        return {"enabled": False, "tools": []}
    schemas = tool_orchestrator.get_tool_schemas()
    return {
        "enabled": True,
        "tools_count": len(schemas),
        "tools": [{"name": s["name"], "description": s.get("description", "")} for s in schemas],
        "db_path": TOOLS_DB_PATH,
    }


@app.post("/retrieve")
async def retrieve_documents(data: dict):
    query  = data.get("query")
    top_k  = data.get("top_k", 4)
    city   = data.get("city")
    if not query:
        return JSONResponse({"error": "query parameter required"}, status_code=400)
    if not RAG_ENABLED or not rag_retriever.is_ready:
        return JSONResponse({"error": "RAG not enabled or not ready"}, status_code=503)
    try:
        loop   = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(
            None, lambda: rag_retriever.retrieve(query, city, top_k)
        )
        context, sources = rag_retriever.format_for_prompt(chunks, max_chars=RAG_MAX_CONTEXT_CHARS)
        return {
            "query": query, "top_k": top_k, "city": city,
            "chunks_retrieved": len(chunks),
            "context": context, "sources": sources,
            "chunks": [
                {"doc_id": c.doc_id, "city": c.city, "title": c.title,
                 "text": c.text, "score": c.score}
                for c in chunks
            ],
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/test-tts", include_in_schema=False)
async def test_tts():
    try:
        loop = asyncio.get_event_loop()
        samples, sr = await loop.run_in_executor(
            None, synthesize_text, "Hello! Travel Buddy voice test.", None
        )
        if samples.dtype in [np.float32, np.float64]:
            samples = np.clip(samples, -1.0, 1.0)
            samples = (samples * 32767).astype(np.int16)
        buf = io.BytesIO()
        wavfile.write(buf, sr, samples)
        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/wav")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/transcribe")
async def api_transcribe(audio: UploadFile = File(...)):
    async with voice_semaphore:
        data    = await audio.read()
        buf     = io.BytesIO(data)
        sr, samples = wavfile.read(buf)
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        t0   = time.time()
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, transcribe_audio, samples, sr)
        return {"text": text, "latency_ms": round((time.time() - t0) * 1000, 1)}


@app.post("/api/synthesize")
async def api_synthesize(text: str = Form(...), voice: str = Form(default=None)):
    async with voice_semaphore:
        try:
            t0      = time.time()
            loop    = asyncio.get_event_loop()
            samples, sr = await loop.run_in_executor(None, synthesize_text, text, voice)
            if samples.dtype != np.int16:
                if samples.dtype in [np.float32, np.float64]:
                    samples = np.clip(samples, -1.0, 1.0)
                    samples = (samples * 32767).astype(np.int16)
            buf = io.BytesIO()
            wavfile.write(buf, sr, samples)
            buf.seek(0)
            return StreamingResponse(
                buf, media_type="audio/wav",
                headers={"X-Latency-Ms": str(round((time.time() - t0) * 1000, 1))},
            )
        except Exception as e:
            print(f"[TTS ERROR] {e}")
            return JSONResponse({"error": str(e)}, status_code=500)


# ── Helper: run RAG concurrently ────────────────────────────────────────────
async def _fetch_rag(msg: str, destination: Optional[str]) -> tuple[str, List[str]]:
    """Returns (rag_context, rag_sources). Never raises — returns empty on error."""
    if not RAG_ENABLED or not rag_retriever.is_ready:
        return "", []
    try:
        t0   = time.time()
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(
            None,
            lambda: rag_retriever.retrieve(msg, destination, RAG_TOP_K),
        )
        context, sources = rag_retriever.format_for_prompt(chunks, max_chars=RAG_MAX_CONTEXT_CHARS)
        elapsed = time.time() - t0
        print(f"[RAG] Latency: {elapsed:.3f}s")
        if elapsed > 2.0:
            print("[RAG WARNING] Latency exceeded 2s target!")
        return context, sources
    except Exception as e:
        print(f"[RAG ERROR] {e}")
        return "", []


# ── Helper: detect tool calls from user message directly ───────────────────
def _city_for_tools(city_value: str) -> str:
    alias = {
        "newyork": "new york",
        "hongkong": "hong kong",
        "srilanka": "sri lanka",
        "fraser": "fraser island",
    }
    return alias.get(city_value, city_value)


def _extract_city_from_text(text: str) -> Optional[str]:
    cities = _extract_all_cities_from_text(text)
    return cities[0] if cities else None


def _extract_all_cities_from_text(text: str) -> List[str]:
    normalized = text.lower().replace(" ", "")
    ordered: List[str] = []
    for c in City:
        if c.value in normalized and c.value not in ordered:
            ordered.append(c.value)
    return ordered


def _dedupe_tool_calls(tool_calls: List[Any]) -> List[Any]:
    deduped = []
    seen = set()
    for tc in tool_calls:
        key = (tc.tool_name, json.dumps(tc.arguments, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(tc)
    return deduped


# ── NEW: detect whether user wants a full itinerary/plan ───────────────────
def _is_itinerary_request(user_message: str) -> bool:
    """Returns True when the user wants a narrative day-by-day trip plan."""
    m = user_message.lower()
    return any(w in m for w in [
        "plan", "itinerary", "day trip", "days trip", "days in",
        "schedule", "what to do", "day by day", "full trip",
        "trip plan", "travel plan",
    ])


def _predict_tools_from_message(msg: str, destination_hint: Optional[str] = None) -> list:
    """
    Parse the user's message with simple keyword rules and return a list of
    synthetic 'detected tool' objects that tool_orchestrator can execute.
    Returns [] if no tool needed (fallback to normal LLM stream).
    """
    if not tool_orchestrator:
        return []
    today = datetime.date.today().isoformat()
    m = msg.lower()
    calls = []
    mentioned_cities = _extract_all_cities_from_text(m)
    if destination_hint and destination_hint not in mentioned_cities:
        mentioned_cities.append(destination_hint)
    mentioned_cities = mentioned_cities[:MAX_CITIES_PER_QUERY]

    # ── flight detection ────────────────────────────────────────────────────
    if any(w in m for w in ["flight", "fly", "flights"]) or ("from" in m and "to" in m):
        from_city, to_city = None, None
        fm = re.search(r"from\s+(.+?)\s+to\s+", m)
        tm = re.search(r"to\s+(.+?)(?:\s+for|\s+\d+\s*days|$)", m)
        if fm:
            from_city = fm.group(1).strip()
        if tm:
            to_city = tm.group(1).strip()
        if from_city:
            mapped_from = _extract_city_from_text(from_city)
            if mapped_from:
                from_city = _city_for_tools(mapped_from)
        if to_city:
            mapped_to = _extract_city_from_text(to_city)
            if mapped_to:
                to_city = _city_for_tools(mapped_to)
        if from_city and to_city:
            raw = f'[TOOL_CALL: search_flights {{"from_city": "{from_city}", "to_city": "{to_city}", "departure_date": "{today}"}}]'
            detected = tool_orchestrator.detect_all_tool_calls(raw)
            calls.extend(detected)
        else:
            if mentioned_cities:
                for hinted_city in mentioned_cities:
                    raw = (
                        f'[TOOL_CALL: search_flights '
                        f'{{"from_city": "your city", "to_city": "{_city_for_tools(hinted_city)}", "departure_date": "{today}"}}]'
                    )
                    detected = tool_orchestrator.detect_all_tool_calls(raw)
                    calls.extend(detected)

    # ── weather detection ───────────────────────────────────────────────────
    if any(w in m for w in ["weather", "temperature", "climate", "forecast"]) or _is_itinerary_request(m):
        weather_cities = mentioned_cities or ([_extract_city_from_text(m)] if _extract_city_from_text(m) else [])
        for city in weather_cities[:MAX_CITIES_PER_QUERY]:
            raw = f'[TOOL_CALL: get_weather {{"city": "{_city_for_tools(city)}"}}]'
            detected = tool_orchestrator.detect_all_tool_calls(raw)
            calls.extend(detected)

    # ── budget detection ────────────────────────────────────────────────────
    if any(w in m for w in ["budget", "cost", "expense", "how much", "price"]) or _is_itinerary_request(m):
        days_match = re.search(r"(\d+)\s*day", m)
        days = int(days_match.group(1)) if days_match else 3
        if mentioned_cities:
            for city in mentioned_cities[:MAX_CITIES_PER_QUERY]:
                raw = f'[TOOL_CALL: calculate_trip_budget {{"destination": "{_city_for_tools(city)}", "duration_days": {days}}}]'
                detected = tool_orchestrator.detect_all_tool_calls(raw)
                calls.extend(detected)

    # ── hotel detection ─────────────────────────────────────────────────────
    if any(w in m for w in ["hotel", "hotels", "stay", "accommodation", "hostel", "airbnb", "where to sleep", "where to stay"]) or _is_itinerary_request(m):
        if mentioned_cities:
            for city in mentioned_cities[:MAX_CITIES_PER_QUERY]:
                raw = f'[TOOL_CALL: search_hotels {{"city": "{_city_for_tools(city)}", "check_in": "{today}"}}]'
                detected = tool_orchestrator.detect_all_tool_calls(raw)
                calls.extend(detected)

    return _dedupe_tool_calls(calls)


def _extract_profile_updates(text: str) -> Dict[str, str]:
    updates: Dict[str, str] = {}
    t = text.strip()
    name_match = re.search(r"(?:my name is|name is)\s+([A-Za-z][A-Za-z\s]{1,40})", t, re.IGNORECASE)
    email_match = re.search(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", t)
    if name_match:
        updates["name"] = name_match.group(1).strip()
    if email_match:
        updates["email"] = email_match.group(1).strip()
    return updates


def _build_profile_saved_message(updates: Dict[str, str]) -> str:
    parts = []
    if "name" in updates:
        parts.append(f"name: {updates['name']}")
    if "email" in updates:
        parts.append(f"email: {updates['email']}")
    details = ", ".join(parts) if parts else "your details"
    return f"Got it — I saved {details} in your profile. I can now personalize your future travel plans."


def _infer_requested_sections(user_message: str) -> set[str]:
    m = user_message.lower()
    sections: set[str] = set()
    if any(w in m for w in ["flight", "flights", "fly", "airport"]):
        sections.add("flights")
    if any(w in m for w in ["weather", "temperature", "forecast", "climate"]):
        sections.add("weather")
    if any(w in m for w in ["food", "restaurant", "cuisine", "eat"]):
        sections.add("food")
    if any(w in m for w in ["budget", "cost", "expense", "how much", "price"]):
        sections.add("budget")
    if any(w in m for w in ["hotel", "hotels", "stay", "accommodation", "hostel", "airbnb", "where to sleep", "where to stay"]):
        sections.add("hotels")
    return sections


def _build_compact_tool_reply(mem: ConversationMemory, tool_results: List[tuple], user_message: str) -> str:
    weather_lines: List[str] = []
    flight_lines: List[str] = []
    budget_lines: List[str] = []
    hotel_lines: List[str] = []
    food_lines: List[str] = []

    for tool_name, wrapped in tool_results:
        if not isinstance(wrapped, dict):
            continue
        if not wrapped.get("success"):
            continue
        content = wrapped.get("result", {})
        if not isinstance(content, dict):
            continue

        if tool_name == "get_weather":
            city = str(content.get("city", "city")).title()
            temp = content.get("temperature")
            cond = content.get("condition") or content.get("description", "")
            humidity = content.get("humidity")
            weather_lines.append(f"- {city}: {temp}°C, {cond}, humidity {humidity}%")

        if tool_name == "search_flights":
            to_city = str(content.get("to", "destination")).title()
            options = content.get("options", [])[:3]
            if options:
                flight_lines.append(f"- {to_city}:")
                for opt in options:
                    airline = opt.get("airline", "Airline")
                    dep = opt.get("departure", "--")
                    arr = opt.get("arrival", "--")
                    price = opt.get("price_per_person", opt.get("price", "N/A"))
                    flight_lines.append(f"  {airline} {dep}->{arr}, ${price}")

        if tool_name == "calculate_trip_budget":
            destination = str(content.get("destination", "destination")).title()
            total = content.get("total")
            per_day = content.get("per_day_per_person")
            budget_level = content.get("budget_level", "moderate")
            budget_lines.append(f"- {destination}: total ${total}, ~${per_day}/day/person ({budget_level})")

        if tool_name == "search_hotels":
            # city_raw = str(content.get("city", "")).strip()
            city_raw = (
                str(content.get("city"))
                or str(content.get("destination"))
                or str(content.get("location"))
                or ""
            ).strip()

            city_display = city_raw.title() if city_raw else "destination"
            # Try both "hotels" and "options" keys since different tool versions use different keys
           # options = content.get("hotels") or content.get("options") or content.get("results") or []
            options = (
                content.get("hotels")
                or content.get("options")
                or content.get("results")
                or content.get("data")
                or content.get("listings")
                or []
            )
            options = [o for o in options if isinstance(o, dict)][:3]
            if options and len(options) > 0:
                hotel_lines.append(f"- {city_display}:")
                for opt in options:
                    name = opt.get("name") or opt.get("hotel_name") or "Hotel"
                    price = opt.get("price_per_night") or opt.get("price") or "N/A"
                    rating = opt.get("rating") or opt.get("stars") or "N/A"
                    hotel_lines.append(f"  {name} ${price}/night, rating {rating}")
            else:
                # Tool ran but returned no listings — use a curated static fallback
                # keyed by city name so we always show something useful
                _HOTEL_KB: Dict[str, List[str]] = {
                    "istanbul":  ["Raffles Istanbul $320/night, rating 4.9", "CVK Park Bosphorus $180/night, rating 4.7", "Hotel Empress Zoe $95/night, rating 4.5"],
                    "lahore":    ["Pearl Continental Lahore $120/night, rating 4.6", "Avari Hotel $90/night, rating 4.4", "Luxus Grand Hotel $75/night, rating 4.3"],
                    "islamabad": ["Serena Hotel $150/night, rating 4.7", "Marriott Islamabad $130/night, rating 4.6", "Hotel One $55/night, rating 4.2"],
                    "paris":     ["Le Bristol $850/night, rating 4.9", "Hotel de Crillon $750/night, rating 4.8", "Hotel des Grands Boulevards $220/night, rating 4.6"],
                    "bangkok":   ["Mandarin Oriental $380/night, rating 4.9", "Capella Bangkok $420/night, rating 4.8", "Novotel Bangkok $90/night, rating 4.3"],
                    "tokyo":     ["Park Hyatt Tokyo $480/night, rating 4.8", "The Peninsula Tokyo $560/night, rating 4.9", "Dormy Inn Asakusa $80/night, rating 4.4"],
                    "dubai":     ["Burj Al Arab $1200/night, rating 5.0", "Atlantis The Palm $350/night, rating 4.7", "Rove Downtown $110/night, rating 4.4"],
                    "barcelona": ["Hotel Arts Barcelona $380/night, rating 4.8", "W Barcelona $290/night, rating 4.6", "Hotel Praktik Rambla $130/night, rating 4.4"],
                    "singapore": ["Marina Bay Sands $550/night, rating 4.8", "Raffles Singapore $800/night, rating 4.9", "Ibis Budget Singapore $80/night, rating 4.1"],
                    "newyork":   ["The Plaza $695/night, rating 4.8", "1 Hotel Central Park $420/night, rating 4.7", "Pod 51 Hotel $130/night, rating 4.2"],
                    "hongkong":  ["The Peninsula Hong Kong $650/night, rating 4.9", "Four Seasons HK $580/night, rating 4.8", "Ibis Hong Kong Central $120/night, rating 4.2"],
                    "seoul":     ["Lotte Hotel Seoul $280/night, rating 4.7", "Four Seasons Seoul $420/night, rating 4.8", "Ibis Ambassador Myeongdong $90/night, rating 4.3"],
                    "andros":    ["Aneroussa Beach Hotel $160/night, rating 4.6", "Paradiso Studios $80/night, rating 4.4", "Villa Rena $65/night, rating 4.3"],
                    "srilanka":  ["Galle Face Hotel $180/night, rating 4.6", "Jetwing Blue $140/night, rating 4.5", "Cinnamon Red $95/night, rating 4.3"],
                    "fraser":    ["Kingfisher Bay Resort $220/night, rating 4.6", "Eurong Beach Resort $160/night, rating 4.4", "Happy Valley Retreat $110/night, rating 4.3"],
                    "rio":       ["Belmond Copacabana Palace $420/night, rating 4.8", "Hotel Fasano Rio $380/night, rating 4.7", "Windsor Atlantica $150/night, rating 4.4"],
                }
                # Match city_raw back to CITY_KB key
                city_key = city_raw.lower().replace(" ", "")
                # Handle aliases
                _alias_reverse = {"newyork": "new york", "hongkong": "hong kong", "srilanka": "sri lanka", "fraser": "fraser island"}
                matched_key = next(
                    (k for k in _HOTEL_KB if city_raw.lower().startswith(k) or k in city_raw.lower().replace(" ", "")),
                    None
                )
                if matched_key and _HOTEL_KB.get(matched_key):
                    hotel_lines.append(f"- {city_display} (curated picks):")
                    for h in _HOTEL_KB[matched_key]:
                        hotel_lines.append(f"  {h}")
                else:
                    hotel_lines.append(f"- {city_display}: no live hotel data available")

    cities_for_food = mem.destinations[:MAX_CITIES_PER_QUERY] if mem.destinations else ([mem.destination] if mem.destination else [])
    for city_key in cities_for_food:
        kb = CITY_KB.get(city_key)
        if not kb:
            continue
        picks = kb["foods"][:3]
        food_lines.append(f"- {kb['name']}: " + "; ".join(picks))

    requested = _infer_requested_sections(user_message)
    if not requested:
        if flight_lines:
            requested.add("flights")
        if weather_lines:
            requested.add("weather")
        if budget_lines:
            requested.add("budget")
        if hotel_lines:
            requested.add("hotels")
        if food_lines:
            requested.add("food")

    sections_out: List[str] = []
    if "flights" in requested:
        sections_out.append("Flights:\n" + "\n".join(flight_lines or ["- Flight options unavailable for this destination."]))
    if "weather" in requested:
        sections_out.append("Weather:\n" + "\n".join(weather_lines or ["- Weather data unavailable for this destination."]))
    if "budget" in requested:
        sections_out.append("Budget:\n" + "\n".join(budget_lines or ["- Budget data unavailable for this destination."]))
    if "hotels" in requested:
        sections_out.append("Hotels:\n" + "\n".join(hotel_lines or ["- Hotel options unavailable for this destination."]))
    if "food" in requested:
        sections_out.append("Food:\n" + "\n".join(food_lines or ["- Food recommendations unavailable for this destination."]))

    return "\n\n".join(sections_out) if sections_out else "I couldn't find relevant tool output for this request."


# ── WebSocket /ws/chat ──────────────────────────────────────────────────────
@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    conv_id = str(uuid.uuid4())
    mem     = ConversationMemory()
    conversations[conv_id] = mem
    await ws.send_text(json.dumps({"type": "hello", "conversation_id": conv_id}))

    try:
        while True:
            raw = await ws.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"type": "error", "code": "bad_json", "message": "Invalid JSON"}))
                continue

            msg = data.get("message", "").strip()
            if not msg:
                await ws.send_text(json.dumps({"type": "error", "code": "empty", "message": "Empty message"}))
                continue

            if not mem.user_id:
                mem.user_id = data.get("user_id") or conv_id

            # ── CRM: profile updates work regardless of travel filter ────────
            profile_updates: Dict[str, str] = _extract_profile_updates(msg)
            if TOOLS_ENABLED and tool_orchestrator and mem.user_id:
                loop = asyncio.get_event_loop()
                try:
                    user_profile = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: tool_orchestrator.crm.get_user(mem.user_id)),
                        timeout=TOOL_TIMEOUT_SECONDS,
                    )
                except Exception as exc:
                    print(f"[CRM] get_user failed: {exc}")
                    user_profile = None

                if profile_updates:
                    try:
                        if user_profile:
                            await asyncio.wait_for(
                                loop.run_in_executor(
                                    None, lambda: tool_orchestrator.crm.update_user(mem.user_id, **profile_updates)
                                ),
                                timeout=TOOL_TIMEOUT_SECONDS,
                            )
                        elif profile_updates.get("name"):
                            await asyncio.wait_for(
                                loop.run_in_executor(
                                    None,
                                    lambda: tool_orchestrator.crm.create_user(
                                        name=profile_updates["name"],
                                        email=profile_updates.get("email", ""),
                                        user_id=mem.user_id,
                                    ),
                                ),
                                timeout=TOOL_TIMEOUT_SECONDS,
                            )
                            user_profile = await asyncio.wait_for(
                                loop.run_in_executor(None, lambda: tool_orchestrator.crm.get_user(mem.user_id)),
                                timeout=TOOL_TIMEOUT_SECONDS,
                            )
                    except Exception as exc:
                        print(f"[CRM] profile update failed: {exc}")

                if user_profile and user_profile.get("name"):
                    mem.user_name = user_profile["name"]

            # Profile-only messages get instant confirmation
            if profile_updates and not _contains_travel_keyword(msg):
                saved_msg = _build_profile_saved_message(profile_updates)
                await ws.send_text(json.dumps({"type": "token", "conversation_id": conv_id, "token": saved_msg, "index": 0}))
                await ws.send_text(json.dumps({"type": "final", "conversation_id": conv_id, "message": saved_msg}))
                continue

            # ── 1. Travel filter ────────────────────────────────────────────
            is_valid, refusal_msg = is_travel_related(msg)
            if not is_valid:
                await ws.send_text(json.dumps({"type": "token", "conversation_id": conv_id, "token": refusal_msg, "index": 0}))
                await ws.send_text(json.dumps({"type": "final", "conversation_id": conv_id, "message": refusal_msg}))
                continue

            if data.get("city"):
                mem.destination = data["city"]
            mem.detect_city(msg)
            mem.add("user", msg)

            # ── 2. RAG — run concurrently with tool detection ────────────────
            rag_task = asyncio.create_task(_fetch_rag(msg, mem.destination))

            # ── 3. Detect tools from user message (no LLM call needed) ──────
            tool_calls_to_run: list = []
            if TOOLS_ENABLED and tool_orchestrator:
                try:
                    loop = asyncio.get_event_loop()
                    tool_calls_to_run = await loop.run_in_executor(
                        None, lambda: _predict_tools_from_message(msg, mem.destination)
                    )
                    print(f"[TOOLS] Pre-detected {len(tool_calls_to_run)} tool(s) from message")
                except Exception as e:
                    print(f"[TOOLS PRE-DETECT ERROR] {e}")

            # ── 4. Wait for RAG ──────────────────────────────────────────────
            rag_context, rag_sources = await rag_task

            # ── 5. Decide routing: itinerary vs structured tool reply ────────
            is_itinerary = _is_itinerary_request(msg)

            # For itinerary requests: run tools to collect live data, then feed
            # everything to the LLM to write a proper narrative day-by-day plan.
            # For direct data requests (weather/flights/budget alone): use the
            # fast compact tool reply path without any LLM call.
            pre_tool_context = ""
            if tool_calls_to_run and is_itinerary:
                print(f"[ITINERARY] Running {len(tool_calls_to_run)} tool(s) to enrich LLM context...")
                t0_pre = time.time()
                loop = asyncio.get_event_loop()

                async def _run_one(d):
                    try:
                        return await asyncio.wait_for(
                            loop.run_in_executor(None, lambda dd=d: tool_orchestrator.execute_tool(dd)),
                            timeout=TOOL_TIMEOUT_SECONDS,
                        )
                    except Exception as exc:
                        return {"error": str(exc), "tool": d.tool_name}

                pre_results = await asyncio.gather(*[_run_one(d) for d in tool_calls_to_run])
                print(f"[ITINERARY] Tools done in {time.time() - t0_pre:.3f}s")

                for detected, result in zip(tool_calls_to_run, pre_results):
                    # Notify frontend that tool ran
                    await ws.send_text(json.dumps({
                        "type": "tool_result",
                        "conversation_id": conv_id,
                        "tool_name": detected.tool_name,
                        "result": result,
                    }))
                    if isinstance(result, dict) and result.get("success"):
                        pre_tool_context += (
                            f"\n[{detected.tool_name}]: {json.dumps(result.get('result', {}))}"
                        )

                # Tools already handled — clear so the compact path is skipped
                tool_calls_to_run = []

            # ── 6. Build system prompt (with optional live tool data) ────────
            system_text = build_system_prompt(
                mem,
                rag_context=rag_context,
                rag_sources=rag_sources,
                tool_context=pre_tool_context,
            )
            if TOOLS_ENABLED and tool_orchestrator and TOOL_PROMPT_ENABLED:
                system_text += f"\n\n{tool_orchestrator.format_tools_for_prompt()}"

            # ── 7a. COMPACT TOOL PATH — structured data requests ─────────────
            if tool_calls_to_run:
                # Notify frontend of pending tool calls
                for detected in tool_calls_to_run:
                    await ws.send_text(json.dumps({
                        "type": "tool_start",
                        "conversation_id": conv_id,
                        "tool_name": detected.tool_name,
                        "tool_args": detected.arguments,
                    }))

                t0_tools = time.time()
                loop = asyncio.get_event_loop()

                async def run_tool_with_timeout(detected):
                    try:
                        out = await asyncio.wait_for(
                            loop.run_in_executor(None, lambda d=detected: tool_orchestrator.execute_tool(d)),
                            timeout=TOOL_TIMEOUT_SECONDS,
                        )
                        return out
                    except asyncio.TimeoutError:
                        return {"error": f"Tool timed out after {TOOL_TIMEOUT_SECONDS:.1f}s", "tool": detected.tool_name}
                    except Exception as exc:
                        return {"error": f"Tool failed: {exc}", "tool": detected.tool_name}

                executed_results = await asyncio.gather(*[
                    run_tool_with_timeout(d) for d in tool_calls_to_run
                ])
                print(f"[TOOLS] Executed {len(tool_calls_to_run)} tool(s) in {time.time() - t0_tools:.3f}s")

                tool_results = []
                for detected, result in zip(tool_calls_to_run, executed_results):
                    await ws.send_text(json.dumps({
                        "type": "tool_result",
                        "conversation_id": conv_id,
                        "tool_name": detected.tool_name,
                        "result": result,
                    }))
                    tool_results.append((detected.tool_name, result))

                reply = _build_compact_tool_reply(mem, tool_results, msg)
                print(f"[STREAM] Sending compact tool reply ({len(tool_results)} tool(s))...")
                idx = 0
                for chunk in reply.split("\n"):
                    token = chunk + "\n"
                    await ws.send_text(json.dumps({
                        "type": "token", "conversation_id": conv_id,
                        "token": token, "index": idx,
                    }))
                    idx += 1
                mem.add("assistant", reply)
                if profile_updates:
                    reply = f"{_build_profile_saved_message(profile_updates)}\n\n{reply}"

            # ── 7b. LLM PATH — itinerary requests and plain dialogue ─────────
            else:
                messages = [{"role": "system", "content": system_text}] + mem.history[-MAX_HISTORY:]
                print("[STREAM] Streaming LLM response" + (" (itinerary + tool context)" if pre_tool_context else "") + "...")
                reply = ""
                idx   = 0
                async for token in stream_ollama_tokens(messages):
                    reply += token
                    await ws.send_text(json.dumps({
                        "type": "token", "conversation_id": conv_id,
                        "token": token, "index": idx,
                    }))
                    idx += 1
                mem.add("assistant", reply)
                if profile_updates:
                    reply = f"{_build_profile_saved_message(profile_updates)}\n\n{reply}"

            await ws.send_text(json.dumps({
                "type": "final",
                "conversation_id": conv_id,
                "message": reply,
            }))

    except WebSocketDisconnect:
        conversations.pop(conv_id, None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, log_level="info")