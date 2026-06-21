"""
Moduł połączenia z bazą danych aplikacji TaskFlow.

Skonfigurowano asynchroniczny silnik SQLAlchemy oraz fabrykę sesji.
Zaimplementowano wzorzec Dependency Injection do wstrzykiwania
sesji bazodanowej w endpointach FastAPI.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

# Pobrano konfigurację aplikacji
settings = get_settings()

# --- Utworzono asynchroniczny silnik bazy danych ---
# Parametr echo=True włącza logowanie zapytań SQL (przydatne w trybie deweloperskim).
# pool_size i max_overflow kontrolują pulę połączeń z bazą danych.
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_size=5,
    max_overflow=10,
)

# --- Skonfigurowano fabrykę sesji asynchronicznych ---
# expire_on_commit=False zapobiega wygasaniu obiektów po zatwierdzeniu transakcji,
# co jest wymagane w kontekście asynchronicznym.
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Zdefiniowano bazową klasę deklaratywną SQLAlchemy.

    Wszystkie modele bazy danych dziedziczą po tej klasie,
    co umożliwia automatyczne tworzenie tabel na podstawie
    definicji modeli (wzorzec Active Record).
    """
    pass


async def get_db() -> AsyncSession:
    """
    Zaimplementowano generator sesji bazodanowej (Dependency Injection).

    Wykorzystywany jako zależność w endpointach FastAPI:
        @router.get("/tasks")
        async def get_tasks(db: AsyncSession = Depends(get_db)):
            ...

    Sesja jest automatycznie zamykana po zakończeniu obsługi żądania HTTP,
    co zapobiega wyciekom połączeń z bazą danych.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Zainicjalizowano schemat bazy danych.

    Utworzono wszystkie tabele zdefiniowane w modelach SQLAlchemy.
    Wywołanie tej funkcji następuje podczas uruchamiania aplikacji
    (zdarzenie 'lifespan' w FastAPI).

    Uwaga: W środowisku produkcyjnym zalecane jest stosowanie
    migracji Alembic zamiast automatycznego tworzenia tabel.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Zamknięto połączenie z bazą danych.

    Wywołanie tej funkcji następuje podczas zamykania aplikacji
    w celu prawidłowego zwolnienia zasobów (puli połączeń).
    """
    await engine.dispose()
