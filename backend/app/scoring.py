"""Pure scoring math for the competition page (Брат vs Ты). No DB/session
access — fully unit-testable by import alone. See app/api/competition.py
for how this combines with real metric data.
"""
import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable


@dataclass(frozen=True)
class ScoringParams:
    min_threshold: float
    target: float
    max_points: float = 100.0

    @property
    def k(self) -> float:
        span = self.target - self.min_threshold
        if span <= 0:
            raise ValueError("target must be greater than min_threshold")
        return math.log(5) / span  # points(target) ≈ 0.8 * max_points


# Tunable per-player constants — raw daily counters, as collected today.
GITHUB_PARAMS = ScoringParams(min_threshold=1, target=6)
OBSIDIAN_PARAMS = ScoringParams(min_threshold=80, target=600)


def daily_points(value: float, params: ScoringParams) -> float:
    """Saturating curve: 0 at/below min_threshold, asymptotic to max_points
    beyond it, so neither trivial engagement nor a multi-hour binge buys a
    strong advantage over hitting target.
    """
    excess = max(0.0, value - params.min_threshold)
    return params.max_points * (1 - math.exp(-params.k * excess))


def week_start(d: date) -> date:
    """Monday on/before `d` — matches mondayIndex() in
    frontend/src/components/gridConstants.ts (date.weekday() is already
    Monday=0..Sunday=6).
    """
    return d - timedelta(days=d.weekday())


def bucket_by_week(items: Iterable[tuple[date, float]]) -> dict[date, float]:
    """Sum (date, value) pairs into {week_start: total}."""
    buckets: dict[date, float] = {}
    for d, value in items:
        wk = week_start(d)
        buckets[wk] = buckets.get(wk, 0.0) + value
    return buckets
