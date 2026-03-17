"""Shared pytest fixtures for the Budget Pacing Service."""

import pytest

from budget_pacing.app import create_app
from budget_pacing.config import TestConfig
from budget_pacing.models.database import db as _db
from budget_pacing.services import BudgetPacingService


@pytest.fixture()
def app():
    """Create a Flask app backed by an in-memory SQLite database."""
    application = create_app(config=TestConfig())
    yield application


@pytest.fixture()
def client(app):
    """Flask test client for HTTP-level integration tests."""
    return app.test_client()


@pytest.fixture()
def db(app):
    """Provide the SQLAlchemy db session, rolling back after each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture()
def service(app):
    """BudgetPacingService wired to the test app's config."""
    return app.config["SERVICE"]
