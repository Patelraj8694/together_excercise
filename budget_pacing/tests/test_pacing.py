"""Unit tests for the pacing algorithm — pure functions, zero I/O."""

from datetime import datetime, timezone

import pytest

from budget_pacing.services import compute_bid, compute_pacing_factor


def _utc(hour: int, minute: int = 0) -> datetime:
    return datetime(2025, 3, 5, hour, minute, tzinfo=timezone.utc)


class TestPacingFactor:

    def test_on_pace(self):
        """At noon with 50 % of budget spent -> factor ~ 1.0."""
        factor = compute_pacing_factor(500.0, 1000.0, now=_utc(12))
        assert factor == pytest.approx(1.0, abs=0.05)

    def test_behind_schedule(self):
        """At noon with 25 % spent -> factor ~ 2.0 (bid up)."""
        factor = compute_pacing_factor(250.0, 1000.0, now=_utc(12))
        assert factor == pytest.approx(2.0, abs=0.05)

    def test_ahead_of_schedule(self):
        """At noon with 75 % spent -> factor ~ 0.67 (bid down)."""
        factor = compute_pacing_factor(750.0, 1000.0, now=_utc(12))
        assert factor == pytest.approx(0.667, abs=0.05)

    def test_zero_spend_returns_max_factor(self):
        factor = compute_pacing_factor(0.0, 1000.0, now=_utc(12), max_factor=2.0)
        assert factor == 2.0

    def test_heavily_overspent_clamps_to_min(self):
        factor = compute_pacing_factor(5000.0, 1000.0, now=_utc(12), min_factor=0.1)
        assert factor == 0.1

    def test_start_of_day_neutral(self):
        early = datetime(2025, 3, 5, 0, 0, 30, tzinfo=timezone.utc)
        factor = compute_pacing_factor(0.0, 1000.0, now=early)
        assert factor == 1.0

    def test_end_of_day_behind_schedule(self):
        factor = compute_pacing_factor(100.0, 1000.0, now=_utc(23, 50), max_factor=2.0)
        assert factor == 2.0

    def test_daily_limit_zero_returns_zero(self):
        assert compute_pacing_factor(0.0, 0.0, now=_utc(12)) == 0.0

    def test_factor_always_within_bounds(self):
        for spend in [0, 50, 250, 500, 750, 1000, 2000]:
            for hour in [1, 6, 12, 18, 23]:
                f = compute_pacing_factor(
                    float(spend), 1000.0, now=_utc(hour),
                    min_factor=0.1, max_factor=2.0,
                )
                assert 0.0 <= f <= 2.0


class TestComputeBid:

    def test_normal(self):
        assert compute_bid(1.0, 1.0, 5.0) == 1.0

    def test_capped_at_max(self):
        assert compute_bid(10.0, 2.0, 5.0) == 5.0

    def test_never_negative(self):
        assert compute_bid(1.0, -1.0, 5.0) == 0.0

    def test_rounds_to_two_decimals(self):
        assert compute_bid(1.0, 0.333, 5.0) == 0.33

    def test_zero_factor_gives_zero_bid(self):
        assert compute_bid(1.0, 0.0, 5.0) == 0.0
