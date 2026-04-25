import json
import os
import sys
import time
from collections import defaultdict

# Add the parent directory to sys.path so we can import rag.retriever
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from rag.retriever import LocalVectorRetriever

def main():
    # 1. Paths
    index_path = os.path.join(base_dir, "rag", "index", "travel_index.json")
    queries_path = os.path.join(base_dir, "..", "EVALS", "test_data", "RAG_QUERIES.JSON")
    reports_dir = os.path.join(base_dir, "reports")
    report_path = os.path.join(reports_dir, "rag_eval_report.json")

    os.makedirs(reports_dir, exist_ok=True)

    # 2. Load Retriever
    print(f"Loading retriever from {index_path}...")
    retriever = LocalVectorRetriever(index_path=index_path)
    if not retriever.load():
        print(f"Failed to load retriever: {retriever.last_error}")
        return
    print("Retriever loaded successfully.")

    retriever.retrieve("warmup query", None, 1)
    print("[WARMUP] done")

    # 3. Load Queries
    print(f"Loading queries from {queries_path}...")
    if not os.path.exists(queries_path):
        print("Queries file not found!")
        return

    with open(queries_path, "r", encoding="utf-8") as f:
        queries = json.load(f)

    results = []
    
    # Metrics grouped by difficulty
    diff_metrics = defaultdict(lambda: {
        "precision_sum": 0.0,
        "recall_sum": 0.0,
        "mrr_sum": 0.0,
        "khr_sum": 0.0,
        "latency_sum": 0.0,
        "count": 0
    })

    doc_type_keywords = {
        "overview":          ["guide_1", "overview", "intro", "general"],
        "food_guide":        ["food", "restaurant", "cuisine", "eat"],
        "activities_guide":  ["guide_2", "activities", "attraction", "things"],
        "visa_requirements": ["visa", "entry", "passport", "requirement"],
        "seasonal_guide":    ["season", "weather", "climate", "time", "guide_3"],
    }

    print("\n--- Running Evaluation ---")
    # 4. Evaluate each query
    for q in queries:
        q_id = q["query_id"]
        query_text = q["query"]
        city = q["city"]
        relevant_doc_types = q["relevant_doc_types"]
        expected_kws = q["expected_answer_contains"]
        diff = q["difficulty"]

        t0 = time.time()
        chunks = retriever.retrieve(query=query_text, city=city, top_k=3)
        t1 = time.time()
        latency_ms = (t1 - t0) * 1000

        # Precision@3
        relevant_chunks = 0
        first_relevant_rank = 0
        found_types = set()
        combined_text = ""

        for rank, chunk in enumerate(chunks, start=1):
            combined_text += chunk.text.lower() + " "
            chunk_identifier = (chunk.doc_id + " " + chunk.title).lower()
            
            is_relevant = False
            for rdt in relevant_doc_types:
                kws = doc_type_keywords.get(rdt, [rdt])
                if any(kw in chunk_identifier for kw in kws):
                    is_relevant = True
                    found_types.add(rdt)
                    
            if is_relevant:
                relevant_chunks += 1
                if first_relevant_rank == 0:
                    first_relevant_rank = rank

        precision = relevant_chunks / 3.0
        recall = len(found_types) / len(relevant_doc_types) if relevant_doc_types else 0.0
        mrr = 1.0 / first_relevant_rank if first_relevant_rank > 0 else 0.0

        # Keyword Hit Rate
        found_kws = 0
        for kw in expected_kws:
            if kw.lower() in combined_text:
                found_kws += 1
        khr = found_kws / len(expected_kws) if expected_kws else 0.0

        q_result = {
            "query_id": q_id,
            "query": query_text,
            "difficulty": diff,
            "precision_at_3": precision,
            "recall_at_3": recall,
            "mrr": mrr,
            "keyword_hit_rate": khr,
            "latency_ms": latency_ms
        }
        results.append(q_result)

        # Update difficulty aggregates
        dm = diff_metrics[diff]
        dm["precision_sum"] += precision
        dm["recall_sum"] += recall
        dm["mrr_sum"] += mrr
        dm["khr_sum"] += khr
        dm["latency_sum"] += latency_ms
        dm["count"] += 1

        # Determine pass/fail emoji (heuristic: at least 1 relevant doc found)
        emoji = "✅" if relevant_chunks > 0 else "❌"
        print(f"[{q_id}] {emoji} | Prec: {precision:.2f} | Rec: {recall:.2f} | MRR: {mrr:.2f} | KHR: {khr:.2f} | Latency: {latency_ms:.1f}ms")

    # 5. Print Summary Grouped by Difficulty
    print("\n--- Summary by Difficulty ---")
    summary = {}
    for diff, dm in diff_metrics.items():
        count = dm["count"]
        if count == 0: continue
        avg_prec = dm["precision_sum"] / count
        avg_recall = dm["recall_sum"] / count
        avg_mrr = dm["mrr_sum"] / count
        avg_khr = dm["khr_sum"] / count
        avg_lat = dm["latency_sum"] / count
        
        summary[diff] = {
            "count": count,
            "avg_precision_at_3": avg_prec,
            "avg_recall_at_3": avg_recall,
            "avg_mrr": avg_mrr,
            "avg_keyword_hit_rate": avg_khr,
            "avg_latency_ms": avg_lat
        }
        
        print(f"[{diff.upper()}] (n={count})")
        print(f"  Precision@3: {avg_prec:.2f}")
        print(f"  Recall@3:    {avg_recall:.2f}")
        print(f"  MRR:         {avg_mrr:.2f}")
        print(f"  Keyword Hit: {avg_khr:.2f}")
        print(f"  Latency:     {avg_lat:.1f}ms")

    # 6. Save Report
    full_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary_by_difficulty": summary,
        "query_results": results
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    print(f"\nReport saved successfully to: {report_path}")

if __name__ == "__main__":
    main()
