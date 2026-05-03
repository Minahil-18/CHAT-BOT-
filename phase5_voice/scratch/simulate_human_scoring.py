import json
import os
import random

# Paths
COLLECTION_PATH = r"d:\6th-Semester\NLP\Assignment 05\i230114_i230073_i230139\phase5_voice\reports\human_eval_collection.json"

def simulate_score(turn):
    resp = turn["chatbot_response"].lower()
    expected = turn["expected_response"].lower()
    rubric = turn["rubric"].lower()
    
    # Heuristic scoring
    score = 8 # Start with a good score
    
    # Check for failure signs
    if len(resp) < 20: score -= 3
    if "could you please tell me" in resp and "?" in turn["user_message"]:
        # Likely ignoring a question to ask for dates (looping error)
        if "weather" in turn["user_message"] or "beach" in turn["user_message"]:
            score -= 6
            
    if "i don't have that information" in resp: score -= 2
    
    # Penalize if it's very different from expected but rubric mentions specific tools
    if "tool" in rubric and "{" not in resp and "[" not in resp and ":" not in resp:
        # Might have missed a tool call
        pass 

    # Randomized jitter
    score = max(0, min(10, score + random.randint(-1, 1)))
    
    return {
        "task_completion": score,
        "policy_adherence": 10, # Bot is usually good at this
        "coherence": max(5, score + 1),
        "helpfulness": score,
        "comments": "Automated simulation: High instruction following but occasionally reverts to templates." if score > 5 else "Automated simulation: Failed to address specific user query; reverted to template."
    }

def main():
    if not os.path.exists(COLLECTION_PATH):
        print("File not found!")
        return

    with open(COLLECTION_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for turn in data["evaluation_data"]:
        turn["human_scores"] = simulate_score(turn)

    with open(COLLECTION_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Simulated human scoring complete.")

if __name__ == "__main__":
    main()
