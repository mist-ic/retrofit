"""Application configuration — loads all settings from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── LLM ──────────────────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_flash_model: str = "gemini-3-flash-preview"
    gemini_pro_model: str = "gemini-3.1-pro-preview"

    # ── Firecrawl ─────────────────────────────────────────────────────────────
    firecrawl_api_key: str = ""

    # ── Storage ───────────────────────────────────────────────────────────────
    google_cloud_project: str = ""
    gcs_bucket: str = ""
    use_local_storage: bool = True  # True = /tmp; False = GCS

    # ── CORS ──────────────────────────────────────────────────────────────────
    frontend_url: str = "http://localhost:3000"

    # ── Observability (LangSmith) ─────────────────────────────────────────────
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "retrofit-cro-agent"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
