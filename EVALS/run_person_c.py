from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Allow running as a script: `python EVALS/run_person_c.py ...`
# by ensuring repo root is on sys.path so `import EVALS...` works.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from EVALS.performance.latency_bench import build_arg_parser as latency_parser
from EVALS.performance.latency_bench import main_async as latency_main_async
from EVALS.performance.throughput_bench import build_arg_parser as throughput_parser
from EVALS.performance.throughput_bench import main_async as throughput_main_async


async def run_all(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    lat_args = latency_parser().parse_args([])
    lat_args.base_http = args.base_http
    lat_args.ws_url = args.ws_url
    lat_args.ollama_tags_url = args.ollama_tags_url
    lat_args.trials = args.trials
    lat_args.out_json = str(out_dir / "latency_report.json")
    lat_args.out_md = str(out_dir / "latency_report.md")
    lat_code = await latency_main_async(lat_args)

    thr_args = throughput_parser().parse_args([])
    thr_args.base_http = args.base_http
    thr_args.ws_url = args.ws_url
    thr_args.levels = args.levels
    thr_args.turns_per_user = args.turns_per_user
    thr_args.out_json = str(out_dir / "throughput_report.json")
    thr_args.out_md = str(out_dir / "throughput_report.md")
    thr_code = await throughput_main_async(thr_args)

    return 0 if (lat_code == 0 and thr_code == 0) else 2


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run Person C performance evals (latency + throughput)")
    p.add_argument("--base-http", default="http://localhost:8000")
    p.add_argument("--ws-url", default="ws://localhost:8000/ws/chat")
    p.add_argument("--ollama-tags-url", default="http://localhost:11434/api/tags")
    p.add_argument("--trials", type=int, default=30)
    p.add_argument("--levels", type=int, nargs="+", default=[1, 2, 4, 6, 8])
    p.add_argument("--turns-per-user", type=int, default=3)
    p.add_argument("--out-dir", default="./outputs")
    return p


def main() -> None:
    args = build_arg_parser().parse_args()
    raise SystemExit(asyncio.run(run_all(args)))


if __name__ == "__main__":
    main()
