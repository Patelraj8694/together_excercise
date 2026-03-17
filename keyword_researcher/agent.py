"""
ADK root agent: Keyword Researcher orchestrator for search and media campaigns.

Orchestrates specialist sub-agents (Keyword Analyst, Market Agent, Recommendation
Agent) via AgentTool. The root agent routes user requests to the appropriate
specialist(s) and synthesizes their outputs for the dashboard.
"""

import os

from google.adk.agents.llm_agent import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search

from .prompt import (
    KEYWORD_RESEARCHER_ROOT_PROMPT,
    KEYWORD_ANALYST_PROMPT,
    MARKET_AGENT_PROMPT,
    RECOMMENDATION_AGENT_PROMPT,
)

# Default model for all agents; override with MODEL env var (e.g. gemini-2.5-flash).
_DEFAULT_MODEL = "gemini-2.5-flash"

# --- Specialist sub-agents (invoked by the root agent via AgentTool) ---

keyword_analyst_agent = Agent(
    name="keyword_analyst_agent",
    model=os.getenv("MODEL", _DEFAULT_MODEL),
    instruction=KEYWORD_ANALYST_PROMPT,
    description="Researches keywords related to a topic, product, or seed list. Use when the user wants keyword discovery, related terms, or search query ideas. Returns a structured list of keywords.",
    output_key="keyword_analyst_output",
    tools=[google_search],
)

market_agent = Agent(
    name="market_agent",
    model=os.getenv("MODEL", _DEFAULT_MODEL),
    instruction=MARKET_AGENT_PROMPT,
    description="Researches markets, segments, audiences, or regions for a product or campaign. Use when the user wants market/audience research or where to focus. Returns a structured list of markets.",
    output_key="market_output",
    tools=[google_search],
)

recommendation_agent = Agent(
    name="recommendation_agent",
    model=os.getenv("MODEL", _DEFAULT_MODEL),
    instruction=RECOMMENDATION_AGENT_PROMPT,
    description="Produces actionable recommendations (prioritization, next steps, bid/campaign advice). Use when the user asks what to do next or for recommendations; can use prior keyword/market context. Returns a list of recommendations.",
    output_key="recommendation_output",
    tools=[google_search],
)

# --- Root orchestrator agent (entry point for deployment and chat) ---

root_agent = Agent(
    model=os.getenv("MODEL", _DEFAULT_MODEL),
    name="keyword_researcher_agent",
    description="Orchestrates keyword research: discovers keywords, markets, and recommendations via specialist agents. Use for any keyword or campaign research request.",
    instruction=KEYWORD_RESEARCHER_ROOT_PROMPT,
    tools=[
        AgentTool(keyword_analyst_agent),
        AgentTool(market_agent),
        AgentTool(recommendation_agent),
    ],
)
