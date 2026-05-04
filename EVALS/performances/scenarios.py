from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    message: str
    city: Optional[str]
    requires_ollama: bool


SCENARIOS: List[Scenario] = [
    Scenario(
        name="tool_only",
        description="Single tool call (weather) with structured response (no LLM).",
        message="What is the weather in Paris right now?",
        city="Paris",
        requires_ollama=False,
    ),
    Scenario(
        name="rag_only",
        description="Knowledge retrieval for travel tips using RAG documents.",
        message="What are the essential items to pack for a winter trip to Islamabad?",
        city="Islamabad",
        requires_ollama=True,
    ),
    Scenario(
        name="rag_plus_tool",
        description="Combined RAG retrieval + tool call (e.g. food recommendations + weather).",
        message="Tell me about the food in Tokyo and what the weather is like today.",
        city="Tokyo",
        requires_ollama=True,
    ),
    Scenario(
        name="full_pipeline",
        description="Full itinerary request triggering RAG, tools, and narrative LLM generation.",
        message="Plan a detailed 3-day itinerary for Istanbul including flights, hotels, and budget.",
        city="Istanbul",
        requires_ollama=True,
    ),
]


def as_dict() -> List[Dict[str, Any]]:
    return [asdict(s) for s in SCENARIOS]
