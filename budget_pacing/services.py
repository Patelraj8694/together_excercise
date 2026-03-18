"""Core business logic: pacing algorithm, circuit breaker, bid computation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from budget_pacing.config import Config

from budget_pacing.models.campaign import CampaignConfig
from budget_pacing.models.database import db
from budget_pacing.models.event import Event
from budget_pacing.schemas.event_schema import EventRequest, EventResponse


class BudgetExceededError(Exception):
    """Raised when recording an event would exceed the campaign's daily limit."""

    def __init__(self, current_spend: float, cost: float, daily_limit: float) -> None:
        self.current_spend = current_spend
        self.cost = cost
        self.daily_limit = daily_limit
        super().__init__(
            f"Recording this event would exceed the daily limit. "
            f"Current spend: ${current_spend:.2f}, "
            f"event cost: ${cost:.2f}, "
            f"daily limit: ${daily_limit:.2f}."
        )


class BudgetPacingService:
    """Orchestrates event recording, pacing computation, and bid generation.

    Parameters
    ----------
    config : Config
        Application configuration (daily_limit, max_bid, etc.).
    """

    def __init__(self, config: Config) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_event(self, payload: EventRequest) -> EventResponse:
        """Record an auction win.

        Raises :class:`BudgetExceededError` if the daily limit would be
        breached.  The check and insert happen inside a single database
        transaction for atomicity.

        Note: SQLite serialises writes, so the read-check-insert
        sequence is safe.  For PostgreSQL/MySQL in production, use
        ``SELECT ... FOR UPDATE`` or a serialisable transaction to
        prevent TOCTOU races under concurrent writes.
        """
        ts_utc = payload.timestamp.astimezone(timezone.utc)
        event_date = ts_utc.strftime("%Y-%m-%d")
        cfg = self._effective_config(payload.campaign_id)

        current_spend = Event.get_daily_spend(payload.campaign_id, event_date)

        if current_spend + payload.cost > cfg["daily_limit"]:
            raise BudgetExceededError(
                current_spend, payload.cost, cfg["daily_limit"]
            )

        event = Event(
            campaign_id=payload.campaign_id,
            cost=payload.cost,
            timestamp=ts_utc,
            event_date=event_date,
        )
        db.session.add(event)
        db.session.commit()

        new_spend = current_spend + payload.cost

        return EventResponse(
            campaign_id=payload.campaign_id,
            daily_spend=round(new_spend, 2),
            daily_limit=cfg["daily_limit"],
        )

    def get_bid(self, campaign_id: str, geo: str | None = None, now: datetime | None = None) -> float:
        """Return a paced bid recommendation for *campaign_id*."""
        if now is None:
            now = datetime.now(timezone.utc)

        today = now.strftime("%Y-%m-%d")
        cfg = self._effective_config(campaign_id)
        current_spend = Event.get_daily_spend(campaign_id, today)

        # Circuit breaker: budget exhausted
        if current_spend >= cfg["daily_limit"]:
            return 0.0

        pacing_factor = compute_pacing_factor(
            actual_spend=current_spend,
            daily_limit=cfg["daily_limit"],
            now=now,
            min_factor=self._config.PACING_MIN_FACTOR,
            max_factor=self._config.PACING_MAX_FACTOR,
        )

        return compute_bid(cfg["base_bid"], pacing_factor, cfg["max_bid"])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _effective_config(self, campaign_id: str) -> dict:
        """Merge optional per-campaign overrides with global defaults."""
        override = CampaignConfig.get_config(campaign_id)
        return {
            "daily_limit": (
                override.daily_limit
                if override and override.daily_limit is not None
                else self._config.DAILY_LIMIT
            ),
            "max_bid": (
                override.max_bid
                if override and override.max_bid is not None
                else self._config.MAX_BID
            ),
            "base_bid": (
                override.base_bid
                if override and override.base_bid is not None
                else self._config.BASE_BID
            ),
        }


# ======================================================================
# Pure functions — no I/O, trivially unit-testable
# ======================================================================


def compute_pacing_factor(
    actual_spend: float,
    daily_limit: float,
    now: datetime | None = None,
    min_factor: float = 0.1,
    max_factor: float = 2.0,
) -> float:
    """Return a multiplier in ``[min_factor, max_factor]`` that scales the
    bid based on how far ahead or behind the ideal spend curve we are.

    * factor > 1.0 — behind schedule → bid more aggressively
    * factor < 1.0 — ahead of schedule → bid less aggressively
    * factor == 1.0 — exactly on pace
    """
    if daily_limit <= 0:
        return 0.0

    if now is None:
        now = datetime.now(timezone.utc)

    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_elapsed = (now - midnight).total_seconds()
    time_fraction = seconds_elapsed / 86_400.0

    # Guard: very start of day — not enough data to pace
    if time_fraction < 0.001:
        return 1.0

    ideal_spend = daily_limit * time_fraction

    # No spend yet → bid as aggressively as allowed
    if actual_spend <= 0:
        return max_factor

    # Inverse-ratio: symmetric on a log scale
    spend_ratio = actual_spend / ideal_spend
    pacing_factor = 1.0 / spend_ratio

    return max(min_factor, min(max_factor, pacing_factor))


def compute_bid(base_bid: float, pacing_factor: float, max_bid: float) -> float:
    """Apply *pacing_factor* to *base_bid* and clamp to ``[0, max_bid]``."""
    raw_bid = base_bid * pacing_factor
    return round(max(0.0, min(max_bid, raw_bid)), 2)
