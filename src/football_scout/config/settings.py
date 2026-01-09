"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys
    groq_api_key: Optional[str] = None

    # LLM Configuration
    llm_model: str = "mixtral-8x7b-32768"
    llm_temperature: float = 0.5
    llm_max_tokens: int = 1024

    # Scraper Configuration
    user_agent: str = "FootballScoutAI/1.0"
    request_timeout: int = 30
    transfermarkt_base_url: str = "https://www.transfermarkt.com"

    # Application
    data_dir: str = "./data"

    def validate_api_key(self) -> bool:
        """Check if the API key is set."""
        return self.groq_api_key is not None and len(self.groq_api_key) > 0


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
