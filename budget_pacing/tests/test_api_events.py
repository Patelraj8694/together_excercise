"""Integration tests for POST /event through the Flask test client."""


class TestPostEvent:

    def test_record_event_success(self, client):
        resp = client.post("/event", json={
            "campaign_id": "A1",
            "cost": 10.0,
            "timestamp": "2025-03-05T10:00:00Z",
        })
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["status"] == "recorded"
        assert body["campaign_id"] == "A1"
        assert body["daily_spend"] == 10.0

    def test_record_multiple_events(self, client):
        client.post("/event", json={
            "campaign_id": "A1",
            "cost": 40.0,
            "timestamp": "2025-03-05T10:00:00Z",
        })
        resp = client.post("/event", json={
            "campaign_id": "A1",
            "cost": 30.0,
            "timestamp": "2025-03-05T11:00:00Z",
        })
        assert resp.status_code == 201
        assert resp.get_json()["daily_spend"] == 70.0

    def test_record_event_exceeds_budget(self, client):
        client.post("/event", json={
            "campaign_id": "A1",
            "cost": 90.0,
            "timestamp": "2025-03-05T10:00:00Z",
        })
        resp = client.post("/event", json={
            "campaign_id": "A1",
            "cost": 20.0,
            "timestamp": "2025-03-05T11:00:00Z",
        })
        assert resp.status_code == 409

    def test_record_event_negative_cost(self, client):
        resp = client.post("/event", json={
            "campaign_id": "A1",
            "cost": -5.0,
            "timestamp": "2025-03-05T10:00:00Z",
        })
        assert resp.status_code == 422

    def test_record_event_zero_cost(self, client):
        resp = client.post("/event", json={
            "campaign_id": "A1",
            "cost": 0.0,
            "timestamp": "2025-03-05T10:00:00Z",
        })
        assert resp.status_code == 422

    def test_record_event_missing_fields(self, client):
        resp = client.post("/event", json={"cost": 1.0})
        assert resp.status_code == 422

    def test_record_event_empty_campaign_id(self, client):
        resp = client.post("/event", json={
            "campaign_id": "",
            "cost": 1.0,
            "timestamp": "2025-03-05T10:00:00Z",
        })
        assert resp.status_code == 422

    def test_record_event_invalid_json(self, client):
        resp = client.post("/event", data="not json", content_type="application/json")
        assert resp.status_code == 400
