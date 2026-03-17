# Candidate UI — Dash scaffold

This folder contains the **Dash (Plotly)** scaffold for the Keyword Researcher interactive UI.

**Your task:** After deploying the Keyword Researcher to your Google Cloud project (see root [PROMPT_FOR_CANDIDATES.md](../PROMPT_FOR_CANDIDATES.md)), build the UI here so users can send messages to the agent and see structured responses (keywords, markets, recommendations).

- **app.py** — Minimal layout (input, send button, response area). Implement callbacks to call your deployed Vertex AI Agent Engine endpoint and display the agent’s reply.
- Set `API_BASE_URL` in `app.py` to your deployed Agent Engine endpoint.

Run from this directory:

```bash
pip install dash
python app.py
```

Then open http://localhost:8050.
