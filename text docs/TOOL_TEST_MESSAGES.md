# 🧪 TOOL TRIGGERING TEST MESSAGES

Copy and paste these into WebSocket to test tool integration instantly.

---

## ✅ **FLIGHT SEARCH TESTS** (Search Flights Tool)

### Message 1: Direct Flight Search
```
"Search for flights from London to Bangkok for 2 passengers departing on June 15, 2026"
```
**Expected Tool**: `search_flights`
**Expected Result**: JSON with 2-3 flights, prices, times
**Look For**: `[TOOL START: search_flights]` → `[TOOL RESULT]` → Flight options in response

### Message 2: Multi-city Flight Search
```
"I need to book a flight from Paris to Tokyo for 4 people on July 1, 2026"
```
**Expected Tool**: `search_flights`
**Expected Result**: Flight options with pricing

### Message 3: Return Flight
```
"Find flights Istanbul to Dubai June 15 for 3 passengers"
```
**Expected Tool**: `search_flights`
**Expected Result**: Available flights

---

## 🌤️ **WEATHER TESTS** (Get Weather Tool)

### Message 4: Simple Weather Query
```
"What's the weather like in Bangkok?"
```
**Expected Tool**: `get_weather`
**Expected Result**: Temperature, humidity, conditions
**Look For**: `[TOOL START: get_weather]` → Temperature data

### Message 5: Weather for Travel Planning
```
"I'm visiting Tokyo next month. What's the weather going to be like?"
```
**Expected Tool**: `get_weather`
**Expected Result**: Weather information for Tokyo

### Message 6: Weather Comparison
```
"Tell me the weather in Dubai and Bangkok"
```
**Expected Tool**: `get_weather` (may call twice)
**Expected Result**: Weather for both cities

---

## 💰 **BUDGET CALCULATOR TESTS** (Calculate Trip Budget)

### Message 7: Simple Budget
```
"Calculate the budget for a 5-day trip to Tokyo with moderate spending"
```
**Expected Tool**: `calculate_trip_budget`
**Expected Result**: Total cost breakdown (accommodation, food, activities, flights)
**Look For**: `[TOOL START: calculate_trip_budget]` → Budget total in result

### Message 8: Luxury Trip Budget
```
"What would a 7-day luxury trip to Paris cost for 1 person?"
```
**Expected Tool**: `calculate_trip_budget`
**Expected Result**: High-end budget estimate

### Message 9: Budget Trip
```
"I want to visit Bangkok for 3 days on a budget. How much will it cost?"
```
**Expected Tool**: `calculate_trip_budget`
**Expected Result**: Budget option with total cost

---

## 🏨 **HOTEL SEARCH TESTS** (Search Hotels)

### Message 10: Luxury Hotel Search
```
"Find luxury hotels in Paris"
```
**Expected Tool**: `search_hotels`
**Expected Result**: Hotel options with ratings, prices
**Look For**: `[TOOL START: search_hotels]` → Hotel list with ratings

### Message 11: Budget Hotel Search
```
"Search for budget hotels in Bangkok"
```
**Expected Tool**: `search_hotels`
**Expected Result**: Affordable hotel options

### Message 12: Mid-range Hotels
```
"Show me moderate hotels in Tokyo"
```
**Expected Tool**: `search_hotels`
**Expected Result**: Mid-range hotel options

---

## 👤 **CRM TESTS** (User Profile Management)

### Message 13: Create User Profile
```
"Create a profile for me. Name is Alice, email is alice@example.com, and I'm interested in beaches and culture"
```
**Expected Tool**: `create_user`
**Expected Result**: User ID, confirmation of profile creation
**Look For**: `[TOOL START: create_user]` → Success confirmation

### Message 14: Get User Profile
```
"Show me my travel profile"
```
**Expected Tool**: `get_user`
**Expected Result**: User information and preferences

### Message 15: Update Preferences
```
"Update my preferences to include mountain trekking and adventure sports"
```
**Expected Tool**: `update_user`
**Expected Result**: Confirmation of updated preferences

### Message 16: Add Trip to History
```
"I just took a trip to Istanbul, add it to my travel history"
```
**Expected Tool**: `add_trip`
**Expected Result**: Trip added to profile

### Message 17: Get Trip History
```
"Show me all my past trips"
```
**Expected Tool**: `get_user_trips`
**Expected Result**: List of trips (may be empty initially)

---

## 🚀 **COMBO TESTS** (Multiple Tools Per Conversation)

### Message 18: Plan Complete Trip
```
"I want to visit Bangkok for 5 days starting June 15, 2026. What are the flights, budget, weather, and hotels there?"
```
**Expected Tools** (in sequence):
1. `search_flights` - Find flights
2. `calculate_trip_budget` - Cost estimate
3. `get_weather` - Weather info
4. `search_hotels` - Hotel options

**What to Watch**: Multiple tool calls, results injected, final response incorporates all data

### Message 19: Create Profile & Plan Trip
```
"My name is Bob, email bob@travel.com, interested in adventure. Now search for flights to Dubai on June 20, 2026 for 2 people"
```
**Expected Tools**:
1. `create_user` - Create Bob's profile
2. `search_flights` - Find Dubai flights

---

## ⚡ **QUICK VALIDATION TESTS**

### Minimal Test (Shortest Message)
```
"flights London Bangkok June 15 2 people 2026"
```
**Expected**: `search_flights` tool call

### Explicit Format Test
```
"[TOOL_CALL: search_flights {"from_city": "London", "to_city": "Bangkok", "departure_date": "2026-06-15", "passengers": 2}]"
```
**Expected**: Immediate tool execution (if LLM echoes this format)

### Weather Test (Simplest)
```
"weather Bangkok"
```
**Expected**: `get_weather` tool call

---

## 🔍 **HOW TO TEST**

### Option A: WebSocket Client (Browser Console)
```javascript
ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = () => console.log('Connected');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'token') {
    process.stdout.write(data.token);
  } else if (data.type === 'tool_start') {
    console.log('\n[TOOL START]', data.tool_name);
  } else if (data.type === 'tool_result') {
    console.log('[TOOL RESULT]', JSON.stringify(data.result, null, 2));
  } else if (data.type === 'final') {
    console.log('\n[FINAL]', data.message);
  }
};

// Send a test message
ws.send(JSON.stringify({
  message: "Search for flights from London to Bangkok for 2 passengers on June 15, 2026"
}));
```

### Option B: Python WebSocket Client
```python
import asyncio
import json
import websockets

async def test():
    uri = "ws://localhost:8000/ws/chat"
    async with websockets.connect(uri) as ws:
        # Wait for hello
        hello = await ws.recv()
        print(f"Connected: {hello}")
        
        # Send test message
        await ws.send(json.dumps({
            "message": "Search for flights from London to Bangkok for 2 passengers on June 15, 2026"
        }))
        
        # Receive responses
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            
            if data['type'] == 'tool_start':
                print(f"\n✅ TOOL DETECTED: {data['tool_name']}")
                print(f"   Args: {data['tool_args']}")
            
            elif data['type'] == 'tool_result':
                print(f"\n📊 TOOL RESULT:")
                print(f"   {json.dumps(data['result'], indent=2)[:200]}...")
            
            elif data['type'] == 'token':
                print(data['token'], end='', flush=True)
            
            elif data['type'] == 'final':
                print(f"\n\n✅ DONE")
                break

asyncio.run(test())
```

### Option C: Using wscat
```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws/chat
# Then type:
{"message": "Search for flights from London to Bangkok for 2 passengers on June 15, 2026"}
```

---

## 📊 **SUCCESS INDICATORS**

When you send a tool-triggering message, you should see:

✅ **In WebSocket Messages**:
```json
{"type": "tool_start", "tool_name": "search_flights", "tool_args": {...}}
{"type": "tool_result", "tool_name": "search_flights", "result": {...}}
```

✅ **In Console Logs** (app_voice.py):
```
[TOOLS] Detected tool: search_flights
[TOOLS] Executing: search_flights with args: {...}
```

✅ **In Final Response**:
- LLM mentions tool results
- Includes actual data from tool (e.g., "3 flights found")
- Natural integration into answer

---

## 🚨 **TROUBLESHOOTING**

### No tool detected?
- **Check**: LLM output format (might not be asking for tools)
- **Fix**: Try more explicit messages like "Find flights..."
- **Debug**: Check console for `[TOOLS]` logs

### Tool error?
- **Check**: Tool parameters match schema
- **Fix**: Ensure dates are in future (e.g., 2026-06-15)
- **Debug**: Look for `[TOOL ERROR]` in console

### No response?
- **Check**: App is running (`python app_voice.py`)
- **Check**: Ollama is running (`ollama serve`)
- **Fix**: Restart both services

---

## ✅ **VALIDATION CHECKLIST**

Test each category:
- [ ] **Flight Search** - Message 1 triggers search_flights
- [ ] **Weather** - Message 4 triggers get_weather
- [ ] **Budget** - Message 7 triggers calculate_trip_budget
- [ ] **Hotels** - Message 10 triggers search_hotels
- [ ] **CRM** - Message 13 triggers create_user
- [ ] **Combo** - Message 18 triggers multiple tools

Once all pass, tool integration is **VERIFIED AND WORKING** ✅

---

## 📝 **NOTES**

- All dates should be in future (2026-06 or later work)
- Cities available: London, Bangkok, Tokyo, Paris, Dubai, Istanbul, Singapore
- Passengers: 1-6 supported
- Budget levels: budget, moderate, luxury
- All operations are async (shouldn't block UI)

---

**Ready to test? Start with Message 1! 🚀**
