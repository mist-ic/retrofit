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
    # Auto-detected: False when GCS_BUCKET is set, True otherwise
    use_local_storage: bool = True

    # ── CORS ──────────────────────────────────────────────────────────────────
    frontend_url: str = "http://localhost:3000"

    # ── Observability (LangSmith) ─────────────────────────────────────────────
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "retrofit-cro-agent"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def model_post_init(self, __context) -> None:
        # If a GCS bucket is configured, automatically switch to cloud storage
        if self.gcs_bucket:
            object.__setattr__(self, "use_local_storage", False)


settings = Settings()
