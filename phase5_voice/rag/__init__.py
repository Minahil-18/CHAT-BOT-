"""RAG package for the voice travel assistant.

This module provides Retrieval-Augmented Generation capabilities:
- LocalVectorRetriever: Loads and searches the travel knowledge vector index
- RetrievedChunk: Data structure for retrieved document chunks
- build_index: Offline pipeline to build the vector index from source documents

Usage:
    from rag.retriever import LocalVectorRetriever
    
    retriever = LocalVectorRetriever(index_path="rag/index/travel_index.json")
    if retriever.load():
        results = retriever.retrieve("Tell me about Paris", top_k=3)
        prompt_text, sources = retriever.format_for_prompt(results)
"""

from rag.retriever import LocalVectorRetriever, RetrievedChunk

__all__ = ["LocalVectorRetriever", "RetrievedChunk"]
__version__ = "1.0.0"
