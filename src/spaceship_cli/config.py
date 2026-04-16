"""
Configuration settings for the Spaceship CLI.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # pylint: disable=too-few-public-methods
    """
    Settings class to handle environment variables and .env files.
    """

    api_key: Optional[str] = Field(default=None, alias="SPACESHIP_API_KEY")
    api_secret: Optional[str] = Field(default=None, alias="SPACESHIP_API_SECRET")
    base_url: str = "https://spaceship.dev/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_file_ignore_missing=True,
    )


settings = Settings()
