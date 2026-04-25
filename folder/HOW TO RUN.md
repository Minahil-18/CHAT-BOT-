# Voice Travel Chatbot - Quick Start Guide

## 🚀 How to Run 


### Option 1: Double-click (Easiest)
Just double-click: **`START_CHATBOT.bat`**

It will:
- ✅ Check if Ollama is running (starts it if not)
- ✅ Start the voice chatbot server
- ✅ Show you the URL to open

### Option 2: Quick Start (If Ollama already running)
Double-click: **`QUICK_START.bat`**
- Skips Ollama check
- Opens browser automatically
- Faster startup

### Option 3: Manual (If .bat files fail)
```bash
# Terminal 1: Start Ollama (if not running)
ollama serve

# Terminal 2: Start Chatbot
cd "phase5_voice"
py app_voice.py

# Open browser:
http://localhost:8000
```

---

## 🛠️ Troubleshooting

### "Ollama not found"
Install Ollama from: https://ollama.ai
Then pull the model:
```bash
ollama pull qwen2.5:1.5b
```

### "Python not found"
Make sure Python 3.11+ is installed and `py` command works

### "Module not found"
Reinstall dependencies:
```bash
cd phase5_voice
pip install -r requirements.txt
```

### Port 8000 already in use
Kill the process:
```bash
taskkill /F /IM python.exe
```

---

## 📋 System Overview

**Stack:**
- 🎤 **ASR**: Moonshine (speech-to-text)
- 🧠 **LLM**: Qwen 2.5 1.5B via Ollama
- 🔊 **TTS**: Piper (text-to-speech)
- 🌐 **Backend**: FastAPI + WebSocket
- 💻 **Frontend**: Single HTML file

**Features:**
- Voice input/output
- 16 travel destinations
- Smart memory (remembers preferences)
- Strict travel-only responses
- Real-time streaming chat

---

## 🌍 Available Destinations (16)

1. Istanbul, Turkey
2. Lahore, Pakistan
3. Islamabad, Pakistan
4. Paris, France
5. Bangkok, Thailand
6. Tokyo, Japan
7. Dubai, UAE
8. Barcelona, Spain
9. Singapore
10. New York City, USA
11. Hong Kong & Macao, China
12. Seoul, South Korea
13. Andros, Greece
14. Sri Lanka
15. Fraser Island, Australia
16. Rio de Janeiro, Brazil

---

## 📝 Notes

- First TTS call takes ~2-3 seconds (model loading)
- Subsequent calls are fast (~0.5s)
- Voice input: Click microphone, speak, click again
- Chatbot ONLY answers travel questions
- Memory: Keeps last 20 messages + key preferences

---

**Enjoy your voice travel assistant! ✈️🎤**
