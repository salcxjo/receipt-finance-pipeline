"""Centralized, typed configuration loaded from environment variables / .env.

Every service (API, ingestion, edge, GUI) imports `settings` from here instead
of reading os.environ directly, so config stays in one auditable place.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:devpass@localhost:5432/receipts"
    # Separate read-only role for the LLM query layer (see ADR 0002/0003).
    database_url_readonly: str | None = None

    anthropic_api_key: str | None = None
    llm_model: str = "claude-sonnet-4-6"

    # Shared secret the phone sends in the X-API-Key header. No default on
    # purpose: uploads stay disabled until UPLOAD_API_KEY is set.
    upload_api_key: str | None = None
    max_upload_mb: int = 15

    receipt_image_dir: str = "data/raw"
    log_level: str = "INFO"


settings = Settings()
