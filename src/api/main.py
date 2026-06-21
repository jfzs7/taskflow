"""
Moduł główny aplikacji TaskFlow.

Zaimplementowano punkt wejścia aplikacji FastAPI.
Skonfigurowano middleware CORS, zarejestrowano routery
oraz zdefiniowano zdarzenia cyklu życia aplikacji
(inicjalizacja i zamykanie połączeń z bazą danych i Redis).

Uruchomienie aplikacji:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import close_db, init_db
from routes.health import router as health_router
from routes.tasks import router as tasks_router
from services.cache_service import close_redis

# Pobrano konfigurację aplikacji
settings = get_settings()

# Skonfigurowano logowanie
logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządzano cyklem życia aplikacji (Lifespan Events).

    Zastąpiono przestarzałe zdarzenia on_startup/on_shutdown
    nowym wzorcem asynccontextmanager (FastAPI >= 0.95).

    Startup: Zainicjalizowano bazę danych (utworzono tabele).
    Shutdown: Zamknięto połączenia z bazą danych i Redis.
    """
    logger.info("🚀 Uruchamianie aplikacji %s v%s (%s)",
                settings.app_name, settings.app_version, settings.app_env)

    # --- Startup ---
    await init_db()
    logger.info("✅ Baza danych zainicjalizowana")

    yield  # Aplikacja działa

    # --- Shutdown ---
    logger.info("🔻 Zamykanie aplikacji...")
    await close_redis()
    await close_db()
    logger.info("✅ Połączenia zamknięte. Aplikacja zatrzymana.")


# --- Utworzono instancję aplikacji FastAPI ---
app = FastAPI(
    title=settings.app_name,
    description=(
        "**TaskFlow** — mikroserwisowy system zarządzania zadaniami.\n\n"
        "Aplikacja opracowana w ramach pracy magisterskiej demonstrująca "
        "podejście DevOps: konteneryzację (Docker), orkiestrację (Kubernetes), "
        "CI/CD (GitHub Actions) oraz wdrożenia chmurowe (AWS, Azure, GCP).\n\n"
        "Autor: Jakub Francuz"
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",         # Swagger UI
    redoc_url="/redoc",       # ReDoc
    openapi_url="/openapi.json",
)

# --- Skonfigurowano middleware CORS ---
# Umożliwiono żądania cross-origin z dowolnych źródeł (tryb deweloperski).
# W produkcji należy ograniczyć allow_origins do konkretnych domen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Zarejestrowano routery ---
app.include_router(health_router)
app.include_router(tasks_router)


@app.get("/", tags=["Root"], summary="Strona główna API")
async def root():
    """
    Zwrócono podstawowe informacje o API.

    Endpoint ten służy jako punkt wejścia — informuje użytkownika
    o dostępnych zasobach (dokumentacja, health check).
    """
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1/tasks",
    }
