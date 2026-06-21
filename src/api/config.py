"""
Moduł konfiguracyjny aplikacji TaskFlow.

Zaimplementowano klasę Settings, która wczytuje zmienne środowiskowe
i udostępnia je w ujednoliconej formie w całej aplikacji.
Wykorzystano bibliotekę pydantic-settings do walidacji
i automatycznego parsowania zmiennych środowiskowych.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Ustawienia konfiguracji całej aplikacji.

    Klasa definiuje wszystkie parametry konfiguracyjne aplikacji,
    które można nadpisać zmiennymi środowiskowymi.
    """

    # --- Ogólne ---
    app_name: str = "TaskFlow"
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "taskflow"
    postgres_user: str = "taskflow_user"
    postgres_password: str = "taskflow_secret_password"

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    @property
    def database_url(self) -> str:
        """
        URL połączenia asynchronicznego z PostgreSQL (asyncpg).
        """
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """
        Synchroniczny URL połączenia z PostgreSQL (np. do migracji Alembic).
        """
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """URL połączenia z Redis."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        """Konfiguracja źródła zmiennych (.env)"""
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Zwraca singleton z konfiguracją aplikacji (zapisany w cache).
    """
    return Settings()
