from __future__ import annotations

import argparse
import asyncio
import time
from typing import Any, Dict, List

import httpx

from ..utils.hardware import get_hardware_info
from ..utils.reporting import md_kv_table, write_json, write_markdown
from ..utils.stats import summarize
from .scenarios import SCENARIOS, as_dict
from .ws_metrics import measure_single_turn


async def _is_http_up(url: str, timeout_s: float = 2.0) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.get(url)
            return r.status_code == 200
    except Exception:
        return False


async def _run_scenario(ws_url: str, scenario: Dict[str, Any], trials: int) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for i in range(trials):
        r = await measure_single_turn(
            ws_url=ws_url,
            message=scenario["message"],
            user_id=f"perf-{scenario['name']}-{i}",
            city=scenario.get("city"),
        )
        results.append(r)
        await asyncio.sleep(0.05)

    ok = [x for x in results if x.get("ok")]
    ttft = [x["ttft_ms"] for x in ok if x.get("ttft_ms") is not None]
    itl = [x["inter_token_ms_avg"] for x in ok if x.get("inter_token_ms_avg") is not None]
    e2e = [x["e2e_ms"] for x in ok if x.get("e2e_ms") is not None]

    return {
        "scenario": scenario,
        "trials": trials,
        "successes": len(ok),
        "failures": len(results) - len(ok),
        "ttft_ms": summarize(ttft),
        "inter_token_ms_avg": summarize(itl),
        "e2e_ms": summarize(e2e),
        "samples": results,
    }


async def main_async(args: argparse.Namespace) -> int:
    base_http = args.base_http.rstrip("/")
    ws_url = args.ws_url
    health_url = f"{base_http}/healthz"
    rag_status_url = f"{base_http}/api/rag/status"

    server_up = await _is_http_up(health_url)

    report: Dict[str, Any] = {
        "title": "Person C - Latency Benchmark",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "targets": {
            "median_ttft_ms_lt": args.target_median_ttft_ms,
            "median_e2e_ms_lt": args.target_median_e2e_ms,
        },
        "endpoints": {"healthz": health_url, "ws_url": ws_url, "rag_status": rag_status_url},
        "hardware": get_hardware_info(),
        "scenarios": as_dict(),
        "results": [],
        "status": "ok" if server_up else "skipped",
        "skip_reason": None if server_up else "chatbot_server_not_running_or_unreachable",
    }

    if not server_up:
        write_json(args.out_json, report)
        write_markdown(args.out_md, _render_md(report))
        return 2

    # Determine which scenarios to run based on Ollama availability.
    ollama_up = await _is_http_up(args.ollama_tags_url)
    report["ollama_up"] = ollama_up

    runnable = []
    for s in SCENARIOS:
        if s.requires_ollama and not ollama_up:
            continue
        runnable.append({"name": s.name, "description": s.description, "message": s.message, "city": s.city})
    report["runnable_scenarios"] = [x["name"] for x in runnable]
    report["skipped_scenarios"] = [s.name for s in SCENARIOS if s.requires_ollama and not ollama_up]

    for s in runnable:
        report["results"].append(await _run_scenario(ws_url, s, args.trials))

    write_json(args.out_json, report)
    write_markdown(args.out_md, _render_md(report))
    return 0


def _render_md(report: Dict[str, Any]) -> str:
    lines: List[str] = ["# Person C - Latency Benchmark", ""]
    lines.append(md_kv_table("Status", {
        "status": report.get("status"),
        "skip_reason": report.get("skip_reason", "-"),
        "ollama_up": report.get("ollama_up", "unknown"),
    }))
    hw = report.get("hardware", {})
    lines.append(md_kv_table("Hardware", hw))

    for r in report.get("results", []):
        s = r.get("scenario", {})
        lines.append(f"## Scenario: {s.get('name')}")
        lines.append("")
        lines.append(f"{s.get('description')}")
        lines.append("")
        lines.append(md_kv_table("Summary", {
            "trials": r.get("trials"),
            "successes": r.get("successes"),
            "failures": r.get("failures"),
        }))
        lines.append(md_kv_table("TTFT (ms)", r.get("ttft_ms", {})))
        lines.append(md_kv_table("Inter-token (ms)", r.get("inter_token_ms_avg", {})))
        lines.append(md_kv_table("E2E (ms)", r.get("e2e_ms", {})))

    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Person C latency benchmark over WebSocket")
    p.add_argument("--base-http", default="http://localhost:8000", help="Base HTTP URL for chatbot")
    p.add_argument("--ws-url", default="ws://localhost:8000/ws/chat", help="WebSocket URL")
    p.add_argument("--ollama-tags-url", default="http://localhost:11434/api/tags", help="Ollama tags endpoint")
    p.add_argument("--trials", type=int, default=30, help="Trials per scenario")
    p.add_argument("--target-median-ttft-ms", type=float, default=2000.0)
    p.add_argument("--target-median-e2e-ms", type=float, default=10000.0)
    p.add_argument("--out-json", default="./outputs/latency_report.json")
    p.add_argument("--out-md", default="./outputs/latency_report.md")
    return p


def main() -> None:
    args = build_arg_parser().parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
