"""
Endpointy monitoringu: /health, /metrics, /prometheus.

/health jest uzywany przez Kubernetes liveness/readiness probes.
/prometheus generuje metryki w formacie tekstowym pobieranym przez Prometheus co 15s.
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

APP_START_TIME = time.time()  # zapamietujemy czas startu do obliczania uptime

# Gauge = aktualna wartosc (moze rosnac i malec), w odroznienieu od Counter (tylko rosnie).
# Etykiety (labels) pozwalaja filtrowac metryki np. po statusie zadania.
TASKS_TOTAL = Gauge("taskflow_tasks_total", "Calkowita liczba zadan w systemie")
TASKS_BY_STATUS = Gauge("taskflow_tasks_by_status", "Liczba zadan wg statusu", ["status"])
TASKS_BY_PRIORITY = Gauge("taskflow_tasks_by_priority", "Liczba zadan wg priorytetu", ["priority"])
DATABASE_STATUS = Gauge("taskflow_database_status", "Status polaczenia z baza (1=OK, 0=brak)")
REDIS_STATUS = Gauge("taskflow_redis_status", "Status polaczenia z Redis (1=OK, 0=brak)")


@router.get("/health", response_model=HealthResponse, summary="Health check aplikacji")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Sprawdza czy aplikacja i jej zaleznosci (DB, Redis) odpowiadaja.
    Uzywany przez Kubernetes do decydowania o restartach podow.
    """
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    redis_healthy = await check_redis_health()
    redis_status = "healthy" if redis_healthy else "unavailable"

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
    """Statystyki zadan i uptime w formacie JSON — wygodna alternatywa dla /prometheus."""
    service = TaskService(db)
    stats = await service.get_task_stats()

    return MetricsResponse(
        total_tasks=stats["total_tasks"],
        tasks_by_status=stats["tasks_by_status"],
        tasks_by_priority=stats["tasks_by_priority"],
        uptime_seconds=round(time.time() - APP_START_TIME, 2),
    )


@router.get("/prometheus", response_class=Response, summary="Metryki w formacie Prometheus")
async def prometheus_metrics(db: AsyncSession = Depends(get_db)):
    """
    Endpoint scrapowany przez Prometheus co 15s (model pull).
    Aktualizuje Gauge'y przed wygenerowaniem odpowiedzi.
    """
    service = TaskService(db)
    stats = await service.get_task_stats()

    TASKS_TOTAL.set(stats["total_tasks"])
    for status_key, val in stats["tasks_by_status"].items():
        TASKS_BY_STATUS.labels(status=status_key).set(val)
    for priority_key, val in stats["tasks_by_priority"].items():
        TASKS_BY_PRIORITY.labels(priority=priority_key).set(val)

    # Sprawdzamy baze i Redis przy kazdym scrapie — aktualne dane w Grafanie.
    db_val = 1
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_val = 0
    DATABASE_STATUS.set(db_val)

    redis_healthy = await check_redis_health()
    REDIS_STATUS.set(1 if redis_healthy else 0)

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
