"""
Moduł schematów Pydantic aplikacji TaskFlow.

Zdefiniowano schematy walidacji danych wejściowych (request)
i wyjściowych (response) dla endpointów API.
Wykorzystano Pydantic v2 do automatycznej walidacji typów,
serializacji JSON oraz generowania dokumentacji OpenAPI/Swagger.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from models import Priority, Status


# ============================================
# Schematy żądań (Request Schemas)
# ============================================

class TaskCreate(BaseModel):
    """
    Schemat tworzenia nowego zadania.

    Zdefiniowano pola wymagane i opcjonalne do utworzenia zadania.
    Walidacja odbywa się automatycznie przez Pydantic.

    Przykład użycia (JSON body):
        {
            "title": "Wdrożyć CI/CD",
            "description": "Skonfigurować GitHub Actions",
            "priority": "high"
        }
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Tytuł zadania (wymagany, 1-255 znaków)",
        examples=["Wdrożyć pipeline CI/CD"]
    )
    description: Optional[str] = Field(
        default="",
        max_length=5000,
        description="Szczegółowy opis zadania (opcjonalny, max 5000 znaków)",
        examples=["Skonfigurować GitHub Actions dla automatycznego testowania i wdrażania"]
    )
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Priorytet zadania (domyślnie: medium)",
        examples=["high"]
    )


class TaskUpdate(BaseModel):
    """
    Schemat aktualizacji zadania.

    Wszystkie pola są opcjonalne — aktualizowane są tylko przesłane pola
    (wzorzec Partial Update / PATCH).

    Przykład użycia (JSON body):
        {
            "status": "in_progress",
            "priority": "critical"
        }
    """
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Nowy tytuł zadania"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Nowy opis zadania"
    )
    priority: Optional[Priority] = Field(
        default=None,
        description="Nowy priorytet zadania"
    )
    status: Optional[Status] = Field(
        default=None,
        description="Nowy status zadania"
    )


# ============================================
# Schematy odpowiedzi (Response Schemas)
# ============================================

class TaskResponse(BaseModel):
    """
    Schemat odpowiedzi dla pojedynczego zadania.

    Zdefiniowano strukturę danych zwracanych przez API
    po operacjach CRUD na zadaniach.
    Zastosowano model_config z from_attributes=True,
    co umożliwia automatyczną konwersję z obiektów SQLAlchemy.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Unikalny identyfikator zadania")
    title: str = Field(description="Tytuł zadania")
    description: Optional[str] = Field(description="Opis zadania")
    priority: Priority = Field(description="Priorytet zadania")
    status: Status = Field(description="Status zadania")
    created_at: datetime = Field(description="Data utworzenia")
    updated_at: datetime = Field(description="Data ostatniej modyfikacji")
    is_deleted: bool = Field(description="Czy zadanie jest usunięte (soft-delete)")


class TaskListResponse(BaseModel):
    """
    Schemat odpowiedzi dla listy zadań z paginacją.

    Opakowano listę zadań w obiekt zawierający metadane paginacji,
    co jest zgodne z najlepszymi praktykami projektowania REST API.
    """
    tasks: list[TaskResponse] = Field(description="Lista zadań")
    total: int = Field(description="Całkowita liczba zadań")
    page: int = Field(description="Numer bieżącej strony")
    per_page: int = Field(description="Liczba zadań na stronę")
    pages: int = Field(description="Całkowita liczba stron")


class MessageResponse(BaseModel):
    """
    Schemat odpowiedzi z wiadomością (np. potwierdzenie usunięcia).
    """
    message: str = Field(description="Treść wiadomości")
    detail: Optional[str] = Field(default=None, description="Dodatkowe szczegóły")


# ============================================
# Schematy health check i metryk
# ============================================

class HealthResponse(BaseModel):
    """
    Schemat odpowiedzi health check.

    Zdefiniowano strukturę informacji o stanie zdrowia aplikacji
    i jej zależności (baza danych, cache).
    """
    status: str = Field(description="Ogólny status aplikacji (healthy/unhealthy)")
    app_name: str = Field(description="Nazwa aplikacji")
    version: str = Field(description="Wersja aplikacji")
    environment: str = Field(description="Środowisko (development/staging/production)")
    database: str = Field(description="Status połączenia z bazą danych")
    redis: str = Field(description="Status połączenia z Redis")


class MetricsResponse(BaseModel):
    """
    Schemat odpowiedzi z metrykami aplikacji.

    Zdefiniowano podstawowe metryki operacyjne aplikacji,
    które mogą być wykorzystane przez systemy monitoringu
    (np. Prometheus, Grafana).
    """
    total_tasks: int = Field(description="Całkowita liczba zadań")
    tasks_by_status: dict = Field(description="Liczba zadań wg statusu")
    tasks_by_priority: dict = Field(description="Liczba zadań wg priorytetu")
    uptime_seconds: float = Field(description="Czas działania aplikacji w sekundach")
