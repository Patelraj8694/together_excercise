"""Unit tests for the daily-limit circuit breaker."""

from datetime import datetime, timezone

import pytest

from budget_pacing.schemas.event_schema import EventRequest
from budget_pacing.services import BudgetExceededError


def _req(campaign_id="A1", cost=50.0, ts="2025-03-05T10:00:00Z"):
    return EventRequest.model_validate({
        "campaign_id": campaign_id,
        "cost": cost,
        "timestamp": ts,
    })


class TestCircuitBreakerOnEvent:

    def test_event_within_budget(self, app, service):
        with app.app_context():
            result = service.record_event(_req(cost=50.0))
            assert result.daily_spend == 50.0

    def test_event_at_exact_limit(self, app, service):
        with app.app_context():
            service.record_event(_req(cost=80.0))
            result = service.record_event(_req(cost=20.0, ts="2025-03-05T11:00:00Z"))
            assert result.daily_spend == 100.0

    def test_event_exceeds_limit(self, app, service):
        with app.app_context():
            service.record_event(_req(cost=90.0))
            with pytest.raises(BudgetExceededError):
                service.record_event(_req(cost=20.0, ts="2025-03-05T11:00:00Z"))

    def test_single_event_exceeds_limit(self, app, service):
        with app.app_context():
            with pytest.raises(BudgetExceededError):
                service.record_event(_req(cost=200.0))

    def test_rejected_event_does_not_update_state(self, app, service):
        with app.app_context():
            from budget_pacing.models.event import Event

            service.record_event(_req(cost=90.0))
            with pytest.raises(BudgetExceededError):
                service.record_event(_req(cost=20.0, ts="2025-03-05T11:00:00Z"))
            assert Event.get_daily_spend("A1", "2025-03-05") == 90.0

    def test_different_days_independent(self, app, service):
        with app.app_context():
            service.record_event(_req(cost=100.0))
            result = service.record_event(_req(cost=50.0, ts="2025-03-06T10:00:00Z"))
            assert result.daily_spend == 50.0

    def test_different_campaigns_independent(self, app, service):
        with app.app_context():
            service.record_event(_req(campaign_id="A1", cost=100.0))
            result = service.record_event(_req(campaign_id="B2", cost=50.0))
            assert result.daily_spend == 50.0


class TestCircuitBreakerOnBid:

    def test_bid_zero_at_limit(self, app, service):
        with app.app_context():
            service.record_event(_req(cost=100.0))
            now = datetime(2025, 3, 5, 12, 0, tzinfo=timezone.utc)
            assert service.get_bid("A1", now=now) == 0.0

    def test_bid_positive_under_limit(self, app, service):
        with app.app_context():
            service.record_event(_req(cost=30.0))
            now = datetime(2025, 3, 5, 12, 0, tzinfo=timezone.utc)
            assert service.get_bid("A1", now=now) > 0.0
