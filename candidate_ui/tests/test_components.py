"""Tests for candidate_ui.components — pure rendering helpers."""

import pytest
from dash import html, dcc

from candidate_ui.components import (
    truncate_title,
    render_conversation,
    parse_agent_response,
)


# ---------------------------------------------------------------------------
# truncate_title
# ---------------------------------------------------------------------------

class TestTruncateTitle:
    def test_short_text_unchanged(self):
        assert truncate_title("hello") == "hello"

    def test_exact_limit_unchanged(self):
        text = "x" * 50
        assert truncate_title(text) == text

    def test_long_text_truncated(self):
        text = "x" * 60
        result = truncate_title(text)
        assert result == "x" * 50 + "..."
        assert len(result) == 53

    def test_custom_limit(self):
        assert truncate_title("abcdef", max_len=3) == "abc..."

    def test_empty_string(self):
        assert truncate_title("") == ""


# ---------------------------------------------------------------------------
# render_conversation
# ---------------------------------------------------------------------------

class TestRenderConversation:
    def test_empty_history(self):
        assert render_conversation([]) == []

    def test_user_message(self):
        history = [{"role": "user", "text": "hello"}]
        result = render_conversation(history)
        assert len(result) == 1
        assert "user-message" in result[0].className

    def test_agent_message(self):
        history = [{"role": "agent", "text": "world"}]
        result = render_conversation(history)
        assert len(result) == 1
        assert "agent-message" in result[0].className

    def test_alternating_messages(self):
        history = [
            {"role": "user", "text": "Find keywords"},
            {"role": "agent", "text": "Here are keywords"},
            {"role": "user", "text": "Thanks"},
        ]
        result = render_conversation(history)
        assert len(result) == 3
        assert "user-message" in result[0].className
        assert "agent-message" in result[1].className
        assert "user-message" in result[2].className

    def test_message_role_labels(self):
        history = [
            {"role": "user", "text": "hi"},
            {"role": "agent", "text": "hello"},
        ]
        result = render_conversation(history)
        # First child of each message div is the role label
        assert result[0].children[0].children == "You"
        assert result[1].children[0].children == "Agent"


# ---------------------------------------------------------------------------
# parse_agent_response
# ---------------------------------------------------------------------------

class TestParseAgentResponse:
    def test_plain_text_returns_markdown(self):
        """Text with no recognised headers → plain markdown."""
        result = parse_agent_response("Just a normal reply.")
        assert len(result) == 1
        assert isinstance(result[0], dcc.Markdown)

    def test_keywords_section_detected(self):
        text = "**Keywords:**\n- running shoes\n- trail running"
        result = parse_agent_response(text)
        # Should produce at least one response-section div
        sections = [c for c in result if hasattr(c, "className") and "response-section" in (c.className or "")]
        assert len(sections) >= 1

    def test_markets_section_detected(self):
        text = "**Markets:**\n- North America\n- Europe"
        result = parse_agent_response(text)
        sections = [c for c in result if hasattr(c, "className") and "section-market" in (c.className or "")]
        assert len(sections) >= 1

    def test_recommendations_section_detected(self):
        text = "**Recommendations:**\n1. Increase bid\n2. Expand targeting"
        result = parse_agent_response(text)
        sections = [c for c in result if hasattr(c, "className") and "section-recommendation" in (c.className or "")]
        assert len(sections) >= 1

    def test_multiple_sections(self):
        text = (
            "Here is your analysis:\n\n"
            "**Keywords:**\n- shoes\n- sneakers\n\n"
            "**Markets:**\n- US\n- UK\n\n"
            "**Recommendations:**\n1. Focus on US first"
        )
        result = parse_agent_response(text)
        sections = [c for c in result if hasattr(c, "className") and "response-section" in (c.className or "")]
        assert len(sections) == 3

    def test_case_insensitive(self):
        text = "keywords:\n- test keyword"
        result = parse_agent_response(text)
        sections = [c for c in result if hasattr(c, "className") and "response-section" in (c.className or "")]
        assert len(sections) >= 1

    def test_dangerously_allow_html_is_false(self):
        """Ensure XSS protection: dangerously_allow_html must be False."""
        result = parse_agent_response("plain text")
        md = result[0]
        assert isinstance(md, dcc.Markdown)
        assert md.dangerously_allow_html is False

    def test_empty_string(self):
        result = parse_agent_response("")
        assert len(result) == 1
        assert isinstance(result[0], dcc.Markdown)
