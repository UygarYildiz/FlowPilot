from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama ayarları; `FLOWPILOT_` önekli ortam değişkenlerinden okunur."""

    model_config = SettingsConfigDict(env_prefix="FLOWPILOT_", env_file=".env", extra="ignore")

    env: str = "development"
    llm_provider: str = "fake"
    llm_model: str = ""
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    decision_threshold: float = 0.75
    # Sınıflandırma motoru: "llm" (generatif, llm_provider ile); "clef" / "subq" (karar modelleri).
    decision_engine: str = "llm"
    clef_model: str = "clef-flash"
    subq_model: str = "subq-snap-1.2"
    # Karar modeli soru sürümü: typed-v2 (departman başına evet/hayır), typed-v3 (asıl + ek)
    typed_prompt: str = "typed-v2"
    subq_api_key: str = Field(default="", validation_alias="SUBQ_API_KEY")
    cloudflare_account_id: str = Field(default="", validation_alias="CLOUDFLARE_ACCOUNT_ID")
    cloudflare_api_token: str = Field(default="", validation_alias="CLOUDFLARE_API_TOKEN")
    # Oturum çerezini imzalar. Canlıda mutlaka değiştirilir.
    secret_key: str = "dev-secret-change-me"
    # Demo kullanıcılarının şifresi (`flowpilot users demo`). Yalnızca kurgusal demo içindir.
    demo_password: str = "flowpilot-demo"
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
