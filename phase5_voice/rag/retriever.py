from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    city: str
    title: str
    source: str
    text: str
    score: float


class LocalVectorRetriever:
    """Loads a local JSON index and performs cosine-similarity retrieval."""

    def __init__(self, index_path: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.index_path = index_path
        self.model_name = model_name
        self._model = None
        self._metadata: List[Dict[str, str]] = []
        self._embeddings: Optional[np.ndarray] = None
        self._last_error: Optional[str] = None
        self._query_cache: Dict[str, List[RetrievedChunk]] = {}  # Add embedding cache

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    @property
    def is_ready(self) -> bool:
        return self._embeddings is not None and len(self._metadata) > 0

    @property
    def size(self) -> int:
        return len(self._metadata)

    def _load_model(self):
        if self._model is not None:
            return self._model
        # Force torch-only import path to avoid TensorFlow/Keras compatibility issues.
        os.environ.setdefault("USE_TF", "0")
        os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.model_name)
        return self._model

    def load(self) -> bool:
        if not os.path.isfile(self.index_path):
            self._last_error = f"Index file not found: {self.index_path}"
            return False

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            chunks = payload.get("chunks", [])
            if not chunks:
                self._last_error = "Index file has no chunks"
                return False

            self._metadata = [
                {
                    "chunk_id": c["chunk_id"],
                    "doc_id": c["doc_id"],
                    "city": c.get("city", ""),
                    "title": c.get("title", ""),
                    "source": c.get("source", ""),
                    "text": c["text"],
                }
                for c in chunks
            ]
            vectors = np.array([c["embedding"] for c in chunks], dtype=np.float32)
            # Keep vectors normalized once to make query-time retrieval fast.
            norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12
            self._embeddings = vectors / norms
            self._last_error = None
            return True
        except Exception as exc:
            self._metadata = []
            self._embeddings = None
            self._last_error = str(exc)
            return False

    def retrieve(self, query: str, city: Optional[str] = None, top_k: int = 4) -> List[RetrievedChunk]:
        if not self.is_ready:
            return []

        # Check cache first (for identical queries)
        cache_key = f"{query}|{city}|{top_k}"
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        model = self._load_model()
        query_vec = model.encode([query], normalize_embeddings=True)[0].astype(np.float32)
        scores = np.dot(self._embeddings, query_vec)

        # City-aware boost helps keep retrieval focused for itinerary queries.
        if city:
            city_lower = city.lower().strip()
            boost = np.array(
                [0.08 if m.get("city", "").lower() == city_lower else 0.0 for m in self._metadata],
                dtype=np.float32,
            )
            scores = scores + boost

        top_k = max(3, int(top_k))
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: List[RetrievedChunk] = []
        for idx in top_indices:
            meta = self._metadata[int(idx)]
            results.append(
                RetrievedChunk(
                    chunk_id=meta["chunk_id"],
                    doc_id=meta["doc_id"],
                    city=meta["city"],
                    title=meta["title"],
                    source=meta["source"],
                    text=meta["text"],
                    score=float(scores[int(idx)]),
                )
            )
        
        # Cache the results
        if len(self._query_cache) < 100:  # Limit cache size
            self._query_cache[cache_key] = results
        
        return results

    @staticmethod
    def format_for_prompt(chunks: List[RetrievedChunk], max_chars: int = 2800) -> Tuple[str, List[str]]:
        if not chunks:
            return "", []

        snippets: List[str] = []
        seen_sources: List[str] = []
        used = 0

        for i, chunk in enumerate(chunks, start=1):
            source_label = chunk.source or chunk.doc_id
            # Clean formatting: title on first line, text on next, minimal metadata
            line = (
                f"[{i}] {chunk.title}\n"
                f"{chunk.text.strip()}"
            )
            next_len = len(line) + 2
            if used + next_len > max_chars:
                break
            snippets.append(line)
            used += next_len
            if source_label not in seen_sources:
                seen_sources.append(source_label)

        return "\n\n".join(snippets), seen_sources
