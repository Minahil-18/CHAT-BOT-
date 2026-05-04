from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


def _now() -> float:
    return time.perf_counter()


@dataclass
class TurnTimings:
    ok: bool
    error: Optional[str]
    connect_ms: Optional[float]
    ttft_ms: Optional[float]
    inter_token_ms_avg: Optional[float]
    e2e_ms: Optional[float]
    token_events: int
    final_message_chars: int
    debug: Dict[str, Any]


async def measure_turn_on_connection(
    ws: Any,
    *,
    payload: Dict[str, Any],
    timeout_s: float = 60.0,
) -> Dict[str, Any]:
    """Measure a single turn over an *already-connected* WebSocket.

    The timing starts right before sending the user payload.
    """

    t_send = _now()
    token_times: List[float] = []
    final_text = ""
    debug_obj: Dict[str, Any] = {}

    try:
        await ws.send(json.dumps(payload))

        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout_s)
            t_recv = _now()
            frame = json.loads(raw)
            ftype = frame.get("type")
            if ftype == "token":
                token_times.append(t_recv)
            elif ftype == "final":
                final_text = frame.get("message", "") or ""
                debug_obj = frame.get("debug", {}) or {}
                break
            else:
                # Ignore tool_start/tool_result/error/other frames for timing.
                continue
    except Exception as exc:
        return asdict(
            TurnTimings(
                ok=False,
                error=str(exc),
                connect_ms=None,
                ttft_ms=None,
                inter_token_ms_avg=None,
                e2e_ms=None,
                token_events=len(token_times),
                final_message_chars=len(final_text),
                debug=debug_obj,
            )
        )

    if not token_times:
        return asdict(
            TurnTimings(
                ok=False,
                error="no_token_events",
                connect_ms=None,
                ttft_ms=None,
                inter_token_ms_avg=None,
                e2e_ms=(_now() - t_send) * 1000,
                token_events=0,
                final_message_chars=len(final_text),
                debug=debug_obj,
            )
        )

    ttft_ms = (token_times[0] - t_send) * 1000
    e2e_ms = (_now() - t_send) * 1000

    if len(token_times) >= 2:
        deltas = [(token_times[i] - token_times[i - 1]) * 1000 for i in range(1, len(token_times))]
        inter_ms_avg = sum(deltas) / len(deltas)
    else:
        inter_ms_avg = None

    return asdict(
        TurnTimings(
            ok=True,
            error=None,
            connect_ms=None,
            ttft_ms=round(ttft_ms, 3),
            inter_token_ms_avg=round(inter_ms_avg, 3) if inter_ms_avg is not None else None,
            e2e_ms=round(e2e_ms, 3),
            token_events=len(token_times),
            final_message_chars=len(final_text),
            debug=debug_obj,
        )
    )


async def measure_single_turn(
    *,
    ws_url: str,
    message: str,
    user_id: str,
    city: Optional[str] = None,
    timeout_s: float = 60.0,
) -> Dict[str, Any]:
    """Measure TTFT / inter-token latency / end-to-end for a single chat turn.

    Assumes server speaks the `{"type":"hello"}` + streamed `token` frames + `final`.
    """

    try:
        import websockets  # type: ignore
    except Exception as exc:
        return asdict(
            TurnTimings(
                ok=False,
                error=f"websockets_not_installed: {exc}",
                ttft_ms=None,
                inter_token_ms_avg=None,
                e2e_ms=None,
                token_events=0,
                final_message_chars=0,
                debug={},
            )
        )

    t_connect0 = _now()
    connect_ms: Optional[float] = None

    try:
        async with websockets.connect(ws_url, ping_interval=None, close_timeout=2) as ws:
            # hello
            await asyncio.wait_for(ws.recv(), timeout=timeout_s)

            connect_ms = (_now() - t_connect0) * 1000

            payload: Dict[str, Any] = {"message": message, "user_id": user_id}
            if city:
                payload["city"] = city
            out = await measure_turn_on_connection(ws, payload=payload, timeout_s=timeout_s)
            # Inject connect time
            out["connect_ms"] = round(connect_ms, 3) if connect_ms is not None else None
            return out

    except Exception as exc:
        return asdict(
            TurnTimings(
                ok=False,
                error=str(exc),
                connect_ms=round(connect_ms, 3) if connect_ms is not None else None,
                ttft_ms=None,
                inter_token_ms_avg=None,
                e2e_ms=None,
                token_events=0,
                final_message_chars=0,
                debug={},
            )
        )
