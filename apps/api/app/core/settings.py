from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_file() -> Path | None:
    """Repo-root `.env` when developing locally. Docker injects the same values as environment variables."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.is_file() or (parent / ".env.example").is_file():
            return candidate if candidate.is_file() else None
    return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://ops:ops@localhost:5434/ops_copilot"
    database_url_sync: str = "postgresql+psycopg://ops:ops@localhost:5434/ops_copilot"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    openai_api_key: str = ""
    openai_api_base: str | None = None
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "ops-copilot"
    api_cors_origins: str = "http://localhost:3000"
    environment: str = "development"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


settings = Settings()
