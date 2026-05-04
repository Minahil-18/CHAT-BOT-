from __future__ import annotations

import argparse
import asyncio
import time
from typing import Any, Dict, List

import httpx

from ..utils.hardware import get_hardware_info
from ..utils.reporting import md_kv_table, write_json, write_markdown
from ..utils.stats import summarize
from .ws_metrics import measure_single_turn


async def _is_http_up(url: str, timeout_s: float = 2.0) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.get(url)
            return r.status_code == 200
    except Exception:
        return False


async def _simulate_user(ws_url: str, user_id: str, city: str, messages: List[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in messages:
        out.append(await measure_single_turn(ws_url=ws_url, message=m, user_id=user_id, city=city, timeout_s=120.0))
        await asyncio.sleep(0.05)
    return out


async def _run_level(ws_url: str, concurrency: int, turns_per_user: int) -> Dict[str, Any]:
    # Keep messages tool-only by default (doesn't require Ollama), so throughput tests can run on machines
    # where Ollama is down, while still exercising WS streaming and tool execution.
    messages = [
        "What's the weather in Dubai right now?",
        "What's the weather in Tokyo right now?",
        "What's the weather in Paris right now?",
        "What's the weather in Bangkok right now?",
        "What's the weather in Istanbul right now?",
    ][: max(1, turns_per_user)]

    t0 = time.perf_counter()
    all_results = await asyncio.gather(
        *[
            _simulate_user(ws_url, f"load-u{i}", city="Dubai", messages=messages)
            for i in range(concurrency)
        ],
        return_exceptions=True,
    )
    t1 = time.perf_counter()

    flat: List[Dict[str, Any]] = []
    errors = 0
    for r in all_results:
        if isinstance(r, Exception):
            errors += 1
            continue
        for turn in r:
            flat.append(turn)
            if not turn.get("ok"):
                errors += 1

    ok = [x for x in flat if x.get("ok")]
    ttft = [x["ttft_ms"] for x in ok if x.get("ttft_ms") is not None]
    e2e = [x["e2e_ms"] for x in ok if x.get("e2e_ms") is not None]

    duration_s = max(1e-6, t1 - t0)
    turns_total = len(flat)
    turns_per_second = turns_total / duration_s

    return {
        "concurrency": concurrency,
        "turns_total": turns_total,
        "duration_s": round(duration_s, 3),
        "turns_per_second": round(turns_per_second, 3),
        "errors": errors,
        "ttft_ms": summarize(ttft),
        "e2e_ms": summarize(e2e),
    }


async def main_async(args: argparse.Namespace) -> int:
    base_http = args.base_http.rstrip("/")
    ws_url = args.ws_url
    health_url = f"{base_http}/healthz"

    server_up = await _is_http_up(health_url)
    report: Dict[str, Any] = {
        "title": "Person C - Throughput Benchmark",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoints": {"healthz": health_url, "ws_url": ws_url},
        "hardware": get_hardware_info(),
        "thresholds": {
            "median_ttft_ms_lt": args.target_median_ttft_ms,
            "median_e2e_ms_lt": args.target_median_e2e_ms,
            "max_error_rate": args.target_error_rate,
        },
        "levels": args.levels,
        "turns_per_user": args.turns_per_user,
        "results": [],
        "status": "ok" if server_up else "skipped",
        "skip_reason": None if server_up else "chatbot_server_not_running_or_unreachable",
        "max_sustainable_concurrency": None,
        "breakpoint_concurrency": None,
    }

    if not server_up:
        write_json(args.out_json, report)
        write_markdown(args.out_md, _render_md(report))
        return 2

    max_sustainable = None
    breakpoint = None

    for lvl in args.levels:
        r = await _run_level(ws_url, lvl, args.turns_per_user)
        report["results"].append(r)

        median_ttft = (r.get("ttft_ms") or {}).get("median")
        median_e2e = (r.get("e2e_ms") or {}).get("median")
        error_rate = (r.get("errors", 0) / max(1, r.get("turns_total", 1)))

        ok = True
        if median_ttft is not None and median_ttft > args.target_median_ttft_ms:
            ok = False
        if median_e2e is not None and median_e2e > args.target_median_e2e_ms:
            ok = False
        if error_rate > args.target_error_rate:
            ok = False

        if ok:
            max_sustainable = lvl
        elif breakpoint is None:
            breakpoint = lvl

    report["max_sustainable_concurrency"] = max_sustainable
    report["breakpoint_concurrency"] = breakpoint

    write_json(args.out_json, report)
    write_markdown(args.out_md, _render_md(report))
    return 0


def _render_md(report: Dict[str, Any]) -> str:
    lines: List[str] = ["# Person C - Throughput Benchmark", ""]
    lines.append(md_kv_table("Status", {
        "status": report.get("status"),
        "skip_reason": report.get("skip_reason", "-"),
        "max_sustainable_concurrency": report.get("max_sustainable_concurrency"),
        "breakpoint_concurrency": report.get("breakpoint_concurrency"),
    }))
    lines.append(md_kv_table("Hardware", report.get("hardware", {})))

    lines.append("## Results")
    lines.append("")
    lines.append("| Concurrency | Turns/s | Errors | Median TTFT (ms) | Median E2E (ms) |")
    lines.append("|---:|---:|---:|---:|---:|")
    for r in report.get("results", []):
        ttft_med = (r.get("ttft_ms") or {}).get("median")
        e2e_med = (r.get("e2e_ms") or {}).get("median")
        lines.append(
            f"| {r.get('concurrency')} | {r.get('turns_per_second')} | {r.get('errors')} | {ttft_med} | {e2e_med} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Person C throughput benchmark over WebSocket")
    p.add_argument("--base-http", default="http://localhost:8000")
    p.add_argument("--ws-url", default="ws://localhost:8000/ws/chat")
    p.add_argument("--levels", type=int, nargs="+", default=[1, 2, 4, 6, 8])
    p.add_argument("--turns-per-user", type=int, default=3)
    p.add_argument("--target-median-ttft-ms", type=float, default=2000.0)
    p.add_argument("--target-median-e2e-ms", type=float, default=10000.0)
    p.add_argument("--target-error-rate", type=float, default=0.01)
    p.add_argument("--out-json", default="./outputs/throughput_report.json")
    p.add_argument("--out-md", default="./outputs/throughput_report.md")
    return p


def main() -> None:
    args = build_arg_parser().parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
