"""Tests for candidate_ui.agent_client — SSE response parsing."""

import pytest

from candidate_ui.agent_client import AgentClient


class TestParseAdkResponse:
    """Tests for the static SSE parser used in local-ADK mode."""

    def test_single_model_event(self):
        raw = (
            'data: {"content": {"role": "model", '
            '"parts": [{"text": "Hello from the agent"}]}}\n'
        )
        assert AgentClient.parse_adk_response(raw) == "Hello from the agent"

    def test_multiple_events_returns_last(self):
        raw = (
            'data: {"content": {"role": "model", "parts": [{"text": "first"}]}}\n'
            'data: {"content": {"role": "model", "parts": [{"text": "second"}]}}\n'
        )
        assert AgentClient.parse_adk_response(raw) == "second"

    def test_ignores_non_model_roles(self):
        raw = (
            'data: {"content": {"role": "user", "parts": [{"text": "should ignore"}]}}\n'
            'data: {"content": {"role": "model", "parts": [{"text": "agent reply"}]}}\n'
        )
        assert AgentClient.parse_adk_response(raw) == "agent reply"

    def test_ignores_malformed_json(self):
        raw = (
            "data: {invalid json}\n"
            'data: {"content": {"role": "model", "parts": [{"text": "ok"}]}}\n'
        )
        assert AgentClient.parse_adk_response(raw) == "ok"

    def test_empty_data_line(self):
        raw = "data: \n"
        assert AgentClient.parse_adk_response(raw) == ""

    def test_no_data_prefix(self):
        raw = "event: ping\nid: 123\n"
        assert AgentClient.parse_adk_response(raw) == ""

    def test_empty_string(self):
        assert AgentClient.parse_adk_response("") == ""

    def test_content_without_parts(self):
        raw = 'data: {"content": {"role": "model"}}\n'
        assert AgentClient.parse_adk_response(raw) == ""

    def test_content_not_dict(self):
        raw = 'data: {"content": "plain string"}\n'
        assert AgentClient.parse_adk_response(raw) == ""

    def test_mixed_events_with_blanks(self):
        raw = (
            "data: \n"
            "\n"
            'data: {"content": {"role": "model", "parts": [{"text": "answer"}]}}\n'
            "\n"
        )
        assert AgentClient.parse_adk_response(raw) == "answer"
