"""
config.py — Application Configuration (Environment-Driven)
============================================================
Centralizes all runtime configuration for the Electoral AI backend.
Settings are loaded exclusively from environment variables (and a .env file
for local development) — no secrets or infrastructure values are hardcoded.

All configuration is accessed via the module-level ``settings`` singleton:

    from config import settings
    print(settings.gcp_project_id)

Environment Variables:
    GCP_PROJECT_ID (str):
        Google Cloud project ID. Required in production.
        Example: "daring-span-495114-b2"

    GCP_REGION (str):
        Google Cloud region for Vertex AI endpoint.
        Default: "us-central1"

    GOOGLE_APPLICATION_CREDENTIALS (str):
        Absolute path to the GCP service account JSON key file.
        Required locally; Cloud Run uses its default service account.
        Example: "/app/gcp-key.json"
        ⚠️  NEVER commit this file to version control.

    MOCK_MODE (bool):
        When True, all Google Cloud API calls are skipped and stub responses
        are returned. Used automatically during testing (set in tests/conftest.py).
        Default: False

    APP_TITLE (str):
        Human-readable application title for the FastAPI docs.
        Default: "Electoral AI Backend"

    APP_VERSION (str):
        Semantic version string for the FastAPI docs.
        Default: "1.0.0"

Local Development:
    Create a ``.env`` file in the project root with the required variables.
    The file is already listed in ``.gitignore`` — never commit it.

    Example .env file::

        GCP_PROJECT_ID=daring-span-495114-b2
        GCP_REGION=us-central1
        GOOGLE_APPLICATION_CREDENTIALS=./gcp-key.json
        MOCK_MODE=false

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Pydantic Settings model that loads configuration from environment variables.

    Pydantic automatically reads values from:
      1. Environment variables (e.g., exported in the shell or set by Cloud Run)
      2. A ``.env`` file in the working directory (for local development only)

    All fields have sensible defaults to minimize configuration for new developers.

    Attributes:
        gcp_project_id (str): Google Cloud project ID for Vertex AI and billing.
        gcp_region (str): GCP region for Vertex AI API endpoint.
        google_application_credentials (str): Path to service account JSON key file.
        mock_mode (bool): Disables all Google API calls when True. Used in tests.
        app_title (str): Application display name shown in FastAPI auto-docs.
        app_version (str): Semantic version string shown in FastAPI auto-docs.
    """

    # ── Google Cloud Platform ──────────────────────────────────────────────
    gcp_project_id: str = "daring-span-495114-b2"
    gcp_region: str = "us-central1"
    google_application_credentials: str = ""

    # ── Development / Testing ─────────────────────────────────────────────
    mock_mode: bool = False

    # ── Application Metadata ──────────────────────────────────────────────
    app_title: str = "Electoral AI Backend"
    app_version: str = "1.0.0"

    class Config:
        """Pydantic configuration for Settings.

        Attributes:
            env_file (str): Path to the .env file for local development.
            env_file_encoding (str): Encoding used to read the .env file.
            case_sensitive (bool): Field names match env vars case-insensitively
                                   when False (e.g., GCP_PROJECT_ID → gcp_project_id).
        """

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# ─── Module-Level Singleton ───────────────────────────────────────────────────
# All other modules import this single instance.
# Never instantiate Settings() directly elsewhere — always use `from config import settings`.
settings = Settings()
