"""
Polaczenie z baza danych PostgreSQL.

Uzywamy asynchronicznego SQLAlchemy 2.0 z driverem asyncpg — dzieki temu
zapytania do bazy nie blokuja serwera podczas oczekiwania na wynik.
Sesja bazodanowa jest wstrzykiwana przez Dependency Injection FastAPI.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

settings = get_settings()

# Pula polaczen: do 5 aktywnych + 10 dodatkowych przy skokach ruchu.
# echo=True loguje SQL w trybie debug — wygodne przy lokalnym developmencie.
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_size=5,
    max_overflow=10,
)

# expire_on_commit=False zapobiega bledom przy odczycie atrybutow po commit().
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Klasa bazowa dla modeli SQLAlchemy."""
    pass


async def get_db() -> AsyncSession:
    """
    Generator sesji do Dependency Injection w FastAPI.
    Sesja jest automatycznie zamykana po zakonczeniu kazdego zapytania HTTP.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Tworzy tabele w bazie przy starcie aplikacji (jesli jeszcze nie istnieja)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Zwalnia pule polaczen przy zamknieciu aplikacji."""
    await engine.dispose()
