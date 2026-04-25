# Assignment 03 — Voice Conversational AI — Session Context

## Assignment Objective
Build a low-latency, production-style voice conversational AI system that:
- Runs on a laptop using quantized open-weights LLM, ASR and TTS in a pipeline
- Supports real-time streaming interaction (<1s latency target)
- Maintains conversation state (carried over from Assignment 02)
- Handles concurrent users (up to 4)
- Exposes a clean API
- Provides a ChatGPT-style web interface for chat and voice

## What Was Assignment 02?
- A travel chatbot (Travel Buddy) using **qwen2.5:1.5b via Ollama**
- FastAPI WebSocket backend with ConversationMemory, City Knowledge Base (9 cities)
- Beautiful web UI with BG.png background, Poppins font, clouds, animated plane
- Files: `phase4_microservice/app.py`, `phase4_microservice/index.html`
- The notebook `assignment2.ipynb` contains the original chatbot code

## Project Structure
```
Assignment 03/
├── assignment2.ipynb          # Previous assignment (reference only)
├── assignment_03.ipynb        # Main notebook — 7 phases of voice AI
├── BG.png                     # Background image used by both UIs
├── phase4_microservice/       # Assignment 02 text-only microservice (reference)
│   ├── app.py
│   └── index.html
└── phase5_voice/              # Assignment 03 voice microservice (ACTIVE)
    ├── app_voice.py           # FastAPI server — THE MAIN BACKEND
    ├── index_voice.html       # Voice-enabled web UI — THE MAIN FRONTEND
    ├── requirements.txt       # Python dependencies
    └── test_tts.py            # Debug script (can be deleted)
```

## Technology Stack
| Component | Tech | Details |
|-----------|------|---------|
| **ASR** | Moonshine tiny (Keras) | Package: `useful-moonshine`. Import: `from moonshine import load_model, ASSETS_DIR`. Expects 16kHz float32 audio. ~26MB model. |
| **LLM** | qwen2.5:1.5b via Ollama | Runs at `http://localhost:11434`. Must have Ollama running + model pulled. |
| **TTS** | Kokoro ONNX v1.0 int8 | Package: `kokoro-onnx`. Files cached at `~/.cache/kokoro_onnx/`. Outputs 24kHz float32. **First call is SLOW (~14s)** due to ONNX graph compilation; subsequent calls are fast. |
| **Backend** | FastAPI + Uvicorn | WebSocket streaming for chat, REST for ASR/TTS |
| **Frontend** | Single HTML file | Web Audio API for TTS playback, MediaRecorder for mic |

## How to Run
1. Make sure **Ollama is running** with qwen2.5:1.5b pulled
2. `cd phase5_voice`
3. `python app_voice.py`
4. Open `http://localhost:8000`

## Key Files & What Controls What

### `app_voice.py` — Backend Server
- **Lines 17-21**: Config — Ollama URL, model name, max tokens, concurrency limit
- **Lines 27-42**: City knowledge base (9 cities with activities, foods, seasons)
- **Lines 45-66**: `ConversationMemory` class + `build_system_prompt()` — maintains chat history
- **Lines 68-85**: ASR loading — Moonshine model + tokenizer, `transcribe_audio()` function
- **Lines 87-109**: TTS loading — Kokoro model download/load, `synthesize_text()` function
- **Lines 111-123**: `stream_ollama_tokens()` — async generator for LLM streaming
- **Lines 126-140**: FastAPI app setup, CORS, routes for `/` (UI), `/BG.png` (background)
- **Lines 142-155**: `/healthz` and `/api/test-tts` endpoints
- **Lines 157-167**: `POST /api/transcribe` — receives WAV audio, returns transcribed text
- **Lines 169-189**: `POST /api/synthesize` — receives text, returns WAV audio (float32→int16 conversion)
- **Lines 191-222**: `WebSocket /ws/chat` — handles chat with streaming tokens + conversation memory
- ASR and TTS run in thread pool via `run_in_executor()` to not block async loop
- `asyncio.Semaphore(4)` limits concurrent voice requests

### `index_voice.html` — Frontend UI
- **Design**: Matches Assignment 02 — BG.png background, Poppins font, floating clouds, animated plane, chat card with avatars
- **Mic recording** (click-to-toggle): Click 🎙 to start recording, click again to stop. Records WebM → converts to 16kHz WAV via AudioContext → sends to `/api/transcribe` → auto-sends transcribed text as chat message
- **Voice output** (ON by default): When bot response finishes (`final` frame), calls `/api/synthesize` with truncated text (first ~800 chars) → plays via Web Audio API (`AudioContext.decodeAudioData` + `BufferSource`)
- **Voice toggle**: Bottom bar "Voice On/Off" button
- **City chips**: Click to set destination context
- **WebSocket chat**: Connects to `/ws/chat`, streams tokens into bubble with typing cursor

### `assignment_03.ipynb` — Notebook (7 Phases)
- **Phase 1**: Install deps, load Moonshine + Kokoro + Ollama, smoke test
- **Phase 2**: `transcribe_audio()` with auto-resample, `vad_trim()`, ASR benchmarks
- **Phase 3**: `synthesize_speech()`, `synthesize_streaming()`, TTS benchmarks
- **Phase 4**: End-to-end `voice_pipeline()` combining ASR→LLM→TTS with TTFT/TTFA metrics
- **Phase 5**: Cell that generates `app_voice.py` (NOTE: standalone file may be newer than notebook cell)
- **Phase 6**: Cell that generates `index_voice.html` (NOTE: standalone file may be newer than notebook cell)
- **Phase 7**: Latency benchmarks, 4-user stress test, failure handling, scorecard

## Known Issues & Gotchas
1. **First TTS call is slow (~14s)** — ONNX graph compilation on first `Kokoro.create()`. Subsequent calls are fast (~1-3s depending on text length).
2. **TTS speed scales linearly with text length** — 800 chars takes ~4x longer than 200 chars. Currently truncated to 800 chars for voice output.
3. **Sample rate mismatch** — Kokoro outputs 24kHz, Moonshine needs 16kHz. Server handles resampling via `scipy.signal.resample`.
4. **Jupyter async** — `asyncio.run()` fails in Jupyter. Notebook cells use `await` directly.
5. **Browser autoplay policy** — Voice playback uses Web Audio API with AudioContext unlocked on user click.
6. **Notebook cells for Phase 5/6 may be outdated** — The standalone `app_voice.py` and `index_voice.html` files have been updated multiple times since the notebook cells generated them. If you re-run those notebook cells, they will overwrite the fixes.

## What's Been Completed
- [x] Phase 1: Model loading (ASR + TTS + LLM)
- [x] Phase 2: ASR pipeline with resampling
- [x] Phase 3: TTS pipeline
- [x] Phase 4: End-to-end voice pipeline
- [x] Phase 5: FastAPI microservice with all endpoints
- [x] Phase 6: Voice-enabled web UI with Assignment 02 design
- [x] Phase 7: Benchmarks and evaluation cells in notebook
- [x] Mic input working (click-to-toggle, noise suppression, echo cancellation)
- [x] Voice output working (Web Audio API, truncated to 800 chars)
- [x] BG.png background served and displayed
- [x] Conversation memory and city knowledge base

## Possible Next Steps
- Reduce TTS truncation limit (e.g., 400 chars) for faster voice responses
- Update notebook Phase 5/6 cells to match current standalone files
- Delete `test_tts.py` debug file
- Performance tuning / latency optimization
