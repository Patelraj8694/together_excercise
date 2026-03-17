"""Dash UI for the Keyword Researcher multi-agent system.

Provides a conversational interface where users send keyword/market research
queries and receive structured responses from the orchestrator agent (via
Vertex AI Agent Engine or the local ADK server).

Run:
    python candidate_ui/app.py          # or: python -m candidate_ui.app
    # -> http://localhost:8050
"""

import json
import traceback
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, State, callback_context, no_update
from dotenv import load_dotenv

from candidate_ui.agent_client import AgentClient

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

# Load the single project-root .env (one level up from candidate_ui/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

agent = AgentClient()

# ---------------------------------------------------------------------------
# Preset prompts — quick-start buttons for common research queries
# ---------------------------------------------------------------------------

PRESET_PROMPTS = [
    "Find keywords for running shoes",
    "What markets should I target for B2B SaaS?",
    "Give me recommendations for my search campaign",
    "Keywords and markets for organic skincare products",
]

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    title="Keyword Researcher",
    suppress_callback_exceptions=True,
)

app.layout = html.Div(
    className="app-container",
    children=[
        # --- Hidden stores for session state ---
        dcc.Store(id="session-id", storage_type="session"),
        dcc.Store(id="conversation-history", data=[], storage_type="session"),

        # --- Header ---
        html.Header(
            className="app-header",
            children=[
                html.H1("Keyword Researcher"),
                html.P(
                    "Multi-agent research assistant for keywords, markets & recommendations.",
                    className="subtitle",
                ),
            ],
        ),

        # --- Main content area ---
        html.Main(
            className="main-content",
            children=[
                # Conversation thread
                html.Div(id="conversation-thread", className="conversation-thread"),

                # Loading indicator
                dcc.Loading(
                    id="loading-indicator",
                    type="dot",
                    color="#4A90D9",
                    children=html.Div(id="loading-target"),
                ),

                # Error banner (hidden by default)
                html.Div(id="error-banner", className="error-banner", style={"display": "none"}),

                # Preset prompt buttons
                html.Div(
                    className="preset-prompts",
                    children=[
                        html.Span("Try: ", className="preset-label"),
                    ]
                    + [
                        html.Button(
                            prompt,
                            id={"type": "preset-btn", "index": i},
                            className="preset-btn",
                            n_clicks=0,
                        )
                        for i, prompt in enumerate(PRESET_PROMPTS)
                    ],
                ),

                # Input area
                html.Div(
                    className="input-area",
                    children=[
                        dcc.Textarea(
                            id="user-input",
                            placeholder="Ask about keywords, markets, or campaign recommendations...",
                            className="user-input",
                            n_blur=0,
                        ),
                        html.Button(
                            "Send",
                            id="send-btn",
                            className="send-btn",
                            n_clicks=0,
                        ),
                    ],
                ),
            ],
        ),

        # --- Footer ---
        html.Footer(
            className="app-footer",
            children=[
                html.Span(f"Backend: {agent._mode}"),
                html.Span(" | "),
                html.Span("Powered by Google ADK + Gemini"),
            ],
        ),
    ],
)

# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@app.callback(
    Output("session-id", "data"),
    Input("session-id", "data"),
)
def ensure_session(current_session_id):
    """Create a session on first load if one doesn't exist."""
    if current_session_id:
        return no_update
    return agent.create_session()


@app.callback(
    Output("user-input", "value"),
    [Input({"type": "preset-btn", "index": dash.ALL}, "n_clicks")],
    prevent_initial_call=True,
)
def fill_preset(n_clicks_list):
    """Populate the input box when a preset prompt button is clicked."""
    ctx = callback_context
    if not ctx.triggered or not any(n_clicks_list):
        return no_update
    # Identify which button was clicked
    prop_id = ctx.triggered[0]["prop_id"]
    btn_info = json.loads(prop_id.split(".")[0])
    return PRESET_PROMPTS[btn_info["index"]]


@app.callback(
    Output("conversation-thread", "children"),
    Output("conversation-history", "data"),
    Output("loading-target", "children"),
    Output("error-banner", "children"),
    Output("error-banner", "style"),
    Output("user-input", "value", allow_duplicate=True),
    Input("send-btn", "n_clicks"),
    State("user-input", "value"),
    State("session-id", "data"),
    State("conversation-history", "data"),
    prevent_initial_call=True,
)
def handle_send(n_clicks, user_text, session_id, history):
    """Send the user's message to the agent and update the conversation."""
    if not n_clicks or not user_text or not user_text.strip():
        return no_update, no_update, no_update, no_update, no_update, no_update

    user_text = user_text.strip()

    if not session_id:
        session_id = agent.create_session()

    # Append user message to history
    history = history or []
    history.append({"role": "user", "text": user_text})

    # Call the agent
    try:
        agent_reply = agent.send_message(session_id, user_text)
        history.append({"role": "agent", "text": agent_reply})
        error_msg = ""
        error_style = {"display": "none"}
    except ConnectionError as exc:
        error_msg = str(exc)
        error_style = {"display": "block"}
        history.append({"role": "agent", "text": f"[Connection error] {exc}"})
    except Exception as exc:
        error_msg = f"Unexpected error: {exc}"
        error_style = {"display": "block"}
        history.append({"role": "agent", "text": f"[Error] {exc}"})
        traceback.print_exc()

    # Build the conversation thread
    thread = _render_conversation(history)

    return thread, history, "", error_msg, error_style, ""


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _render_conversation(history: list[dict]) -> list:
    """Convert conversation history into Dash HTML components."""
    elements = []
    for entry in history:
        role = entry["role"]
        text = entry["text"]

        if role == "user":
            elements.append(
                html.Div(
                    className="message user-message",
                    children=[
                        html.Div("You", className="message-role"),
                        html.Div(text, className="message-text"),
                    ],
                )
            )
        else:
            # Agent response — parse into structured sections
            sections = _parse_agent_response(text)
            elements.append(
                html.Div(
                    className="message agent-message",
                    children=[
                        html.Div("Agent", className="message-role"),
                        html.Div(sections, className="message-text"),
                    ],
                )
            )
    return elements


def _parse_agent_response(text: str) -> list:
    """Parse agent text into structured Dash components.

    Detects sections like **Keywords:**, **Markets:**, **Recommendations:**
    and renders them as labelled blocks.  Falls back to plain text.
    """
    import re

    # Section headers the agent typically produces
    section_pattern = re.compile(
        r"(?:^|\n)\s*\*{0,2}(Keywords?|Markets?|Recommendations?|Summary|Next Steps)"
        r"[:\s]*\*{0,2}",
        re.IGNORECASE,
    )

    # If there are no recognisable sections, return as markdown
    if not section_pattern.search(text):
        return [dcc.Markdown(text, className="agent-markdown")]

    # Split on section headers and render each as a card
    parts = section_pattern.split(text)
    headers = section_pattern.findall(text)

    components: list = []

    # Leading text before the first header
    if parts and parts[0].strip():
        components.append(dcc.Markdown(parts[0].strip(), className="agent-markdown"))

    for header, body in zip(headers, parts[1:]):
        header = header.strip().rstrip(":")
        body = body.strip()
        if not body:
            continue

        icon = _section_icon(header.lower())
        components.append(
            html.Div(
                className=f"response-section section-{header.lower()}",
                children=[
                    html.H3(f"{icon} {header}", className="section-header"),
                    dcc.Markdown(body, className="section-body"),
                ],
            )
        )

    return components if components else [dcc.Markdown(text, className="agent-markdown")]


def _section_icon(header: str) -> str:
    """Return a simple text icon for a section header."""
    icons = {
        "keyword": "[KW]",
        "keywords": "[KW]",
        "market": "[MKT]",
        "markets": "[MKT]",
        "recommendation": "[REC]",
        "recommendations": "[REC]",
        "summary": "[SUM]",
        "next steps": "[>>]",
    }
    return icons.get(header, "[-]")


# ---------------------------------------------------------------------------
# Embedded CSS — keeps the app self-contained (no external assets needed)
# ---------------------------------------------------------------------------

app.index_string = """<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
        /* --- Reset & base --- */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #f5f7fa;
            color: #1a1a2e;
            line-height: 1.6;
        }

        /* --- App container --- */
        .app-container {
            max-width: 860px;
            margin: 0 auto;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* --- Header --- */
        .app-header {
            background: linear-gradient(135deg, #4A90D9 0%, #357ABD 100%);
            color: white;
            padding: 24px 32px;
            border-radius: 0 0 12px 12px;
        }
        .app-header h1 { font-size: 1.75rem; font-weight: 700; }
        .subtitle { opacity: 0.85; font-size: 0.95rem; margin-top: 4px; }

        /* --- Main content --- */
        .main-content {
            flex: 1;
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        /* --- Conversation thread --- */
        .conversation-thread {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 55vh;
            padding: 8px 0;
        }

        /* --- Messages --- */
        .message {
            padding: 14px 18px;
            border-radius: 10px;
            max-width: 92%;
        }
        .user-message {
            background: #e8f0fe;
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }
        .agent-message {
            background: #ffffff;
            align-self: flex-start;
            border: 1px solid #e0e4ea;
            border-bottom-left-radius: 2px;
        }
        .message-role {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #6b7280;
            margin-bottom: 4px;
        }
        .message-text { font-size: 0.95rem; white-space: pre-wrap; }
        .agent-markdown p { margin-bottom: 8px; }
        .agent-markdown ul, .agent-markdown ol { margin-left: 20px; margin-bottom: 8px; }
        .agent-markdown li { margin-bottom: 4px; }

        /* --- Response sections --- */
        .response-section {
            background: #f9fafb;
            border-left: 3px solid #4A90D9;
            border-radius: 6px;
            padding: 12px 16px;
            margin: 8px 0;
        }
        .section-keywords  { border-left-color: #10b981; }
        .section-markets   { border-left-color: #f59e0b; }
        .section-recommendations { border-left-color: #8b5cf6; }
        .section-header {
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 6px;
            color: #374151;
        }
        .section-body { font-size: 0.9rem; }

        /* --- Error banner --- */
        .error-banner {
            background: #fef2f2;
            color: #991b1b;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 0.9rem;
        }

        /* --- Preset prompts --- */
        .preset-prompts {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
        }
        .preset-label { font-size: 0.85rem; color: #6b7280; font-weight: 500; }
        .preset-btn {
            background: #fff;
            border: 1px solid #d1d5db;
            border-radius: 20px;
            padding: 6px 14px;
            font-size: 0.82rem;
            color: #374151;
            cursor: pointer;
            transition: all 0.15s;
        }
        .preset-btn:hover { background: #e8f0fe; border-color: #4A90D9; color: #1d4ed8; }

        /* --- Input area --- */
        .input-area {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        .user-input {
            flex: 1;
            resize: vertical;
            min-height: 56px;
            max-height: 160px;
            padding: 12px 16px;
            border: 1px solid #d1d5db;
            border-radius: 10px;
            font-size: 0.95rem;
            font-family: inherit;
            outline: none;
            transition: border-color 0.15s;
        }
        .user-input:focus { border-color: #4A90D9; box-shadow: 0 0 0 2px rgba(74,144,217,0.15); }
        .send-btn {
            background: #4A90D9;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 28px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s;
            white-space: nowrap;
        }
        .send-btn:hover { background: #357ABD; }
        .send-btn:active { background: #2563eb; }

        /* --- Footer --- */
        .app-footer {
            text-align: center;
            padding: 16px;
            font-size: 0.8rem;
            color: #9ca3af;
        }

        /* --- Loading --- */
        ._dash-loading { margin: 12px auto; }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
