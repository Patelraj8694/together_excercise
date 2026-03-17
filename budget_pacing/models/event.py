"""SQLAlchemy model for auction-win events."""

from datetime import datetime, timezone

from sqlalchemy import Index, func

from budget_pacing.models.database import db


class Event(db.Model):
    """A single auction win recorded against a campaign.

    Attributes
    ----------
    id : int
        Auto-incrementing primary key.
    campaign_id : str
        Identifier of the campaign that won the auction.
    cost : float
        Dollar amount paid for the win (always > 0).
    timestamp : datetime
        When the auction was won (timezone-aware, stored as UTC).
    event_date : str
        Calendar date in UTC (``YYYY-MM-DD``), derived from *timestamp* at
        insert time.  Pre-extracted so daily aggregation is a simple
        ``WHERE event_date = ?`` with an index hit.
    created_at : datetime
        Server-side creation timestamp.
    """

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.String(64), nullable=False, index=True)
    cost = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False)
    event_date = db.Column(db.String(10), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Composite index for the hot query: SUM(cost) WHERE campaign_id AND event_date
    __table_args__ = (
        Index("idx_events_campaign_date", "campaign_id", "event_date"),
    )

    def __repr__(self) -> str:
        return f"<Event {self.campaign_id} ${self.cost:.2f} {self.event_date}>"

    # ------------------------------------------------------------------
    # Query helpers (class methods keep queries close to the model)
    # ------------------------------------------------------------------

    @classmethod
    def get_daily_spend(cls, campaign_id: str, event_date: str) -> float:
        """Return total cost for *campaign_id* on *event_date*, or ``0.0``."""
        result = (
            db.session.query(func.coalesce(func.sum(cls.cost), 0.0))
            .filter(cls.campaign_id == campaign_id, cls.event_date == event_date)
            .scalar()
        )
        return float(result)
