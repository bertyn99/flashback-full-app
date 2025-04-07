from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys
    MISTRAL_API_KEY: str
    MISTRAL_AGENT_IMAGE_PROMPT: str
    ELEVEN_API_KEY: str
    ELEVEN_VOICE_ID: str
    GLADIA_API_KEY: str
    SEELAB_API_KEY: str
    GEMINI_API_KEY: str

    # Cloudflare R2 settings
    R2_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_CL_KEY: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str
    R2_ENDPOINT_URL: str  # Format: https://<account_id>.r2.cloudflarestorage.com
    R2_PUBLIC_URL: str  # Format: https://pub-<account_id>.r2.dev
    # Base URLs and endpoints
    GLADIA_BASE_URL: str = "https://api.gladia.io/v2/"

    # Model settings
    MISTRAL_MODEL: str = "mistral-large-latest"
    ELEVEN_VOICE_ID: str = "Josh"
    ELEVEN_MODEL: str = "eleven_monolingual_v1"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


# Create global settings instance
settings = Settings()
