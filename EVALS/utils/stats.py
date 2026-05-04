from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


def _percentile(sorted_values: List[float], p: float) -> Optional[float]:
    if not sorted_values:
        return None
    if p <= 0:
        return float(sorted_values[0])
    if p >= 100:
        return float(sorted_values[-1])
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_values[int(k)])
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return float(d0 + d1)


@dataclass
class SummaryStats:
    n: int
    mean: Optional[float]
    median: Optional[float]
    p90: Optional[float]
    p99: Optional[float]
    min: Optional[float]
    max: Optional[float]


def summarize(values: List[float]) -> Dict[str, Any]:
    if not values:
        return asdict(SummaryStats(n=0, mean=None, median=None, p90=None, p99=None, min=None, max=None))
    xs = sorted(float(v) for v in values)
    mean = sum(xs) / len(xs)
    median = _percentile(xs, 50)
    p90 = _percentile(xs, 90)
    p99 = _percentile(xs, 99)
    return asdict(
        SummaryStats(
            n=len(xs),
            mean=round(mean, 3),
            median=round(median or 0.0, 3) if median is not None else None,
            p90=round(p90 or 0.0, 3) if p90 is not None else None,
            p99=round(p99 or 0.0, 3) if p99 is not None else None,
            min=round(xs[0], 3),
            max=round(xs[-1], 3),
        )
    )
