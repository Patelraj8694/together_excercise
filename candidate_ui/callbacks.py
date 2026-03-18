"""Dash callback registrations for the Keyword Researcher UI.

All callbacks are registered via ``register_callbacks(app, agent)``,
keeping them decoupled from the Dash app instance and the AgentClient.
"""

import json
import traceback
import uuid
from datetime import datetime, timezone

import dash
from dash import Input, Output, State, callback_context, no_update

from candidate_ui.agent_client import AgentClient
from candidate_ui.components import render_conversation, truncate_title
from candidate_ui.layout import PRESET_PROMPTS


def register_callbacks(app: dash.Dash, agent: AgentClient) -> None:
    """Attach all callbacks to *app*.

    Parameters
    ----------
    app:
        The Dash application instance.
    agent:
        Initialised AgentClient (local or Vertex AI).
    """

    # ------------------------------------------------------------------
    # Session bootstrap
    # ------------------------------------------------------------------

    @app.callback(
        Output("session-id", "data"),
        Input("session-id", "data"),
    )
    def ensure_session(current_session_id: str | None) -> str:
        """Create an agent session on first load if one doesn't exist."""
        if current_session_id:
            return current_session_id
        return agent.create_session()

    # ------------------------------------------------------------------
    # Preset prompt buttons
    # ------------------------------------------------------------------

    @app.callback(
        Output("user-input", "value"),
        [Input({"type": "preset-btn", "index": dash.ALL}, "n_clicks")],
        prevent_initial_call=True,
    )
    def fill_preset(n_clicks_list: list[int]) -> str:
        """Populate the input box when a preset prompt button is clicked."""
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks_list):
            return no_update
        prop_id = ctx.triggered[0]["prop_id"]
        btn_info = json.loads(prop_id.split(".")[0])
        return PRESET_PROMPTS[btn_info["index"]]

    # ------------------------------------------------------------------
    # Sidebar rendering
    # ------------------------------------------------------------------

    @app.callback(
        Output("conversation-list", "children"),
        Input("all-conversations", "data"),
        Input("active-conversation-id", "data"),
    )
    def render_sidebar(
        all_convs: dict | None,
        active_id: str | None,
    ) -> list:
        """Render the list of past conversations in the sidebar."""
        from dash import html

        all_convs = all_convs or {}
        if not all_convs:
            return html.P("No conversations yet.", className="sidebar-empty")

        sorted_convs = sorted(
            all_convs.items(),
            key=lambda x: x[1].get("updated_at", ""),
            reverse=True,
        )

        items: list = []
        for conv_id, conv in sorted_convs:
            title = conv.get("title", "Untitled")
            msg_count = len(conv.get("history", [])) // 2
            is_active = conv_id == active_id

            items.append(
                html.Button(
                    className=f"conv-item {'conv-item-active' if is_active else ''}",
                    id={"type": "conv-btn", "index": conv_id},
                    n_clicks=0,
                    children=[
                        html.Div(title, className="conv-title"),
                        html.Div(
                            f"{msg_count} message{'s' if msg_count != 1 else ''}",
                            className="conv-meta",
                        ),
                    ],
                )
            )
        return items

    # ------------------------------------------------------------------
    # Unified conversation action handler
    # ------------------------------------------------------------------
    # Consolidates new-chat, switch-conversation, and send-message into
    # a single callback to avoid excessive allow_duplicate=True and
    # eliminate overlapping Output conflicts.
    # ------------------------------------------------------------------

    @app.callback(
        Output("conversation-thread", "children"),
        Output("conversation-history", "data"),
        Output("all-conversations", "data"),
        Output("active-conversation-id", "data"),
        Output("session-id", "data", allow_duplicate=True),
        Output("loading-target", "children"),
        Output("error-banner", "children"),
        Output("error-banner", "style"),
        Output("user-input", "value", allow_duplicate=True),
        # --- Inputs (any of these can trigger the callback) ---
        Input("send-btn", "n_clicks"),
        Input("new-chat-btn", "n_clicks"),
        Input({"type": "conv-btn", "index": dash.ALL}, "n_clicks"),
        # --- State (read-only) ---
        State("user-input", "value"),
        State("session-id", "data"),
        State("conversation-history", "data"),
        State("all-conversations", "data"),
        State("active-conversation-id", "data"),
        prevent_initial_call=True,
    )
    def handle_conversation_action(
        send_clicks: int,
        new_chat_clicks: int,
        conv_btn_clicks: list[int],
        user_text: str | None,
        session_id: str | None,
        history: list[dict] | None,
        all_convs: dict | None,
        active_id: str | None,
    ) -> tuple:
        """Single callback for all conversation-mutating actions.

        Determines which input fired via ``ctx.triggered_id`` and branches:
        - ``new-chat-btn`` → create a new empty conversation
        - ``conv-btn`` → switch to an existing conversation
        - ``send-btn`` → send user message to the agent
        """
        ctx = callback_context
        no_change = (
            no_update, no_update, no_update, no_update, no_update,
            no_update, no_update, no_update, no_update,
        )

        if not ctx.triggered:
            return no_change

        triggered_id = ctx.triggered_id
        all_convs = all_convs or {}
        history = history or []

        # ---- New Chat ----
        if triggered_id == "new-chat-btn":
            if not new_chat_clicks:
                return no_change

            conv_id = uuid.uuid4().hex
            new_session_id = agent.create_session()
            all_convs[conv_id] = {
                "title": "New conversation",
                "session_id": new_session_id,
                "history": [],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            return ([], [], all_convs, conv_id, new_session_id,
                    "", "", {"display": "none"}, "")

        # ---- Switch Conversation ----
        if isinstance(triggered_id, dict) and triggered_id.get("type") == "conv-btn":
            if not any(n for n in conv_btn_clicks if n):
                return no_change

            conv_id = triggered_id["index"]
            conv = all_convs.get(conv_id, {})
            conv_history = conv.get("history", [])
            conv_session = conv.get("session_id", "")
            thread = render_conversation(conv_history)
            return (thread, conv_history, no_update, conv_id, conv_session,
                    "", "", {"display": "none"}, no_update)

        # ---- Send Message ----
        if triggered_id == "send-btn":
            if not send_clicks or not user_text or not user_text.strip():
                return no_change

            user_text = user_text.strip()

            if not session_id:
                session_id = agent.create_session()

            # Auto-create conversation if none is active
            if not active_id or active_id not in all_convs:
                active_id = uuid.uuid4().hex
                all_convs[active_id] = {
                    "title": truncate_title(user_text),
                    "session_id": session_id,
                    "history": [],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }

            history.append({"role": "user", "text": user_text})

            # Set title from first real user message
            conv = all_convs[active_id]
            if conv.get("title") == "New conversation":
                conv["title"] = truncate_title(user_text)

            # Call the agent
            error_msg = ""
            error_style: dict = {"display": "none"}
            try:
                agent_reply = agent.send_message(session_id, user_text)
                history.append({"role": "agent", "text": agent_reply})
            except ConnectionError as exc:
                error_msg = str(exc)
                error_style = {"display": "block"}
                history.append({"role": "agent", "text": f"[Connection error] {exc}"})
            except Exception as exc:
                error_msg = f"Unexpected error: {exc}"
                error_style = {"display": "block"}
                history.append({"role": "agent", "text": f"[Error] {exc}"})
                traceback.print_exc()

            # Persist conversation
            conv["history"] = history
            conv["session_id"] = session_id
            conv["updated_at"] = datetime.now(timezone.utc).isoformat()
            all_convs[active_id] = conv

            thread = render_conversation(history)
            return (thread, history, all_convs, active_id, session_id,
                    "", error_msg, error_style, "")

        return no_change
