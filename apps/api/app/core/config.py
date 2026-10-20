from functools import lru_cache
from pathlib import Path
from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILES = tuple(parent / ".env" for parent in Path(__file__).resolve().parents)


class Settings(BaseSettings):
    app_name: str = "property-intelligence"
    app_env: str = "local"
    database_url: str
    secret_key: SecretStr = Field(validation_alias=AliasChoices("SECRET_KEY", "APP_SECRET"))
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
