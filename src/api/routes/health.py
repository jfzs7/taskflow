"""
Moduł endpointów health check i metryk aplikacji TaskFlow.

Zaimplementowano endpointy monitoringu:
- GET /health  — sprawdzenie stanu zdrowia aplikacji i zależności
- GET /metrics — pobranie metryk operacyjnych aplikacji

Endpointy te są kluczowe dla orkiestratorów (Kubernetes)
do określania gotowości (readiness) i żywotności (liveness) podów.
"""

import time
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from schemas import HealthResponse, MetricsResponse
from services.cache_service import check_redis_health
from services.task_service import TaskService

router = APIRouter(tags=["Monitoring"])
settings = get_settings()

# Zapisanie czasu startu aplikacji do uptime
APP_START_TIME = time.time()


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


@router.get("/metrics", response_model=MetricsResponse, summary="Metryki aplikacji")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """
    Pobranie metryk operacyjnych aplikacji.

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
