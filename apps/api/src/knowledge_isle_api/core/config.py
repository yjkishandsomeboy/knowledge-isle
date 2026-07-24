from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Knowledge Isle"
    app_env: str = "development"
    admin_setup_token: str = "change-me-before-setup"
    database_url: str = "postgresql+asyncpg://knowledge_isle:knowledge_isle_dev@localhost:5432/knowledge_isle"
    session_cookie_name: str = "knowledge_isle_session"
    session_ttl_days: int = 14
    cors_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "knowledge_isle"
    minio_secret_key: str = "knowledge_isle_dev_password"
    minio_bucket: str = "knowledge-isle-private"
    minio_secure: bool = False
    redis_url: str = "redis://localhost:6379/0"
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = "gpt-5.6-sol"
    ai_timeout_seconds: float = 90.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
