"""Tests for Pydantic request/response schemas."""

import pytest
from pydantic import ValidationError

from budget_pacing.schemas.bid_schema import BidRequest
from budget_pacing.schemas.event_schema import EventRequest


class TestEventRequestSchema:

    def test_valid_event(self):
        req = EventRequest.model_validate({
            "campaign_id": "A1",
            "cost": 0.50,
            "timestamp": "2025-03-05T10:00:00Z",
        })
        assert req.campaign_id == "A1"
        assert req.cost == 0.50
        assert req.timestamp.year == 2025

    def test_missing_campaign_id(self):
        with pytest.raises(ValidationError):
            EventRequest.model_validate({"cost": 1.0, "timestamp": "2025-03-05T10:00:00Z"})

    def test_empty_campaign_id(self):
        with pytest.raises(ValidationError):
            EventRequest.model_validate({
                "campaign_id": "",
                "cost": 1.0,
                "timestamp": "2025-03-05T10:00:00Z",
            })

    def test_negative_cost(self):
        with pytest.raises(ValidationError):
            EventRequest.model_validate({
                "campaign_id": "A1",
                "cost": -5.0,
                "timestamp": "2025-03-05T10:00:00Z",
            })

    def test_zero_cost(self):
        with pytest.raises(ValidationError):
            EventRequest.model_validate({
                "campaign_id": "A1",
                "cost": 0.0,
                "timestamp": "2025-03-05T10:00:00Z",
            })

    def test_missing_timestamp(self):
        with pytest.raises(ValidationError):
            EventRequest.model_validate({"campaign_id": "A1", "cost": 1.0})

    def test_invalid_timestamp(self):
        with pytest.raises(ValidationError):
            EventRequest.model_validate({
                "campaign_id": "A1",
                "cost": 1.0,
                "timestamp": "not-a-date",
            })

    def test_z_suffix_accepted(self):
        req = EventRequest.model_validate({
            "campaign_id": "A1",
            "cost": 1.0,
            "timestamp": "2025-03-05T10:00:00Z",
        })
        assert req.timestamp is not None

    def test_timezone_aware_timestamp(self):
        req = EventRequest.model_validate({
            "campaign_id": "A1",
            "cost": 1.0,
            "timestamp": "2025-03-05T22:00:00+12:00",
        })
        assert req.timestamp is not None


class TestBidRequestSchema:

    def test_valid_request(self):
        req = BidRequest.model_validate({"campaign_id": "A1"})
        assert req.campaign_id == "A1"
        assert req.geo is None

    def test_with_geo(self):
        req = BidRequest.model_validate({"campaign_id": "A1", "geo": "Auckland"})
        assert req.geo == "Auckland"

    def test_missing_campaign_id(self):
        with pytest.raises(ValidationError):
            BidRequest.model_validate({})

    def test_empty_campaign_id(self):
        with pytest.raises(ValidationError):
            BidRequest.model_validate({"campaign_id": ""})
