"""
Moduł endpointów health check i metryk aplikacji TaskFlow.

Zaimplementowano endpointy monitoringu:
- GET /health  — sprawdzenie stanu zdrowia aplikacji i zależności
- GET /metrics — pobranie metryk operacyjnych aplikacji

Endpointy te są kluczowe dla orkiestratorów (Kubernetes)
do określania gotowości (readiness) i żywotności (liveness) podów.
"""

import time
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Gauge

from config import get_settings
from database import get_db
from schemas import HealthResponse, MetricsResponse
from services.cache_service import check_redis_health
from services.task_service import TaskService

router = APIRouter(tags=["Monitoring"])
settings = get_settings()

# Zapisanie czasu startu aplikacji do uptime
APP_START_TIME = time.time()

# --- Definicja wskaźników Prometheus (Gauges) ---
# Gauges pozwalają na prezentację aktualnego stanu liczbowego zadań w podziale na etykiety (labels)
TASKS_TOTAL = Gauge("taskflow_tasks_total", "Calkowita liczba zadan w systemie")
TASKS_BY_STATUS = Gauge("taskflow_tasks_by_status", "Liczba zadan w podziale na statusy", ["status"])
TASKS_BY_PRIORITY = Gauge("taskflow_tasks_by_priority", "Liczba zadan w podziale na priorytety", ["priority"])
DATABASE_STATUS = Gauge("taskflow_database_status", "Status polaczenia z baza danych (1=OK, 0=brak)")
REDIS_STATUS = Gauge("taskflow_redis_status", "Status polaczenia z Redis (1=OK, 0=brak)")


@router.get("/health", response_model=HealthResponse, summary="Health check aplikacji")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Sprawdzenie stanu zdrowia aplikacji i jej zależności.

    Endpoint wykorzystywany przez:
    - Kubernetes liveness/readiness probes
    - Load balancery (Nginx, cloud LB)
    - Systemy monitoringu (Prometheus, Grafana)
    """
    # Sprawdzenie połączenia z bazą danych
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    # Sprawdzenie połączenia z Redis
    redis_healthy = await check_redis_health()
    redis_status = "healthy" if redis_healthy else "unavailable"

    # Określenie ogólnego statusu aplikacji
    overall = "healthy" if db_status == "healthy" else "unhealthy"

    return HealthResponse(
        status=overall,
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        database=db_status,
        redis=redis_status,
    )


@router.get("/metrics", response_model=MetricsResponse, summary="Metryki aplikacji (JSON)")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """
    Pobranie metryk operacyjnych aplikacji w formacie JSON.

    Zwraca statystyki zadań (liczba wg statusu i priorytetu)
    oraz czas działania aplikacji (uptime).
    """
    service = TaskService(db)
    stats = await service.get_task_stats()

    return MetricsResponse(
        total_tasks=stats["total_tasks"],
        tasks_by_status=stats["tasks_by_status"],
        tasks_by_priority=stats["tasks_by_priority"],
        uptime_seconds=round(time.time() - APP_START_TIME, 2),
    )


@router.get("/prometheus", response_class=Response, summary="Metryki aplikacji (Prometheus)")
async def prometheus_metrics(db: AsyncSession = Depends(get_db)):
    """
    Pobranie metryk operacyjnych aplikacji w formacie tekstowym Prometheus.

    Wywoływane przez serwer Prometheus podczas skrobania (scraping).
    Aktualizuje wskaźniki zadań na bieżąco przed wygenerowaniem danych.
    """
    service = TaskService(db)
    stats = await service.get_task_stats()

    # Aktualizacja wskaźników przed pobraniem najnowszego zrzutu metryk
    TASKS_TOTAL.set(stats["total_tasks"])
    for status_key, val in stats["tasks_by_status"].items():
        TASKS_BY_STATUS.labels(status=status_key).set(val)
    for priority_key, val in stats["tasks_by_priority"].items():
        TASKS_BY_PRIORITY.labels(priority=priority_key).set(val)

    # Aktualizacja statusu bazy danych
    db_val = 1
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_val = 0
    DATABASE_STATUS.set(db_val)

    # Aktualizacja statusu cache Redis
    redis_healthy = await check_redis_health()
    redis_val = 1 if redis_healthy else 0
    REDIS_STATUS.set(redis_val)

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

