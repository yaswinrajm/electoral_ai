"""
config.py — Application Configuration
======================================
Manages environment-based configuration for the Electoral AI backend using
Pydantic's BaseSettings. All values are read from the `.env` file at startup
and are accessible throughout the application via the `settings` singleton.

Configuration Fields:
    app_name (str):         Display name for the FastAPI application.
    port (int):             Port number for the Uvicorn server. Default: 8080.
    host (str):             Host binding for the server. Default: 0.0.0.0 (all interfaces).
    mock_mode (bool):       When True, skips all Google API calls and returns mock data.
                            Useful for local development without credentials.
    gemini_api_key (str):   Legacy API key field (not used in Vertex AI mode).
    google_application_credentials (str):
                            Path to the GCP Service Account JSON key file.
                            Required for Vertex AI, Translation API, and TTS API.

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or the .env file.
    Pydantic automatically validates types and raises errors for missing required fields.
    """

    # Application Identity
    app_name: str = "Electoral AI Backend"

    # Server Configuration
    port: int = 8080
    host: str = "0.0.0.0"

    # Development Mode — disables real API calls when True
    mock_mode: bool = False

    # Legacy field kept for backward compatibility; not active in Vertex AI mode
    gemini_api_key: str = ""

    # Path to the Google Cloud Service Account key file (required for production)
    google_application_credentials: Optional[str] = None

    # Pydantic V2 settings: load from .env file and silently ignore extra variables
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Singleton instance — import this throughout the application
settings = Settings()
