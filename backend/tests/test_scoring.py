from datetime import date

import pytest

from app.scoring import ScoringParams, bucket_by_week, daily_points, week_start

PARAMS = ScoringParams(min_threshold=80, target=600, max_points=100)


def test_zero_at_and_below_threshold():
    assert daily_points(0, PARAMS) == 0
    assert daily_points(80, PARAMS) == 0
    assert daily_points(50, PARAMS) == 0


def test_target_hits_about_80_percent():
    assert daily_points(600, PARAMS) == pytest.approx(80.0, rel=1e-6)


def test_monotonic_and_bounded_for_huge_values():
    low = daily_points(600, PARAMS)
    high = daily_points(5_000, PARAMS)
    assert low < high < PARAMS.max_points


def test_week_start_monday_sunday_midweek():
    assert week_start(date(2026, 10, 12)) == date(2026, 10, 12)  # Monday
    assert week_start(date(2026, 10, 18)) == date(2026, 10, 12)  # Sunday same week
    assert week_start(date(2026, 10, 15)) == date(2026, 10, 12)  # mid-week Thursday


def test_bucket_by_week_splits_on_week_boundary():
    buckets = bucket_by_week(
        [
            (date(2026, 10, 18), 10.0),  # Sunday, week of Oct 12
            (date(2026, 10, 19), 5.0),  # Monday, next week
        ]
    )
    assert buckets == {date(2026, 10, 12): 10.0, date(2026, 10, 19): 5.0}
