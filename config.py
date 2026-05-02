from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "Electoral AI Backend"
    port: int = 8080
    host: str = "0.0.0.0"
    
    # New configurations
    mock_mode: bool = False
    gemini_api_key: str = ""
    
    # We add this so Pydantic knows it's an expected field from .env
    google_application_credentials: Optional[str] = None

    # Use SettingsConfigDict for Pydantic V2 and ensure extra env vars are ignored
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
