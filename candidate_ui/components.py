"""Reusable rendering helpers for the Keyword Researcher Dash UI.

Pure functions — no side effects, no Dash app dependency, trivially testable.
"""

import re

from dash import dcc, html


# Section headers the agent typically produces
_SECTION_PATTERN = re.compile(
    r"(?:^|\n)\s*\*{0,2}(Keywords?|Markets?|Recommendations?|Summary|Next Steps)"
    r"[:\s]*\*{0,2}",
    re.IGNORECASE,
)

_SECTION_ICONS: dict[str, str] = {
    "keyword": "[KW]",
    "keywords": "[KW]",
    "market": "[MKT]",
    "markets": "[MKT]",
    "recommendation": "[REC]",
    "recommendations": "[REC]",
    "summary": "[SUM]",
    "next steps": "[>>]",
}

MAX_TITLE_LENGTH = 50


def truncate_title(text: str, max_len: int = MAX_TITLE_LENGTH) -> str:
    """Truncate text to *max_len* characters, appending '...' if needed."""
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def render_conversation(history: list[dict]) -> list:
    """Convert conversation history into Dash HTML components."""
    elements: list = []
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
            sections = parse_agent_response(text)
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


def parse_agent_response(text: str) -> list:
    """Parse agent text into structured Dash components.

    Detects sections like **Keywords:**, **Markets:**, **Recommendations:**
    and renders them as labelled blocks.  Falls back to plain markdown.
    """
    if not _SECTION_PATTERN.search(text):
        return [dcc.Markdown(text, dangerously_allow_html=False, className="agent-markdown")]

    # re.split with a capturing group interleaves captured headers into the
    # result: [leading, header1, body1, header2, body2, ...]
    parts = _SECTION_PATTERN.split(text)

    components: list = []

    # Leading text before the first header (parts[0])
    if parts[0].strip():
        components.append(
            dcc.Markdown(parts[0].strip(), dangerously_allow_html=False, className="agent-markdown")
        )

    # Iterate header/body pairs via stride-2 indexing
    for header, body in zip(parts[1::2], parts[2::2]):
        header = header.strip().rstrip(":")
        body = body.strip()
        if not body:
            continue

        css_class = header.lower().replace(" ", "-")
        icon = _SECTION_ICONS.get(header.lower(), "[-]")
        components.append(
            html.Div(
                className=f"response-section section-{css_class}",
                children=[
                    html.H3(f"{icon} {header}", className="section-header"),
                    dcc.Markdown(body, dangerously_allow_html=False, className="section-body"),
                ],
            )
        )

    return components if components else [
        dcc.Markdown(text, dangerously_allow_html=False, className="agent-markdown")
    ]
