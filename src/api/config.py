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
    Klasa konfiguracyjna aplikacji.

    Zdefiniowano wszystkie parametry konfiguracyjne aplikacji,
    które mogą zostać nadpisane przez zmienne środowiskowe.
    Zastosowano wzorzec Singleton (poprzez lru_cache) w celu
    zapewnienia jednej instancji konfiguracji w całej aplikacji.
    """

    # --- Ustawienia aplikacji ---
    app_name: str = "TaskFlow"
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # --- Baza danych PostgreSQL ---
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
        Wygenerowano URL połączenia z bazą danych PostgreSQL.
        Wykorzystano sterownik asyncpg do obsługi asynchronicznych zapytań.
        """
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """
        Wygenerowano synchroniczny URL połączenia z bazą danych.
        Wykorzystywany przez Alembic do migracji schematu bazy danych.
        """
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Wygenerowano URL połączenia z serwerem Redis."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        """
        Skonfigurowano źródło zmiennych środowiskowych.
        Plik .env jest wczytywany automatycznie, jeśli istnieje.
        """
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Zwrócono singleton instancji konfiguracji.

    Zastosowano dekorator @lru_cache w celu zapewnienia,
    że konfiguracja jest wczytywana tylko raz podczas
    cyklu życia aplikacji (wzorzec Singleton).
    """
    return Settings()
