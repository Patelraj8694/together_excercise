"""Layout definition for the Keyword Researcher Dash UI.

Separated from callbacks to follow single-responsibility principle.
CSS is auto-loaded from assets/styles.css by Dash.
"""

from dash import dcc, html

# ---------------------------------------------------------------------------
# Preset prompts — quick-start buttons for common research queries
# ---------------------------------------------------------------------------

PRESET_PROMPTS: list[str] = [
    "Find keywords for running shoes",
    "What markets should I target for B2B SaaS?",
    "Give me recommendations for my search campaign",
    "Keywords and markets for organic skincare products",
]


def create_layout(backend_mode: str) -> html.Div:
    """Build the top-level Dash layout.

    Parameters
    ----------
    backend_mode:
        "local" or "vertex" — displayed in the footer.
    """
    return html.Div(
        className="app-wrapper",
        children=[
            # --- Hidden stores (all localStorage for persistence) ---
            dcc.Store(id="session-id", storage_type="local"),
            dcc.Store(id="conversation-history", data=[], storage_type="local"),
            dcc.Store(id="all-conversations", data={}, storage_type="local"),
            dcc.Store(id="active-conversation-id", data=None, storage_type="local"),

            # --- Left sidebar: conversation history ---
            html.Aside(
                className="sidebar",
                children=[
                    html.Div(
                        className="sidebar-header",
                        children=[
                            html.H2("Conversations"),
                            html.Button(
                                "+ New Chat",
                                id="new-chat-btn",
                                className="new-chat-btn",
                                n_clicks=0,
                            ),
                        ],
                    ),
                    html.Div(id="conversation-list", className="conversation-list"),
                ],
            ),

            # --- Main panel ---
            html.Div(
                className="app-container",
                children=[
                    # Header
                    html.Header(
                        className="app-header",
                        children=[
                            html.H1("Keyword Researcher"),
                            html.P(
                                "Multi-agent research assistant for keywords, "
                                "markets & recommendations.",
                                className="subtitle",
                            ),
                        ],
                    ),

                    # Main content area
                    html.Main(
                        className="main-content",
                        children=[
                            html.Div(
                                id="conversation-thread",
                                className="conversation-thread",
                            ),
                            dcc.Loading(
                                id="loading-indicator",
                                type="dot",
                                color="#4A90D9",
                                children=html.Div(id="loading-target"),
                            ),
                            html.Div(
                                id="error-banner",
                                className="error-banner",
                                style={"display": "none"},
                            ),
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
                                        placeholder="Ask about keywords, markets, "
                                        "or campaign recommendations...",
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

                    # Footer
                    html.Footer(
                        className="app-footer",
                        children=[
                            html.Span(f"Backend: {backend_mode}"),
                            html.Span(" | "),
                            html.Span("Powered by Google ADK + Gemini"),
                        ],
                    ),
                ],
            ),
        ],
    )
