"""Tests for SQLAlchemy models — data-access layer."""

from datetime import datetime, timezone

from budget_pacing.models.campaign import CampaignConfig
from budget_pacing.models.database import db
from budget_pacing.models.event import Event


class TestEventModel:

    def test_insert_and_get_daily_spend(self, app):
        with app.app_context():
            e1 = Event(campaign_id="A1", cost=10.0, timestamp=datetime(2025, 3, 5, 10, tzinfo=timezone.utc), event_date="2025-03-05")
            e2 = Event(campaign_id="A1", cost=5.5, timestamp=datetime(2025, 3, 5, 11, tzinfo=timezone.utc), event_date="2025-03-05")
            db.session.add_all([e1, e2])
            db.session.commit()

            assert Event.get_daily_spend("A1", "2025-03-05") == 15.5

    def test_empty_spend_returns_zero(self, app):
        with app.app_context():
            assert Event.get_daily_spend("UNKNOWN", "2025-03-05") == 0.0

    def test_daily_spend_isolates_dates(self, app):
        with app.app_context():
            db.session.add(Event(campaign_id="A1", cost=10.0, timestamp=datetime(2025, 3, 5, 10, tzinfo=timezone.utc), event_date="2025-03-05"))
            db.session.add(Event(campaign_id="A1", cost=20.0, timestamp=datetime(2025, 3, 6, 10, tzinfo=timezone.utc), event_date="2025-03-06"))
            db.session.commit()

            assert Event.get_daily_spend("A1", "2025-03-05") == 10.0
            assert Event.get_daily_spend("A1", "2025-03-06") == 20.0

    def test_daily_spend_isolates_campaigns(self, app):
        with app.app_context():
            db.session.add(Event(campaign_id="A1", cost=10.0, timestamp=datetime(2025, 3, 5, 10, tzinfo=timezone.utc), event_date="2025-03-05"))
            db.session.add(Event(campaign_id="B2", cost=20.0, timestamp=datetime(2025, 3, 5, 10, tzinfo=timezone.utc), event_date="2025-03-05"))
            db.session.commit()

            assert Event.get_daily_spend("A1", "2025-03-05") == 10.0
            assert Event.get_daily_spend("B2", "2025-03-05") == 20.0


class TestCampaignConfigModel:

    def test_no_config_returns_none(self, app):
        with app.app_context():
            assert CampaignConfig.get_config("NONEXISTENT") is None

    def test_returns_config_when_exists(self, app):
        with app.app_context():
            cfg = CampaignConfig(campaign_id="X1", daily_limit=500.0, max_bid=3.0, base_bid=0.5)
            db.session.add(cfg)
            db.session.commit()

            result = CampaignConfig.get_config("X1")
            assert result.daily_limit == 500.0
            assert result.max_bid == 3.0
            assert result.base_bid == 0.5
