"""Deploy Keyword Researcher agent to Vertex AI Agent Engine via the ADK Python SDK.

Run from the project root:
  uv run python deploy.py
  # or: python deploy.py (with venv activated)

Requires env: GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION; optional: STAGING_BUCKET, REASONING_ENGINE_RESOURCE_NAME.
Uses config from keyword_researcher/.env and optional .env at project root.
Set REASONING_ENGINE_RESOURCE_NAME to update an existing Agent Engine; otherwise a new one is created.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
import vertexai
from vertexai.agent_engines import AdkApp

from keyword_researcher.agent import root_agent

load_dotenv(Path(__file__).resolve().parent / "keyword_researcher" / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

# Pinned requirements so local and remote match (avoid cloudpickle/pydantic serialization issues).
DEPLOY_REQUIREMENTS = [
    "google-cloud-aiplatform[adk,agent_engines]>=1.120.0",  # Vertex AI ADK and Agent Engine APIs
    "pydantic==2.12.2",   # Pin to avoid serialization mismatches between local and deployed runtime
    "cloudpickle==3.1.2", # Pin for consistent agent/tool serialization in the cloud
]


def main() -> None:
    """Deploy or update the Keyword Researcher agent on Vertex AI Agent Engine.

    Reads GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION from env. If
    REASONING_ENGINE_RESOURCE_NAME is set, updates that Agent Engine; otherwise
    creates a new one. Loads .env from keyword_researcher/ and project root.
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")
    if not project or not location:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set (e.g. in keyword_researcher/.env or .env)"
        )
    client = vertexai.Client(project=project, location=location)
    app = AdkApp(agent=root_agent, enable_tracing=True)
    # Include only the agent package so .venv and candidate_ui are not in the tarball.
    agent_package_dir = str(Path(__file__).resolve().parent / "keyword_researcher")
    agent_config = {
        "requirements": DEPLOY_REQUIREMENTS,
        "extra_packages": [agent_package_dir],
        "staging_bucket": os.getenv("STAGING_BUCKET") or None,  # Optional; uses default if unset
        "display_name": "Keyword Researcher",
    }
    print("Agent config:", agent_config)
    # If set, update existing Agent Engine; otherwise create a new one.
    resource_name = (os.getenv("REASONING_ENGINE_RESOURCE_NAME") or "").strip() or None
    print("Resource name:", resource_name)
    if resource_name:
        remote_app = client.agent_engines.update(
            name=resource_name,
            agent=app,
            config=agent_config,
        )
        print("Updated Agent Engine:", remote_app.api_resource.name)
    else:
        remote_app = client.agent_engines.create(
            agent=app,
            config=agent_config,
        )
        print("Created Agent Engine:", remote_app.api_resource.name)


if __name__ == "__main__":
    main()
