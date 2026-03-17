"""Application configuration loaded from environment variables.

Uses ``python-dotenv`` to load a ``.env`` file (if present) from the
project root, so configuration lives outside the codebase.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (two levels up: budget_pacing/ -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Config:
    """Production configuration.

    Every budget/pacing setting is overridable via a ``BP_``-prefixed env var.
    Flask-SQLAlchemy settings use the standard ``SQLALCHEMY_`` prefix.
    """

    # --- Budget constraints ---------------------------------------------------
    DAILY_LIMIT: float = float(os.getenv("BP_DAILY_LIMIT", "1000.0"))
    MAX_BID: float = float(os.getenv("BP_MAX_BID", "10.0"))
    BASE_BID: float = float(os.getenv("BP_BASE_BID", "1.0"))

    # --- Pacing algorithm tuning ----------------------------------------------
    PACING_MIN_FACTOR: float = float(os.getenv("BP_PACING_MIN_FACTOR", "0.1"))
    PACING_MAX_FACTOR: float = float(os.getenv("BP_PACING_MAX_FACTOR", "2.0"))

    # --- Flask-SQLAlchemy -----------------------------------------------------
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "BP_DATABASE_URI", "sqlite:///budget_pacing.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # --- Flask ----------------------------------------------------------------
    TESTING: bool = False


class TestConfig(Config):
    """Overrides for the test suite — in-memory DB, smaller limits."""

    DAILY_LIMIT: float = 100.0
    MAX_BID: float = 5.0
    BASE_BID: float = 1.0
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    TESTING: bool = True
