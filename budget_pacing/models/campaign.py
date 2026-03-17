"""SQLAlchemy model for optional per-campaign configuration overrides."""

from budget_pacing.models.database import db


class CampaignConfig(db.Model):
    """Per-campaign overrides for budget and bidding parameters.

    If no row exists for a campaign, the service falls back to global
    defaults from :class:`~budget_pacing.config.Config`.  All columns
    (except the PK) are nullable — ``None`` means "use global default".
    """

    __tablename__ = "campaign_config"

    campaign_id = db.Column(db.String(64), primary_key=True)
    daily_limit = db.Column(db.Float, nullable=True)
    max_bid = db.Column(db.Float, nullable=True)
    base_bid = db.Column(db.Float, nullable=True)

    def __repr__(self) -> str:
        return f"<CampaignConfig {self.campaign_id}>"

    @classmethod
    def get_config(cls, campaign_id: str):
        """Return the config row for *campaign_id*, or ``None``."""
        return db.session.get(cls, campaign_id)
