from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    MISTRAL_API_KEY: str
    MISTRAL_AGENT_IMAGE_PROMPT: str
    ELEVEN_API_KEY: str
    ELEVEN_VOICE_ID: str
    GLADIA_API_KEY: str
    SEELAB_API_KEY: str

    # Base URLs and endpoints
    GLADIA_BASE_URL: str = "https://api.gladia.io/v2/"


    # Model settings
    MISTRAL_MODEL: str = "mistral-large-latest"
    ELEVEN_VOICE_ID: str = "Josh"
    ELEVEN_MODEL: str = "eleven_monolingual_v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True
    )

# Create global settings instance
settings = Settings()
