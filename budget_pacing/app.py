"""Flask application factory with Flask-SQLAlchemy integration."""

from flask import Flask, jsonify, redirect
from flasgger import Swagger

from budget_pacing.config import Config  # config.py already loads root .env
from budget_pacing.controllers.bid_controller import bid_bp
from budget_pacing.controllers.event_controller import event_bp
from budget_pacing.models.database import db
from budget_pacing.services import BudgetPacingService

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}

SWAGGER_TEMPLATE = {
    "info": {
        "title": "Budget Pacing Service",
        "description": (
            "A microservice that recommends optimised bids for ad campaigns "
            "to maintain smooth budget spending throughout the day.\n\n"
            "**Core features:**\n"
            "- Record auction wins (cost attribution)\n"
            "- Get paced bid recommendations based on time-of-day vs. spend progress\n"
            "- Circuit breaker: rejects events that would exceed the daily budget\n"
        ),
        "version": "1.0.0",
    },
    "tags": [
        {
            "name": "Events",
            "description": "Record auction wins and attribute costs to campaigns",
        },
        {
            "name": "Bids",
            "description": "Get paced bid recommendations for campaigns",
        },
    ],
}


def create_app(config=None) -> Flask:
    """Application factory.

    Parameters
    ----------
    config : object, optional
        A configuration object (e.g. :class:`TestConfig`).
        Defaults to :class:`Config` (production settings).
    """
    app = Flask(__name__)

    # Load configuration
    if config is None:
        config = Config()
    app.config.from_object(config)

    # Initialise Flask-SQLAlchemy
    db.init_app(app)

    with app.app_context():
        # Import models so SQLAlchemy registers them before create_all
        from budget_pacing.models import campaign, event  # noqa: F401

        db.create_all()

    # Wire up service layer
    service = BudgetPacingService(config)
    app.config["SERVICE"] = service

    # Register controller blueprints
    app.register_blueprint(event_bp)
    app.register_blueprint(bid_bp)

    # Swagger UI — interactive API docs at /apidocs
    Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)

    @app.route("/")
    def index():
        return redirect("/apidocs/")

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=8000, debug=True)
