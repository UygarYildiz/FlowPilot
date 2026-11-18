from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama ayarları; `FLOWPILOT_` önekli ortam değişkenlerinden okunur."""

    model_config = SettingsConfigDict(env_prefix="FLOWPILOT_", env_file=".env", extra="ignore")

    env: str = "development"
    llm_provider: str = "fake"
    llm_model: str = ""
    database_url: str = "postgresql+psycopg://flowpilot:flowpilot@localhost:5433/flowpilot"
    storage_dir: str = "var/attachments"
    seed_dir: str = "seed/atlas"
    imap_host: str = ""
    imap_port: int = 993
    imap_user: str = ""
    imap_password: str = ""
    imap_folder: str = "INBOX"


@lru_cache
def get_settings() -> Settings:
    return Settings()
