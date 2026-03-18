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

---

## Exercise Implementation Details

### Project Structure (after implementation)

```
product_engineer_tech_exercise/
│
├── .env.example                        # Config template (committed, no secrets)
├── .env                                # Actual config (git-ignored, shared separately but added for convenience)
├── .gitignore
├── .dockerignore
├── Dockerfile                          # Shared image (Python 3.12-slim)
├── docker-compose.yml                  # Orchestrates all 3 services
├── requirements.txt                    # Unified Python dependencies
├── deploy.py                           # Deploy keyword_researcher to Vertex AI
├── SUBMISSION.md                       # Full technical deep-dive
├── CLOUD_SETUP.md                      # GCP setup walkthrough
│
├── budget_pacing/                      # TASK 1 — Budget Pacing Service
│   ├── app.py                          #   Flask application factory + Swagger
│   ├── config.py                       #   Configuration (reads BP_ env vars)
│   ├── services.py                     #   Business logic (pacing algorithm + circuit breaker)
│   ├── controllers/
│   │   ├── event_controller.py         #   POST /event — record auction wins
│   │   └── bid_controller.py           #   GET  /bid  — get paced bid recommendation
│   ├── models/
│   │   ├── database.py                 #   SQLAlchemy db singleton
│   │   ├── event.py                    #   Event model + get_daily_spend()
│   │   └── campaign.py                 #   CampaignConfig per-campaign overrides
│   ├── schemas/
│   │   ├── event_schema.py             #   EventRequest/Response (Pydantic v2)
│   │   └── bid_schema.py              #   BidRequest/Response (Pydantic v2)
│   ├── tests/                          #   57 tests
│   │   ├── conftest.py                 #     Shared fixtures (in-memory SQLite)
│   │   ├── test_pacing.py              #     14 pacing math tests
│   │   ├── test_schemas.py             #     13 validation tests
│   │   ├── test_models.py              #     6 model tests
│   │   ├── test_circuit_breaker.py     #     9 budget safety tests
│   │   ├── test_api_events.py          #     8 POST /event integration tests
│   │   └── test_api_bids.py            #     7 GET /bid integration tests
│   └── INTERVIEW.md                    #   Interview prep document
│
├── candidate_ui/                       # TASK 2 — Keyword Researcher Dash UI
│   ├── app.py                          #   Application factory & entry-point
│   ├── layout.py                       #   Dash component tree (sidebar + main panel)
│   ├── callbacks.py                    #   All callback registrations (consolidated)
│   ├── components.py                   #   Pure rendering/parsing helpers
│   ├── agent_client.py                 #   Backend client (local ADK / Vertex AI)
│   ├── assets/
│   │   └── styles.css                  #   CSS (auto-served by Dash convention)
│   └── tests/                          #   28 tests
│       ├── test_components.py          #     18 rendering/parsing tests
│       └── test_agent_client.py        #     10 SSE parser tests
│
└── keyword_researcher/                 # GIVEN — Multi-agent ADK package
    ├── agent.py                        #   Root agent + 3 specialist sub-agents
    └── prompt.py                       #   System instructions per agent
```

---

### Task 1: Budget Pacing Service — Architecture

**What it does:** Recommends optimised bids for ad campaigns to spread daily budget evenly throughout the day.

**Pattern:** MVC (Model-View-Controller) with Application Factory

```
                    ┌──────────────────────────────────────────────┐
  HTTP Request      │              Flask Application               │
  ──────────────>   │                                              │
                    │  controllers/        services.py             │
  POST /event  ───> │  event_controller ──> BudgetPacingService    │
                    │                       ├─ record_event()      │
                    │                       │  (circuit breaker)   │
  GET  /bid    ───> │  bid_controller   ──> ├─ get_bid()           │
                    │                       │  (pacing algorithm)  │
                    │                       │                      │
                    │  schemas/             models/                │
                    │  Pydantic v2    <──>  SQLAlchemy (SQLite)    │
                    │  (validation)         (persistence)          │
                    │                                              │
                    │  Flasgger ──> Swagger UI at /apidocs         │
                    └──────────────────────────────────────────────┘
```

**Key algorithms:**
- **Inverse-ratio pacing:** `bid = base_bid × clamp(1/spend_ratio, min, max)` — bids up when behind schedule, down when ahead
- **Circuit breaker:** Rejects events that would exceed daily budget (HTTP 409), returns `bid=0` when limit is reached

---

### Task 2: Keyword Researcher UI — Architecture

**What it does:** Chat interface to a multi-agent AI system that discovers keywords, analyses markets, and generates campaign recommendations.

**Pattern:** Modular Dash with Application Factory + Separation of Concerns

```
┌─────────────────────────────────────────────────────┐
│  candidate_ui/ (Dash App)                           │
│                                                     │
│  app.py ─── create_app() factory                    │
│    ├── layout.py     → Component tree (sidebar +    │
│    │                    main chat panel)            │
│    ├── callbacks.py  → Consolidated event handlers  │
│    │     │                                          │
│    │     ├── new-chat-btn  ─┐                       │
│    │     ├── conv-btn       ├─> Single callback     │
│    │     └── send-btn      ─┘   (ctx.triggered_id)  │
│    │                                                │
│    ├── components.py → Pure rendering helpers       │       ┌──────────────────┐
│    │     ├── render_conversation()                  │       │  ADK Agent       │
│    │     ├── parse_agent_response()                 │       │  (port 8000)     │
│    │     └── truncate_title()                       │       │                  │
│    │                                                │       │  Root Agent      │
│    └── agent_client.py ─────────────────────────────│──────>│  ├── Keyword     │
│          ├── mode: "local" or "vertex"              │       │  ├── Market      │
│          ├── create_session()                       │       │  └── Recommend.  │
│          ├── send_message()                         │       │                  │
│          └── parse_adk_response()                   │<──────│  Gemini 2.5 Flash│
│                                                     │       │  + google_search │
│  assets/styles.css → Dash auto-served CSS           │       └──────────────────┘
│  dcc.Store (localStorage) → Persistent conversations│
└─────────────────────────────────────────────────────┘
```

**Key features:**
- **Conversation sidebar** — persistent history in browser localStorage, switch between chats
- **Dual backend** — auto-detects local ADK vs Vertex AI from env vars
- **Structured parsing** — agent responses split into colour-coded Keywords/Markets/Recommendations cards
- **XSS protection** — `dangerously_allow_html=False` on all Markdown rendering

---

### How the 3 Services Connect (Docker Compose)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  dash-ui     │────>│  agent       │     │ budget-pacing│
│  port 8050   │     │  port 8000   │     │ port 8080    │
│              │     │              │     │              │
│  Dash UI     │     │  ADK Server  │     │  Flask API   │
│  (chat)      │     │  (Gemini AI) │     │  (Swagger)   │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                     │
       └──── depends_on ────┘                     │
             (healthcheck)              (independent service)
```

---

## Quick Start (Run Everything)

> `.env` file is included — no API key setup needed.

### Clone Repo

```bash
git clone https://github.com/Patelraj8694/together_excercise.git
```

### Directory

```bash
cd together_excercise
```

### Option A: Docker Compose (one command) — Recommended

```bash
docker-compose up -d
```

### Option B: Local (3 terminals)

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

### Run Tests (85 total)

```bash
pytest budget_pacing/tests/ -v   # 57 passed (pacing, schemas, models, API)
pytest candidate_ui/tests/ -v    # 28 passed (rendering, parsing, SSE)
```