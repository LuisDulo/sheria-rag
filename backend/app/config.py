from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/sheria"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5-5"
    embedding_model: str = "BAAI/bge-small-en-v1.5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
