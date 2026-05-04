from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_markdown(path: str | Path, markdown: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")


def md_kv_table(title: str, rows: Dict[str, Any]) -> str:
    lines = [f"## {title}", "", "| Key | Value |", "|---|---|"]
    for k, v in rows.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    return "\n".join(lines)
