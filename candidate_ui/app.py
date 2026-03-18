"""Dash UI for the Keyword Researcher multi-agent system.

Provides a conversational interface where users send keyword/market research
queries and receive structured responses from the orchestrator agent (via
Vertex AI Agent Engine or the local ADK server).

Architecture:
    app.py          — Application factory & entry-point (this file)
    layout.py       — Dash component tree (layout definition)
    callbacks.py    — All callback registrations
    components.py   — Pure rendering/parsing helpers (testable)
    agent_client.py — Backend client (local ADK / Vertex AI)
    assets/         — Static CSS (auto-served by Dash)

Run:
    python candidate_ui/app.py          # or: python -m candidate_ui.app
    # -> http://localhost:8050
"""

import os
from pathlib import Path

import dash
from dotenv import load_dotenv

from candidate_ui.agent_client import AgentClient
from candidate_ui.callbacks import register_callbacks
from candidate_ui.layout import create_layout

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def create_app() -> dash.Dash:
    """Application factory — creates and configures the Dash app."""
    agent = AgentClient()

    application = dash.Dash(
        __name__,
        title="Keyword Researcher",
        # Required for pattern-matching callbacks (dash.ALL)
        suppress_callback_exceptions=True,
    )

    application.layout = create_layout(backend_mode=agent.mode)
    register_callbacks(application, agent)

    return application


# Create the app instance (used by Dash's built-in server and Docker)
app = create_app()
server = app.server  # Expose the Flask server for production WSGI

# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("DASH_PORT", "8050"))
    app.run(debug=False, host="0.0.0.0", port=port)
