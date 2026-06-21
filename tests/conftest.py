"""
Moduł konfiguracyjny testów (conftest.py) aplikacji TaskFlow.

Zdefiniowano fixtures pytest do testowania endpointów API
z użyciem bazy danych SQLite w pamięci (zamiast PostgreSQL).
Zastosowano wzorzec izolacji testów — każdy test operuje
na czystej bazie danych.
"""

import asyncio
import sys
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Dodano ścieżkę src/api do sys.path (aby importy działały w testach)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "api"))

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402

# --- Konfiguracja testowej bazy danych (SQLite in-memory) ---
# Użyto SQLite zamiast PostgreSQL w testach w celu uproszczenia
# i przyspieszenia wykonywania testów (brak potrzeby zewnętrznej bazy).
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_taskflow.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Utworzono pętlę zdarzeń asyncio dla całej sesji testów."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """
    Przygotowano czystą bazę danych przed każdym testem.

    Utworzono wszystkie tabele przed testem i usunięto je po teście,
    co zapewnia pełną izolację między testami.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Utworzono sesję bazodanową dla pojedynczego testu."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Utworzono klienta HTTP do testowania endpointów API.

    Nadpisano zależność get_db, aby testy korzystały
    z testowej bazy danych (SQLite) zamiast produkcyjnej (PostgreSQL).
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
