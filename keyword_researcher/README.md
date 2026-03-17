# Keyword Researcher — Multi-agent ADK package

This package implements the **Keyword Researcher** multi-agent system using [Google ADK](https://google.github.io/adk-docs/).

## Structure

- **agent.py** — Defines `root_agent` (orchestrator) and three sub-agents: `keyword_analyst_agent`, `market_agent`, `recommendation_agent`. Each sub-agent is exposed to the root via `AgentTool`; all use `google_search`.
- **prompt.py** — System instructions for the root and each specialist (routing, keyword discovery, market research, recommendations).
- **.env** / **.env.example** — `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `MODEL`; optional `STAGING_BUCKET`, `REASONING_ENGINE_RESOURCE_NAME`, `GOOGLE_API_KEY` (for local `adk run`).

## Deploy

From the **project root** (parent of `keyword_researcher/`):

```bash
pip install -r requirements.txt
python deploy.py
```

Ensure `keyword_researcher/.env` is set with your GCP project and location before deploying.

## Run locally

From the project root:

```bash
adk run keyword_researcher
# or: adk web --port 8000
```

Set `GOOGLE_API_KEY` in `.env` for Gemini API when running locally.
