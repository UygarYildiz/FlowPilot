from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama ayarları; `FLOWPILOT_` önekli ortam değişkenlerinden okunur."""

    model_config = SettingsConfigDict(env_prefix="FLOWPILOT_", env_file=".env", extra="ignore")

    env: str = "development"
    llm_provider: str = "fake"
    llm_model: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
