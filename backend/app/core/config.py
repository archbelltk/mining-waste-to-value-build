"""App settings, loaded from environment variables (see .env.example).

Like what you know: this is the same role a validated `process.env` wrapper
built on Zod would play in a Node app — one typed object every other module
imports from, instead of scattered `os.environ[...]` calls.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"

    database_url: str
    redis_url: str

    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
