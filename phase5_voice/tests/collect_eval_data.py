import asyncio
import json
import os
import uuid
import websockets
from typing import List, Dict, Any

# ── Configurations ──────────────────────────────────────────────────────────
WS_URL = "ws://localhost:8000/ws/chat"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIALOGUES_PATH = os.path.join(SCRIPT_DIR, "data", "test_dialogues.json")
REPORT_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "reports")
COLLECTION_PATH = os.path.join(REPORT_DIR, "human_eval_collection.json")

# Ensure reports directory exists
os.makedirs(REPORT_DIR, exist_ok=True)

async def run_dialogue(dialogue: Dict[str, Any]) -> List[Dict[str, Any]]:
    dialogue_id = dialogue["dialogue_id"]
    turns = dialogue["turns"]
    user_id = f"human-eval-{dialogue_id}-{uuid.uuid4().hex[:4]}"
    
    collected_turns = []
    
    try:
        async with websockets.connect(WS_URL) as ws:
            # Wait for hello message
            await ws.recv()
            
            for i in range(len(turns)):
                turn = turns[i]
                if turn["role"] == "user":
                    user_msg = turn["content"]
                    
                    # Find ground truth/rubric
                    expected = ""
                    rubric = ""
                    if i + 1 < len(turns) and turns[i+1]["role"] == "expected_assistant":
                        expected = turns[i+1].get("content", "")
                        rubric = turns[i+1].get("rubric", "")
                    
                    # Send to chatbot
                    await ws.send(json.dumps({"message": user_msg, "user_id": user_id}))
                    
                    # Collect tokens
                    assistant_response = ""
                    while True:
                        resp_raw = await ws.recv()
                        resp = json.loads(resp_raw)
                        if resp["type"] == "final":
                            assistant_response = resp["message"]
                            break
                    
                    collected_turns.append({
                        "dialogue_id": dialogue_id,
                        "turn_index": i // 2,
                        "user_message": user_msg,
                        "chatbot_response": assistant_response,
                        "expected_response": expected,
                        "rubric": rubric,
                        "human_scores": {
                            "task_completion": None,
                            "policy_adherence": None,
                            "coherence": None,
                            "helpfulness": None,
                            "comments": ""
                        }
                    })
                    await asyncio.sleep(0.5)
                    
    except Exception as e:
        print(f"  [ERROR] Dialogue {dialogue_id} failed: {e}")
        
    return collected_turns

async def main():
    print("🚀 Starting Dialogue Collection for Human Evaluation...")
    
    if not os.path.exists(DIALOGUES_PATH):
        print(f"Error: {DIALOGUES_PATH} not found.")
        return

    with open(DIALOGUES_PATH, "r", encoding="utf-8") as f:
        dialogues = json.load(f)

    all_data = []
    
    for diag in dialogues:
        diag_id = diag["dialogue_id"]
        print(f"Running Dialogue {diag_id}: {diag['category']}...")
        
        turns_data = await run_dialogue(diag)
        all_data.extend(turns_data)
        
        await asyncio.sleep(1.0)

    # Save for human scoring
    output = {
        "metadata": {
            "total_turns": len(all_data),
            "instructions": "Evaluators should fill in scores (0-10) in the 'human_scores' fields."
        },
        "evaluation_data": all_data
    }

    with open(COLLECTION_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("\n" + "="*60)
    print("COLLECTION COMPLETE")
    print("="*60)
    print(f"Successfully collected {len(all_data)} turns.")
    print(f"File saved to: {COLLECTION_PATH}")
    print("You can now open this file and perform your manual human evaluation.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
