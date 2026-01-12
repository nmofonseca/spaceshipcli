from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    api_key: str = Field(..., alias="SPACESHIP_API_KEY")
    api_secret: str = Field(..., alias="SPACESHIP_API_SECRET")
    base_url: str = "https://spaceship.dev/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore",
        env_file_ignore_missing=True
    )

settings = Settings()
