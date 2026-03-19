"""Client for communicating with the deployed Keyword Researcher agent.

Supports two backends:
  1. **Vertex AI Agent Engine** (production) — uses the google-cloud-aiplatform SDK
  2. **Local ADK** (development) — calls the local ``adk web`` server via HTTP

The backend is selected automatically based on whether
``REASONING_ENGINE_RESOURCE_NAME`` is set in the environment.
"""

import json
import os

import requests

__all__ = ["AgentClient"]


class AgentClient:
    """Thin wrapper that sends user messages to the Keyword Researcher agent
    and returns the agent's text response.
    """

    def __init__(self) -> None:
        self._resource_name = os.getenv("REASONING_ENGINE_RESOURCE_NAME", "").strip()
        self._project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
        self._location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1").strip()
        self._local_url = os.getenv("ADK_LOCAL_URL", "http://localhost:8000").strip()

        self._remote_app = None

        if self._resource_name and self._project:
            self.mode = "vertex"
            self._init_vertex()
        else:
            self.mode = "local"

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_vertex(self) -> None:
        """Connect to the deployed Vertex AI Agent Engine."""
        import vertexai

        client = vertexai.Client(
            project=self._project, location=self._location
        )
        self._remote_app = client.agent_engines.get(self._resource_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_session(self) -> str:
        """Create a new conversation session and return its ID."""
        if self.mode == "vertex":
            session = self._remote_app.create_session()
            return session.id if hasattr(session, "id") else str(session)
        return self._create_local_session()

    def send_message(self, session_id: str, message: str) -> str:
        """Send *message* to the agent in the given session.

        Returns the agent's text reply.
        """
        if self.mode == "vertex":
            return self._send_vertex(session_id, message)
        return self._send_local(session_id, message)

    # ------------------------------------------------------------------
    # Vertex AI backend
    # ------------------------------------------------------------------

    def _send_vertex(self, session_id: str, message: str) -> str:
        """Send a message via the Vertex AI Agent Engine SDK."""
        response = self._remote_app.send_message(
            session_id=session_id,
            message=message,
        )
        # The SDK may return different shapes — handle them gracefully
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            return response.get("response") or response.get("content") or str(response)
        if hasattr(response, "text"):
            return response.text
        if hasattr(response, "content"):
            return response.content
        return str(response)

    # ------------------------------------------------------------------
    # Local ADK backend
    # ------------------------------------------------------------------

    def _create_local_session(self) -> str:
        """Create a session on the local ADK server via its REST API."""
        url = f"{self._local_url}/apps/keyword_researcher/users/dash_user/sessions"
        try:
            resp = requests.post(url, json={}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            session_id = data.get("id")
            if not session_id:
                raise ConnectionError(
                    f"ADK server returned no session ID. Response: {data}"
                )
            return session_id
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to local ADK server at {self._local_url}. "
                f"Run: adk web --port 8000"
            )
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(
                f"ADK server error: {exc}"
            )

    def _send_local(self, session_id: str, message: str) -> str:
        """Send a message to the local ``adk web`` server via HTTP."""
        url = f"{self._local_url}/run_sse"
        payload = {
            "app_name": "keyword_researcher",
            "user_id": "dash_user",
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}],
            },
            "streaming": False,
        }
        try:
            resp = requests.post(url, json=payload, timeout=120)

            # Session expired (server restarted) — create a new one and retry
            if resp.status_code == 404:
                new_session_id = self._create_local_session()
                payload["session_id"] = new_session_id
                self._last_new_session_id = new_session_id
                resp = requests.post(url, json=payload, timeout=120)

            resp.raise_for_status()

            # Parse SSE-style response — extract the last agent text
            agent_text = self.parse_adk_response(resp.text)
            return agent_text if agent_text else resp.text
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to local ADK server at {self._local_url}. "
                f"Run: adk web --port 8000"
            )
        except requests.exceptions.RequestException as exc:
            raise ConnectionError(
                f"ADK server error: {exc}"
            )

    @staticmethod
    def parse_adk_response(raw: str) -> str:
        """Extract the final agent text from an ADK SSE response."""
        agent_text = ""
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                if not data_str:
                    continue
                try:
                    data = json.loads(data_str)
                    content = data.get("content", {})
                    if isinstance(content, dict):
                        parts = content.get("parts", [])
                        for part in parts:
                            if isinstance(part, dict) and "text" in part:
                                role = content.get("role", "")
                                if role == "model":
                                    agent_text = part["text"]
                except (json.JSONDecodeError, AttributeError):
                    continue
        return agent_text
