"""
Konfiguracja aplikacji TaskFlow.

Wszystkie parametry srodowiskowe w jednym miejscu — zamiast szukac ich po calym kodzie.
Uzywamy pydantic-settings, ktory sam pobiera wartosci z .env lub zmiennych systemowych.
Funkcja get_settings() jest singletonem dzieki @lru_cache — parsujemy .env tylko raz.
"""

# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Ustawienia aplikacji czytane ze zmiennych srodowiskowych lub pliku .env.
    Pydantic automatycznie waliduje typy i wartosci przy starcie.
    """

    # Ogolne
    app_name: str = "TaskFlow"
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "taskflow"
    postgres_user: str = "taskflow_user"
    postgres_password: str = "taskflow_secret_password"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    @property
    def database_url(self) -> str:
        """Asynchroniczny URL do PostgreSQL (asyncpg)."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Synchroniczny URL do PostgreSQL — przydatny np. przy migracjach Alembic."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """URL do Redis, z haslem lub bez zaleznie od konfiguracji."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # ignorujemy zmienne srodowiskowe ktore nie sa nam potrzebne (np. z Docker Compose)
    )


@lru_cache()
def get_settings() -> Settings:
    """Zwraca singleton z konfiguracja — wczytywany tylko raz, potem z cache."""
    return Settings()
