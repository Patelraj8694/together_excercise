# Keyword Researcher: Deploy + Dash UI

## Mission

You are given the **Keyword Researcher** multi-agent source code. Your job is to:

1. **Deploy the Keyword Researcher** to your own **Google Cloud project** (Vertex AI Agent Engine).
2. **Build an interactive UI** using **Dash (Plotly)** so users can ask the agent questions and see clear, structured responses (keyword lists, market segments, and recommendations).

## What is keyword research (and why it matters)

You don’t need advertising experience for this task, but a little context helps. **Keyword research** is the process of finding and choosing the words and phrases (keywords) that people type into search engines (e.g. Google) when looking for a product, service, or topic. In **search advertising** (e.g. Google Ads), advertisers bid on those keywords so their ads can appear when someone searches for them. Good keyword research helps:

- **Reach the right people** — Choose terms that match how your audience actually searches (e.g. “best running shoes for flat feet” vs. “running shoes”).
- **Spend budget wisely** — Focus on terms that are relevant and likely to convert, and avoid terms that are too broad, too niche, or not aligned with the product.
- **Plan campaigns** — Group keywords into themes (e.g. brand vs. product vs. competitor), decide which **markets** (regions, audiences, or segments) to target, and get **recommendations** on what to do next.

The **Keyword Researcher** agent in this repo automates part of that work: it discovers keywords, suggests relevant markets, and gives actionable recommendations. Your job is to deploy that agent and build a UI where users can ask it questions and see those results in a clear, usable way.

## What you're given

- **Multi-agent source code** in this repo:
  - `keyword_researcher/` — ADK package: `agent.py` (root + Keyword Analyst, Market Agent, Recommendation Agent), `prompt.py`, `.env.example`.
  - `deploy.py` — Script to deploy the agent to Vertex AI Agent Engine.
- **API documentation** ([AGENT_API.md](AGENT_API.md)) describing the conversational API (session-based; send message, receive agent response with keywords, markets, or recommendations).
- **Dash scaffold** in `candidate_ui/app.py` — minimal layout; you implement the callbacks and wiring to your deployed endpoint.

## Your task (two steps)

### Step 1: Deploy the Keyword Researcher to your Google Cloud project

1. Create or use a Google Cloud project with Vertex AI (and Agent Engine) enabled.
2. Copy `keyword_researcher/.env.example` to `keyword_researcher/.env` and set:
   - `GOOGLE_CLOUD_PROJECT` — your GCP project ID  
   - `GOOGLE_CLOUD_LOCATION` — e.g. `us-central1`  
   - Optionally `STAGING_BUCKET` (for deploy artifacts).
3. From the project root, run:
   ```bash
   pip install -r requirements.txt
   python deploy.py
   ```
4. Save the Agent Engine resource name or endpoint URL from the output; you will use it as the base URL in your Dash app.

### Step 2: Build the interactive UI using Dash

Build a **Dash (Plotly)** UI that:

1. **Lets the user ask questions**  
   A text input (and/or preset prompts) so the user can ask for keywords, markets, or recommendations (e.g. “Find keywords for running shoes”, “Which markets for B2B SaaS?”, “What should I do next?”).

2. **Sends the message to your deployed endpoint and displays the response**  
   Call your Vertex AI Agent Engine endpoint to submit the user’s message and show the agent’s reply. Structure the display so that **keywords**, **markets**, and **recommendations** are easy to scan (e.g. lists, sections, or simple tables). Handle loading state and errors.

3. **(Optional)** **Conversation history**  
   Keep a short history of turns (user message + agent response) so the user can refer back or ask follow-ups in context.

Use the Dash scaffold in `candidate_ui/app.py` as a starting point; configure the API base URL to point at your deployed Agent Engine.

## Technical focus

- **Deployment:** Successfully deploying the ADK agent to Vertex AI and obtaining a working endpoint.
- **State management:** Handling async or slow endpoint calls in Dash (e.g. loading states, `dcc.Store` for session id, messages, or last response).
- **Product sense:** Is the information (keywords, markets, recommendations) presented clearly enough for a media buyer or campaign manager to act on?
- **Integration:** Using the API so that each user message is sent to the agent and the response is shown in your UI.

## Optional note

In a real product this might power search ad keyword research, campaign planning, or market prioritization; here we keep the scenario focused so you can concentrate on deployment and the dashboard.
