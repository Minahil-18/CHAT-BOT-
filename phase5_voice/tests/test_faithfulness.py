import asyncio
import json
import os
import uuid
import websockets
import httpx
from typing import List, Dict, Any

# ── Configurations ──────────────────────────────────────────────────────────
WS_URL = "ws://localhost:8000/ws/chat"
OLLAMA_URL = "http://localhost:11434/api/chat"
JUDGE_MODEL = "qwen2.5:3b"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
QUERIES_PATH = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "EVALS", "test_data", "FAITHFULNESS_QUERIES.JSON")
REPORT_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "reports", "faithfulness_report.json")

async def get_chatbot_response(query: str, city: str) -> str:
    try:
        async with websockets.connect(WS_URL) as ws:
            await ws.recv() # hello
            await ws.send(json.dumps({"message": query, "user_id": "eval-faith", "city": city}))
            while True:
                resp = json.loads(await ws.recv())
                if resp["type"] == "final":
                    return resp["message"]
    except Exception as e:
        return f"ERROR: {e}"

async def judge_faithfulness(query: str, expected_fact: str, actual_answer: str) -> bool:
    prompt = f"""You are a strict fact-checker. 
Check if the 'Actual Answer' is faithful to the 'Expected Fact'. 
The 'Actual Answer' doesn't have to be identical, but it must contain the specific factual information mentioned in the 'Expected Fact'.

Expected Fact: {expected_fact}
Actual Answer: {actual_answer}

Respond ONLY in this JSON format:
{{"is_faithful": true/false, "reason": "brief explanation"}}"""

    payload = {
        "model": JUDGE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(OLLAMA_URL, json=payload)
            data = resp.json()
            result = json.loads(data["message"]["content"])
            return result.get("is_faithful", False)
    except:
        return False

async def main():
    print("🧪 Starting Faithfulness Evaluation (30 QA pairs)...")
    
    if not os.path.exists(QUERIES_PATH):
        print(f"Error: {QUERIES_PATH} not found.")
        return

    with open(QUERIES_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)

    results = []
    faithful_count = 0

    for q in queries:
        print(f"Testing {q['query_id']}: {q['query']}...")
        
        # 1. Get response from bot
        bot_response = await get_chatbot_response(q["query"], q["city"])
        
        # 2. Judge faithfulness
        is_faithful = await judge_faithfulness(q["query"], q["expected_fact"], bot_response)
        
        if is_faithful:
            faithful_count += 1
            print("  ✅ Faithful")
        else:
            print("  ❌ Unfaithful/Hallucinated")

        results.append({
            "query_id": q["query_id"],
            "query": q["query"],
            "expected_fact": q["expected_fact"],
            "bot_response": bot_response,
            "is_faithful": is_faithful
        })
        
        await asyncio.sleep(0.5)

    # Summary
    score = (faithful_count / len(queries)) * 100
    report = {
        "summary": {
            "total_queries": len(queries),
            "faithful_answers": faithful_count,
            "faithfulness_score_percent": round(score, 2)
        },
        "details": results
    }

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "="*60)
    print("FAITHFULNESS EVALUATION COMPLETE")
    print("="*60)
    print(f"Final Score: {score:.1f}%")
    print(f"Report saved to: {REPORT_PATH}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
