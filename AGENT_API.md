# Keyword Researcher Multi-Agent API Documentation

This document describes the **API contract** for the Keyword Researcher multi-agent system. You have the multi-agent source code in this repo and will **deploy it to your own Google Cloud project** via `deploy.py`. The deployed **Vertex AI Agent Engine** serves this API. For local development you can run `adk run keyword_researcher` or `adk web`; the same conversational pattern applies.

## Purpose of the multi-agent

The system is a **conversational agent**: the user sends a message (e.g. “Find keywords for CRM software”, “Which markets for fitness apps?”, “Recommendations for these keywords”), and the agent returns a single reply. Internally, a **root agent** orchestrates up to three specialist agents:

1. **Keyword Analyst** — Discovers keywords for a topic or seed list (uses web search).
2. **Market Agent** — Researches markets, segments, or regions (uses web search).
3. **Recommendation Agent** — Produces actionable recommendations (uses web search and prior context).

You do **not** call these specialists directly; you send a **user message** to the single endpoint and receive one **agent response** per turn.

---

## Base URL and authentication

- **Production (Vertex AI):** After you run `python deploy.py`, your Agent Engine will have a resource name and (depending on setup) an endpoint URL. Use that as the base URL in your Dash UI. Authentication (e.g. `Authorization: Bearer <token>`, API key, or service account) follows Vertex AI / Agent Engine documentation; use the same credentials that have access to your GCP project.
- **Local development:** Run `adk run keyword_researcher` or `adk web` and use the URL and session mechanism provided by the ADK (or a local proxy that mimics the production API).

---

## Conversation model

The API is **session-based** and **turn-based**:

1. **Create or reuse a session** (exact path and payload depend on the Vertex AI Agent Engine or local setup; the interviewer will provide details).
2. **Send a user message** (e.g. POST to a path like `/sessions/{session_id}/messages` or equivalent) with a body such as `{"message": "Find keywords for running shoes"}`.
3. **Receive the agent response** in the reply (e.g. JSON with a `response` or `content` field containing the agent’s text).

The agent’s reply is **plain text** (possibly with markdown-style formatting). It is written to be dashboard-friendly and may contain:

- **Keywords**: A list of search terms or key phrases, sometimes grouped (e.g. by intent or theme).
- **Markets**: A list of segments, regions, or verticals with short notes.
- **Recommendations**: A numbered or bulleted list of actionable suggestions.

Your UI should **parse or display** this text in a structured way (e.g. split into “Keywords”, “Markets”, “Recommendations” sections if the agent uses those headings, or render as formatted text).

---

## Typical request (conceptual)

- **Method:** `POST`
- **Path:** As provided by the interviewer (e.g. send-message or session-message endpoint).
- **Body (example):**

```json
{
  "message": "Find keywords for running shoes",
  "session_id": "optional-if-session-created-separately"
}
```

---

## Typical response (conceptual)

- **Status:** `200 OK`
- **Body (example):**

```json
{
  "response": "Here are **keywords** for running shoes:\n\n- best running shoes 2024\n- marathon training shoes\n- lightweight running shoes\n\n...",
  "session_id": "abc123"
}
```

The `response` (or equivalent) field contains the full agent reply. Structure (keywords, markets, recommendations) is conveyed in the text; your dashboard can render it as-is or parse sections for a richer layout.

---

## Summary for your Dash UI

1. **Send user message:** Call the endpoint with the user’s question (and session id if required). Show a loading state while waiting.
2. **Display agent response:** Show the returned text in a readable way. Optionally detect or parse “Keywords”, “Markets”, and “Recommendations” and render them as lists or cards.
3. **Handle errors:** If the request fails, show a clear message and allow the user to retry or rephrase.
4. **(Optional)** Keep a short conversation history (user + agent turns) so follow-up questions have context.

Exact endpoint paths and request/response field names depend on the Vertex AI Agent Engine API you get after running `deploy.py`; see the deploy output and Vertex AI Agent Engine documentation for your environment.
