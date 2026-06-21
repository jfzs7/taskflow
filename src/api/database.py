"""
Moduł połączenia z bazą danych aplikacji TaskFlow.

Skonfigurowano asynchroniczny silnik SQLAlchemy oraz fabrykę sesji.
Zaimplementowano wzorzec Dependency Injection do wstrzykiwania
sesji bazodanowej w endpointach FastAPI.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

# Inicjalizacja konfiguracji
settings = get_settings()

# --- Silnik asynchroniczny bazy danych ---
# echo=True loguje zapytania SQL w trybie debug.
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_size=5,
    max_overflow=10,
)

# --- Fabryka sesji asynchronicznych ---
# expire_on_commit=False zapobiega przedwczesnemu wygasaniu atrybutów modelu.
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Bazowa klasa modeli SQLAlchemy.
    """
    pass


async def get_db() -> AsyncSession:
    """
    Generator sesji bazy danych (do Dependency Injection w FastAPI).

    Automatycznie zamyka sesję po zakończeniu żądania HTTP.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Inicjalizacja schematu bazy danych.

    Tworzy tabele w bazie, jeśli jeszcze nie istnieją.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Zamknięcie połączenia z bazą danych (zwolnienie puli).
    """
    await engine.dispose()
