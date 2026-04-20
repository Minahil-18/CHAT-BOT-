# RAG Module (Phase 1)

This folder contains the local Retrieval-Augmented Generation setup for the travel assistant.

## Contents
- `documents/travel_docs.jsonl` - source corpus (80 documents)
- `build_index.py` - offline, rerunnable indexing pipeline
- `retriever.py` - runtime retrieval and prompt formatting
- `index/travel_index.json` - generated vector index (created after running build step)

## Build Index
Run this from `phase5_voice`:

```bash
python rag/build_index.py
```

Optional parameters:

```bash
python rag/build_index.py --chunk-size 512 --overlap 80 --model sentence-transformers/all-MiniLM-L6-v2
```

## Runtime Environment Variables
- `RAG_ENABLED=true|false`
- `RAG_INDEX_PATH` (default: `rag/index/travel_index.json`)
- `RAG_TOP_K` (minimum enforced: 3)
- `RAG_MAX_CONTEXT_CHARS`

## Notes
If the index is missing, the chatbot automatically falls back to the legacy city knowledge base so voice chat still works.
