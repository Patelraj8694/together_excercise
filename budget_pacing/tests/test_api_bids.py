"""Integration tests for GET /bid through the Flask test client."""

from datetime import datetime, timezone


def _today_ts(hour=10):
    """Return an ISO timestamp for today at the given hour (UTC)."""
    now = datetime.now(timezone.utc)
    return now.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


class TestGetBid:

    def test_bid_new_campaign(self, client):
        resp = client.get("/bid?campaign_id=A1")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["campaign_id"] == "A1"
        assert body["bid"] > 0

    def test_bid_after_spending(self, client):
        client.post("/event", json={
            "campaign_id": "A1",
            "cost": 30.0,
            "timestamp": _today_ts(),
        })
        resp = client.get("/bid?campaign_id=A1")
        assert resp.status_code == 200
        assert resp.get_json()["bid"] > 0

    def test_bid_zero_at_limit(self, client):
        client.post("/event", json={
            "campaign_id": "A1",
            "cost": 100.0,
            "timestamp": _today_ts(),
        })
        resp = client.get("/bid?campaign_id=A1")
        assert resp.status_code == 200
        assert resp.get_json()["bid"] == 0.0

    def test_bid_accepts_geo(self, client):
        resp = client.get("/bid?campaign_id=A1&geo=Auckland")
        assert resp.status_code == 200
        assert resp.get_json()["campaign_id"] == "A1"

    def test_bid_missing_campaign_id(self, client):
        resp = client.get("/bid")
        assert resp.status_code == 422

    def test_bid_never_exceeds_max(self, client):
        resp = client.get("/bid?campaign_id=NEW")
        assert resp.get_json()["bid"] <= 5.0

    def test_bid_between_zero_and_max(self, client):
        resp = client.get("/bid?campaign_id=X")
        bid = resp.get_json()["bid"]
        assert 0.0 <= bid <= 5.0
