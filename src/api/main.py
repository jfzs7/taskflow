"""
Moduł główny aplikacji TaskFlow.

Zaimplementowano punkt wejścia aplikacji FastAPI.
Skonfigurowano middleware CORS, zarejestrowano routery
oraz zdefiniowano zdarzenia cyklu życia aplikacji
(inicjalizacja i zamykanie połączeń z bazą danych i Redis).

Uruchomienie aplikacji:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import time
import logging
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from config import get_settings
from database import close_db, init_db
from routes.health import router as health_router
from routes.tasks import router as tasks_router
from services.cache_service import close_redis

# Inicjalizacja konfiguracji
settings = get_settings()

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Zarządzanie cyklem życia aplikacji (Lifespan Events).

    Obsługa startu i zatrzymania aplikacji.
    Startup: Inicjalizacja bazy (tworzenie tabel).
    Shutdown: Zamknięcie połączeń do bazy i Redis.
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


# --- Instancja aplikacji FastAPI ---
app = FastAPI(
    title=settings.app_name,
    description=(
        "**TaskFlow** — system zarządzania zadaniami.\n\n"
        "Projekt demonstrujący podejście DevOps: konteneryzację (Docker), "
        "orkiestrację (Kubernetes), CI/CD (GitHub Actions) oraz chmurę (AWS, Azure, GCP).\n\n"
        "Autor: Jakub Francuz"
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",         # Swagger UI
    redoc_url="/redoc",       # ReDoc
    openapi_url="/openapi.json",
)

# --- Konfiguracja middleware CORS ---
# Zezwolenie na żądania cross-origin w trybie deweloperskim.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Definicja metryk Prometheus dla ruchu API ---
REQUEST_COUNT = Counter(
    "taskflow_requests_total",
    "Calkowita liczba zapytan HTTP",
    ["method", "endpoint", "http_status"]
)
REQUEST_LATENCY = Histogram(
    "taskflow_request_latency_seconds",
    "Czas wykonania zapytania HTTP w sekundach",
    ["method", "endpoint"]
)

# --- Middleware do automatycznego pomiaru ruchu HTTP ---
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    endpoint = request.url.path
    
    # Pominięcie plików statycznych w zbieraniu metryk
    if endpoint.startswith("/static") or endpoint.startswith("/favicon"):
        return await call_next(request)
        
    response = await call_next(request)
    
    # Pomiar czasu i zapisanie metryk
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        http_status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)
    
    return response

# --- Konfiguracja plików statycznych i szablonów ---
# Obsługa plików statycznych (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Obsługa silnika szablonów Jinja2
templates = Jinja2Templates(directory="templates")

# --- Rejestracja routerów ---
app.include_router(health_router)
app.include_router(tasks_router)


@app.get("/", response_class=HTMLResponse, tags=["Root"], summary="Strona główna (Panel Użytkownika)")
async def root(request: Request):
    """
    Renderowanie panelu użytkownika aplikacji TaskFlow.

    Zwraca stronę HTML z panelem do zarządzania zadaniami.
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "app_name": settings.app_name, "version": settings.app_version}
    )

