from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import Dict, Iterable, List

# Keep sentence-transformers in torch mode and avoid TF/Keras import conflicts.
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

from sentence_transformers import SentenceTransformer


def sliding_chunks(text: str, chunk_size: int = 512, overlap: int = 80) -> List[str]:
    tokens = text.split()
    if not tokens:
        return []
    if len(tokens) <= chunk_size:
        return [text.strip()]

    chunks: List[str] = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(tokens), step):
        window = tokens[i : i + chunk_size]
        if not window:
            continue
        chunks.append(" ".join(window).strip())
        if i + chunk_size >= len(tokens):
            break
    return chunks


def read_docs(path: str) -> Iterable[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def build_index(input_path: str, output_path: str, model_name: str, chunk_size: int, overlap: int) -> Dict[str, object]:
    model = SentenceTransformer(model_name)

    chunk_records: List[Dict[str, object]] = []
    for doc in read_docs(input_path):
        doc_id = doc.get("doc_id") or f"doc_{len(chunk_records) + 1}"
        city = doc.get("city", "")
        title = doc.get("title", "Untitled")
        source = doc.get("source", doc_id)
        text = doc.get("text", "").strip()
        if not text:
            continue

        parts = sliding_chunks(text, chunk_size=chunk_size, overlap=overlap)
        for i, part in enumerate(parts, start=1):
            chunk_records.append(
                {
                    "chunk_id": f"{doc_id}_chunk_{i}",
                    "doc_id": doc_id,
                    "city": city,
                    "title": title,
                    "source": source,
                    "text": part,
                }
            )

    if not chunk_records:
        raise RuntimeError("No chunks produced from input documents")

    embeddings = model.encode([c["text"] for c in chunk_records], normalize_embeddings=False)

    for record, vec in zip(chunk_records, embeddings):
        record["embedding"] = [float(x) for x in vec]

    payload = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "model": model_name,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "documents": len({c["doc_id"] for c in chunk_records}),
        "chunks": chunk_records,
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    return {"documents": payload["documents"], "chunks": len(chunk_records), "output": output_path}


def main():
    parser = argparse.ArgumentParser(description="Build local travel RAG index")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--input", default=os.path.join(base_dir, "documents", "travel_docs.jsonl"))
    parser.add_argument("--output", default=os.path.join(base_dir, "index", "travel_index.json"))
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=80)
    args = parser.parse_args()

    summary = build_index(
        input_path=args.input,
        output_path=args.output,
        model_name=args.model,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
