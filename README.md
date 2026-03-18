# Keyword Researcher — Multi-Agent System + Dash UI

This repo contains the **Keyword Researcher** multi-agent system (Google ADK) and a candidate task to deploy it and build an interactive Dash UI.

## Current structure

```
agentic_media_buyer/
├── keyword_researcher/          # Multi-agent ADK package (given to candidates)
│   ├── __init__.py
│   ├── agent.py                 # Root agent + Keyword Analyst, Market, Recommendation agents
│   ├── prompt.py                # System instructions for each agent
│   ├── .env.example
│   └── .env                     # GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, MODEL, etc.
├── candidate_ui/
│   └── app.py                   # Dash scaffold for the interactive UI
├── deploy.py                    # Deploy Keyword Researcher to Vertex AI Agent Engine
├── requirements.txt
├── README.md
├── PROMPT_FOR_CANDIDATES.md     # Task instructions for candidates
└── AGENT_API.md                 # API contract for the deployed agent
```

## Multi-agent architecture

- **Root agent** (`keyword_researcher_agent`): Single entry point. Routes user messages to the right specialist(s), then returns a clear, structured reply (keywords, markets, or recommendations).
- **Keyword Analyst**: Discovers keywords for a topic, product, or seed list (via web search). Returns a structured list of keywords.
- **Market Agent**: Researches markets, segments, audiences, or regions. Returns a structured list of markets.
- **Recommendation Agent**: Produces actionable recommendations (prioritization, next steps, bid/campaign advice). Can use prior keyword/market context from the conversation.

All agents use **google_search**; the root uses **AgentTool** to invoke the specialists. Instructions are in `keyword_researcher/prompt.py`.

---

## For candidates: what to do

You are given the **multi-agent source code** in this repo. Your task has two parts:

1. **Deploy the Keyword Researcher** to your own **Google Cloud project** (Vertex AI Agent Engine), so you have a live endpoint.
2. **Build the interactive UI** using **Dash (Plotly)** that lets users send messages to the agent and see structured responses (keywords, markets, recommendations).

Full instructions are in [PROMPT_FOR_CANDIDATES.md](PROMPT_FOR_CANDIDATES.md). The API contract for the deployed agent is in [AGENT_API.md](AGENT_API.md).

---

## Deploy Keyword Researcher to Google Cloud

From the project root, with a GCP project and Vertex AI enabled:

1. Copy `keyword_researcher/.env.example` to `keyword_researcher/.env` and set:
   - `GOOGLE_CLOUD_PROJECT` — your GCP project ID  
   - `GOOGLE_CLOUD_LOCATION` — e.g. `us-central1`  
   - Optionally `STAGING_BUCKET`, `MODEL`, `REASONING_ENGINE_RESOURCE_NAME`

2. Install dependencies and deploy:

```bash
pip install -r requirements.txt
python deploy.py
```

3. Note the Agent Engine resource name or endpoint URL from the deploy output; you will use it as the base URL when building your Dash UI.

To update an existing deployment, set `REASONING_ENGINE_RESOURCE_NAME` in `.env` and run `python deploy.py` again.

## Run the agent locally (optional)

```bash
pip install -r requirements.txt
adk run keyword_researcher
# or: adk web --port 8000  (then select keyword_researcher)
```

For local run you can set `GOOGLE_API_KEY` in `keyword_researcher/.env` for Gemini API.

## Run the Dash UI scaffold

After deploying (or if using a local proxy), start the Dash app:

```bash
cd candidate_ui
pip install dash
python app.py
```

Open http://localhost:8050. Implement callbacks so the UI sends user messages to your deployed endpoint and displays the agent response (keywords, markets, recommendations) in a clear, structured way.

---

## Quick Start (Run Everything)

> `.env` file is included — no API key setup needed.

### Option A: Docker Compose (one command) -- Recommended and Easiest

```bash
docker-compose up -d
```

### Option B: Local (3 terminals) - Last Resort

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (source .venv/bin/activate on Mac/Linux)
pip install -r requirements.txt

# Terminal 1 — Agent server
adk web --port 8000

# Terminal 2 — Keyword Researcher UI
python -m candidate_ui.app

# Terminal 3 — Budget Pacing API
python -m budget_pacing.app
```

### URLs

| URL | Service | What You See |
|-----|---------|-------------|
| http://localhost:8050 | Keyword Researcher UI | Chat interface — ask for keywords, markets, recommendations |
| http://localhost:8080/apidocs | Budget Pacing API | Swagger UI — click "Try it out" to test POST /event and GET /bid |
| http://localhost:8000 | ADK Dev UI | Agent debug console (development only) |

### Run Tests

```bash
pytest budget_pacing/tests/ -v   # 57 passed (pacing, schemas, models, API)
pytest candidate_ui/tests/ -v    # 28 passed (rendering, parsing, SSE)
```
