"""
Punkt wejscia aplikacji TaskFlow.

Tutaj dzieje sie wszystko przy starcie: middleware, routery, metryki Prometheus
i zarzadzanie polaczeniami do bazy i Redis przez lifespan context.

Uruchomienie:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import time
import logging
from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from prometheus_client import Counter, Histogram

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from fastapi.templating import Jinja2Templates
# pyrefly: ignore [missing-import]
from fastapi.responses import HTMLResponse

from config import get_settings
from database import close_db, init_db
from routes.health import router as health_router
from routes.tasks import router as tasks_router
from services.cache_service import close_redis

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup i shutdown aplikacji w jednym miejscu.

    Startup: tworzy tabele w bazie jesli nie istnieja.
    Shutdown: ladnie zamyka polaczenia do DB i Redis.
    """
    logger.info("[START] Uruchamianie aplikacji %s v%s (%s)",
                settings.app_name, settings.app_version, settings.app_env)

    await init_db()
    logger.info("[OK] Baza danych zainicjalizowana")

    yield  # tu dziala aplikacja

    logger.info("[STOP] Zamykanie aplikacji...")
    await close_redis()
    await close_db()
    logger.info("[OK] Polaczenia zamkniete. Aplikacja zatrzymana.")


app = FastAPI(
    title=settings.app_name,
    description=(
        "**TaskFlow** — system zarzadzania zadaniami.\n\n"
        "Projekt demonstrujacy podejscie DevOps: konteneryzacja (Docker), "
        "orkiestracja (Kubernetes), CI/CD (GitHub Actions) oraz monitoring (Prometheus + Grafana).\n\n"
        "Autor: Jakub Francuz"
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Zezwalamy na cross-origin w trybie dev — na produkcji nalezy zawezic origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Counter liczy zapytania, Histogram mierzy czas odpowiedzi — pobierane przez Prometheus.
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


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Mierzy czas odpowiedzi i liczy zapytania dla Prometheusa. Pomija pliki statyczne."""
    start_time = time.time()
    endpoint = request.url.path

    if endpoint.startswith("/static") or endpoint.startswith("/favicon"):
        return await call_next(request)

    response = await call_next(request)

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


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(health_router)
app.include_router(tasks_router)


@app.get("/", response_class=HTMLResponse, tags=["Root"], summary="Panel uzytkownika")
async def root(request: Request):
    """Renderuje glowny panel HTML aplikacji TaskFlow."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "app_name": settings.app_name, "version": settings.app_version}
    )
