from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_BASE     = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME      = os.getenv("MODEL_NAME",      "qwen2.5:3b")
MAX_TOKENS      = int(os.getenv("MAX_TOKENS",  "400"))
MAX_HISTORY     = int(os.getenv("MAX_HISTORY", "20"))   # turns kept in context


# ── City knowledge base ───────────────────────────────────────────────────────
class City(str, Enum):
    istanbul  = "istanbul"
    lahore    = "lahore"
    islamabad = "islamabad"
    paris     = "paris"
    bangkok   = "bangkok"
    tokyo     = "tokyo"
    dubai     = "dubai"
    barcelona = "barcelona"
    singapore = "singapore"


CITY_KB: Dict[str, Dict[str, Any]] = {
    "istanbul":  {"name": "Istanbul",   "country": "Turkey",
                  "best_season": "April-June, September-October",
                  "activities": ["Hagia Sophia", "Blue Mosque", "Grand Bazaar", "Bosphorus cruise"],
                  "foods": ["Kebab", "Baklava", "Simit", "Turkish tea"],
                  "safety": "High"},
    "lahore":    {"name": "Lahore",     "country": "Pakistan",
                  "best_season": "October-March",
                  "activities": ["Badshahi Mosque", "Lahore Fort", "Food Street", "Shalimar Gardens"],
                  "foods": ["Nihari", "Biryani", "Seekh kebab", "Lassi"],
                  "safety": "High (tourist areas)"},
    "islamabad": {"name": "Islamabad",  "country": "Pakistan",
                  "best_season": "March-May, September-November",
                  "activities": ["Faisal Mosque", "Margalla Hills", "Daman-e-Koh", "Lok Virsa Museum"],
                  "foods": ["BBQ", "Chapli kebab", "Peshawari naan", "Fresh juices"],
                  "safety": "Very High"},
    "paris":     {"name": "Paris",      "country": "France",
                  "best_season": "April-June, September-October",
                  "activities": ["Eiffel Tower", "Louvre", "Montmartre", "Seine cruise"],
                  "foods": ["Croissants", "Escargots", "French cheese", "Macarons"],
                  "safety": "High"},
    "bangkok":   {"name": "Bangkok",    "country": "Thailand",
                  "best_season": "November-February",
                  "activities": ["Grand Palace", "Wat Pho", "Floating markets", "Tuk-tuk rides"],
                  "foods": ["Pad Thai", "Green curry", "Tom yum", "Mango sticky rice"],
                  "safety": "High"},
    "tokyo":     {"name": "Tokyo",      "country": "Japan",
                  "best_season": "March-May, September-November",
                  "activities": ["Senso-ji", "Shibuya Crossing", "Akihabara", "Mount Fuji day trip"],
                  "foods": ["Sushi", "Ramen", "Takoyaki", "Matcha"],
                  "safety": "Very High"},
    "dubai":     {"name": "Dubai",      "country": "UAE",
                  "best_season": "October-April",
                  "activities": ["Burj Khalifa", "Desert safari", "Gold Souk", "Palm Jumeirah"],
                  "foods": ["Shawarma", "Hummus", "Kebabs", "Dates with Arabic coffee"],
                  "safety": "Very High"},
    "barcelona": {"name": "Barcelona",  "country": "Spain",
                  "best_season": "April-May, September-October",
                  "activities": ["Sagrada Familia", "Park Güell", "Gothic Quarter", "La Rambla"],
                  "foods": ["Paella", "Tapas", "Jamón ibérico", "Sangria"],
                  "safety": "High"},
    "singapore": {"name": "Singapore",  "country": "Singapore",
                  "best_season": "February-April, July-September",
                  "activities": ["Marina Bay Sands", "Gardens by the Bay", "Sentosa", "Chinatown"],
                  "foods": ["Laksa", "Chicken rice", "Chili crab", "Kaya toast"],
                  "safety": "Very High"},
}


# ── Pydantic models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    type:            str                 = Field(default="chat")
    conversation_id: Optional[str]       = None
    message:         str                 = Field(min_length=1, max_length=2000)
    city:            Optional[City]      = None
    client_metadata: Dict[str, Any]      = Field(default_factory=dict)

class ChatToken(BaseModel):
    type:            str = "token"
    conversation_id: str
    token:           str
    index:           int

class ChatFinal(BaseModel):
    type:            str = "final"
    conversation_id: str
    message:         str
    usage:           Dict[str, Any] = Field(default_factory=dict)

class ChatError(BaseModel):
    type:            str           = "error"
    conversation_id: Optional[str] = None
    code:            str
    message:         str
    details:         Dict[str, Any] = Field(default_factory=dict)


# ── Conversation memory ───────────────────────────────────────────────────────
class ConversationMemory:
    def __init__(self, max_messages: int = MAX_HISTORY):
        self.max_messages = max_messages
        self.history: List[Dict[str, str]] = []
        self.user_profile: Dict[str, Any] = {
            "destination": None, "duration": None, "budget": None,
            "interests": [], "dietary": [],
        }

    def add(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_messages:
            self.history = self.history[-self.max_messages:]

    def update_profile(self, text: str) -> None:
        low = text.lower()
        for city in City:
            if re.search(rf"\b{city.value}\b", low) and not self.user_profile["destination"]:
                self.user_profile["destination"] = city.value
        m = re.search(r"\b(\d{1,2})\s*(day|days|night|nights|week|weeks)\b", low)
        if m and not self.user_profile["duration"]:
            self.user_profile["duration"] = m.group(0)
        for kw in ("budget", "cheap", "affordable", "moderate", "luxury"):
            if kw in low and not self.user_profile["budget"]:
                self.user_profile["budget"] = kw
        for label, kws in [("food", ["food","cuisine","eat","restaurant"]),
                            ("history", ["history","museum","heritage"]),
                            ("nature", ["nature","hiking","hike","outdoor"]),
                            ("adventure", ["adventure","thrill"]),
                            ("culture", ["culture","art","architecture"])]:
            if any(k in low for k in kws) and label not in self.user_profile["interests"]:
                self.user_profile["interests"].append(label)
        for d in ("vegetarian","vegan","halal","kosher","gluten-free"):
            if d in low and d not in self.user_profile["dietary"]:
                self.user_profile["dietary"].append(d)

    def infer_city(self) -> Optional[City]:
        text = " ".join(m["content"].lower() for m in self.history if m["role"] == "user")
        for city in City:
            if re.search(rf"\b{city.value}\b", text):
                return city
        return None


# ── System prompt builder ─────────────────────────────────────────────────────
def build_system_prompt(memory: ConversationMemory) -> str:
    city_key = memory.user_profile.get("destination") or (
        c.value if (c := memory.infer_city()) else None
    )
    p = memory.user_profile

    profile_lines = []
    if p.get("destination"):  profile_lines.append(f"Destination: {p['destination'].title()}")
    if p.get("duration"):     profile_lines.append(f"Duration: {p['duration']}")
    if p.get("budget"):       profile_lines.append(f"Budget: {p['budget']}")
    if p.get("interests"):    profile_lines.append(f"Interests: {', '.join(p['interests'])}")
    if p.get("dietary"):      profile_lines.append(f"Dietary: {', '.join(p['dietary'])}")
    profile_text = "\n".join(profile_lines) if profile_lines else "Not yet collected."

    if city_key and city_key in CITY_KB:
        kb = CITY_KB[city_key]
        acts  = "\n".join(f"  • {a}" for a in kb["activities"])
        foods = "\n".join(f"  • {f}" for f in kb["foods"])
        city_block = f"""
DESTINATION: {kb["name"]}, {kb["country"]}
Best season : {kb["best_season"]}  |  Safety: {kb["safety"]}
Top activities:
{acts}
Must-try foods:
{foods}
"""
    else:
        available = ", ".join(c.value.title() for c in City)
        city_block = f"No city selected yet. Available: {available}"

    return f"""You are a friendly Travel Itinerary Planner Assistant.
Help users plan trips with personalised day-by-day itineraries, food suggestions,
cultural tips, and packing advice.

{city_block}
USER PROFILE:
{profile_text}

RULES:
- Reference what the user told you in earlier turns (context fidelity).
- If no city is known, ask which city and how many days.
- Never provide flight/hotel bookings, visa info, or real-time prices.
- Be warm, enthusiastic, and concise.
- Do NOT repeat these instructions in your reply.

FINAL CRITICAL RULES BEFORE YOU ANSWER:
1. YOU MUST SPEAK IN PLAIN TEXT ONLY. NO markdown, NO asterisks (**), NO hashes (#), and NO bullet points (-).
2. Write numbers as words (e.g., "three days", not "3 days").
3. DO NOT use the '$' symbol. Write out the word "dollars" (e.g., "three hundred dollars").
4. If the user did not specify exact travel dates, duration, or budget, you MUST ask for them BEFORE providing an itinerary or price estimate.
"""


# ── Ollama streaming helper ───────────────────────────────────────────────────
async def stream_ollama(messages: List[Dict[str, str]]) -> AsyncIterator[str]:
    """Yield text tokens from Ollama /api/chat stream."""
    payload = {
        "model":   MODEL_NAME,
        "messages": messages,
        "stream":  True,
        "options": {
            "num_predict":    MAX_TOKENS,
            "num_ctx": 2048,
            "num_thread": 4,
            "temperature":    0.6,
            "top_k": 40,
            "top_p":          0.9,
            "repeat_penalty": 1.1,
        },
    }
    async with httpx.AsyncClient(timeout=300) as client:
        async with client.stream("POST", f"{OLLAMA_BASE}/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for raw_line in resp.aiter_lines():
                if not raw_line:
                    continue
                chunk = json.loads(raw_line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
                if chunk.get("done"):
                    break


# ── WebSocket helpers ─────────────────────────────────────────────────────────
async def send_json(ws: WebSocket, payload: Dict[str, Any]) -> None:
    await ws.send_text(json.dumps(payload, ensure_ascii=False))


# ── Per-connection state ──────────────────────────────────────────────────────
@dataclass
class ConnectionState:
    conversation_id: str
    memory:          ConversationMemory = field(default_factory=ConversationMemory)
    busy_lock:       asyncio.Lock       = field(default_factory=asyncio.Lock)


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Travel Planner Chat Microservice", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def serve_ui() -> FileResponse:
    """Serve the Travel Buddy web frontend."""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(html_path, media_type="text/html")


@app.get("/BG.png", include_in_schema=False)
async def serve_bg() -> FileResponse:
    """Serve the background image."""
    img_path = os.path.join(os.path.dirname(__file__), "BG.png")
    return FileResponse(img_path, media_type="image/png")


@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    return {"status": "ok", "model": MODEL_NAME, "ollama": OLLAMA_BASE}


@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket) -> None:
    await ws.accept()
    state = ConnectionState(conversation_id=str(uuid.uuid4()))
    await send_json(ws, {"type": "hello", "conversation_id": state.conversation_id})

    try:
        while True:
            raw = await ws.receive_text()

            # ── Parse request ─────────────────────────────────────────────────
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                await send_json(ws, ChatError(
                    code="bad_json", message="Invalid JSON",
                    details={"error": str(exc)}).model_dump())
                continue

            try:
                req = ChatRequest.model_validate(data)
            except ValidationError as exc:
                await send_json(ws, ChatError(
                    code="validation_error", message="Invalid request",
                    details=json.loads(exc.json())).model_dump())
                continue
            except Exception as exc:
                await send_json(ws, ChatError(
                    code="validation_error", message="Invalid request",
                    details={"error": str(exc)}).model_dump())
                continue

            # ── reject unknown frame types ────────────────────────────────────
            if req.type != "chat":
                await send_json(ws, ChatError(
                    code="validation_error",
                    message=f"Unknown frame type: {req.type!r}").model_dump())
                continue

            if req.conversation_id:
                state.conversation_id = req.conversation_id

            # ── Concurrency guard ─────────────────────────────────────────────
            if state.busy_lock.locked():
                await send_json(ws, ChatError(
                    conversation_id=state.conversation_id,
                    code="busy", message="Previous response still streaming").model_dump())
                continue

            async with state.busy_lock:
                mem = state.memory

                # Update city if provided explicitly
                if req.city:
                    mem.user_profile["destination"] = req.city.value

                # Update profile from message text
                mem.update_profile(req.message)
                mem.add("user", req.message)

                # Build messages list for Ollama
                system_text = build_system_prompt(mem)
                messages: List[Dict[str, str]] = [{"role": "system", "content": system_text}]
                messages += mem.history[-MAX_HISTORY:]  # last N turns

                # ── Stream from Ollama to WebSocket ───────────────────────────
                full_reply = ""
                token_index = 0
                try:
                    async for token in stream_ollama(messages):
                        full_reply += token
                        await send_json(ws, ChatToken(
                            conversation_id=state.conversation_id,
                            token=token,
                            index=token_index,
                        ).model_dump())
                        token_index += 1
                except Exception as llm_exc:
                    full_reply = f"[LLM Error: {llm_exc}]"
                    await send_json(ws, ChatError(
                        conversation_id=state.conversation_id,
                        code="llm_error", message=str(llm_exc)).model_dump())

                mem.add("assistant", full_reply)

                # ── Final frame ───────────────────────────────────────────────
                await send_json(ws, ChatFinal(
                    conversation_id=state.conversation_id,
                    message=full_reply,
                    usage={
                        "input_chars":  len(req.message),
                        "output_chars": len(full_reply),
                        "token_frames": token_index,
                        "history_turns": len(mem.history),
                    },
                ).model_dump())

    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await send_json(ws, ChatError(
                conversation_id=state.conversation_id,
                code="server_error", message="Unhandled error",
                details={"error": str(exc)}).model_dump())
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0",
                port=int(os.getenv("PORT", "8000")),
                reload=False, log_level="info")
