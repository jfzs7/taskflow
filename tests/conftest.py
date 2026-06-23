"""
Konfiguracja testow (fixtures) dla pytest.

Zamiast PostgreSQL uzywamy SQLite in-memory — szybsze, izolowane, bez zewnetrznego serwera.
Mechanizm: app.dependency_overrides[get_db] podmienia zaleznosc FastAPI — endpointy
dostaja sesje SQLite zamiast PostgreSQL, nie wiedzac o tym.

Redis jest wylaczony w testach — cache_service zwroci None przy braku polaczenia
i aplikacja dziala w trybie bez cache (graceful degradation).
"""

import asyncio
import sys
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Dodajemy src/api do sys.path zeby importy dzialaly bez instalowania pakietu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "api"))

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402

# SQLite in-memory — oddzielny plik per sesja testow (nie :memory:, bo wspoldzelony engine)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_taskflow.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Jedna petla zdarzen asyncio dla calej sesji testow."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """
    Tworzy tabele przed kazdym testem i usuwa je po tесcie.
    Dzieki temu kazdy test startuje z czystym stanem — kolejnosc nie ma znaczenia.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Sesja bazodanowa dla jednego testu."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Klient HTTP do testowania endpointow API.
    Nadpisuje get_db tak, zeby API uzywalo SQLite zamiast PostgreSQL.
    ASGITransport — nie uruchamia prawdziwego serwera, dziala in-process.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()  # czyscimy nadpisania po tescie
