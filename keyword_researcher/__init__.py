"""Keyword Researcher: ADK-based agent for keyword and market research.

This package provides a root agent that orchestrates specialist sub-agents
(Keyword Analyst, Market Agent, Recommendation Agent) for search and media
campaign research. Use the `agent` module to access the root agent and
deploy or run it via the ADK.
"""

from . import agent

__all__ = ["agent"]