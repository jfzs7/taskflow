"""
Moduł modeli bazy danych aplikacji TaskFlow.

Zdefiniowano model Task (zadanie) reprezentujący tabelę 'tasks'
w bazie danych PostgreSQL. Wykorzystano typy wyliczeniowe (Enum)
do ograniczenia dozwolonych wartości pól 'priority' i 'status'.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
)

from database import Base


class Priority(str, enum.Enum):
    """
    Typ wyliczeniowy priorytetu zadania.

    Zdefiniowano cztery poziomy priorytetu, od najniższego do krytycznego.
    Dziedziczenie po str umożliwia automatyczną serializację do JSON.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(str, enum.Enum):
    """
    Typ wyliczeniowy statusu zadania.

    Zdefiniowano cztery stany cyklu życia zadania:
    - TODO: zadanie oczekujące na realizację
    - IN_PROGRESS: zadanie w trakcie realizacji
    - DONE: zadanie zakończone
    - ARCHIVED: zadanie zarchiwizowane (soft-delete)
    """
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class Task(Base):
    """
    Model zadania (Task) — główna encja aplikacji TaskFlow.

    Zmapowano obiekt Python na tabelę 'tasks' w bazie PostgreSQL.
    Zastosowano wzorzec soft-delete (pole is_deleted) zamiast
    fizycznego usuwania rekordów, co umożliwia odzyskiwanie danych.

    Atrybuty:
        id (int): Unikalny identyfikator zadania (klucz główny, auto-increment).
        title (str): Tytuł zadania (wymagany, max 255 znaków).
        description (str): Szczegółowy opis zadania (opcjonalny).
        priority (Priority): Priorytet zadania (domyślnie: MEDIUM).
        status (Status): Status zadania (domyślnie: TODO).
        created_at (datetime): Data i czas utworzenia (ustawiane automatycznie).
        updated_at (datetime): Data i czas ostatniej modyfikacji (aktualizowane automatycznie).
        is_deleted (bool): Flaga soft-delete (domyślnie: False).
    """
    __tablename__ = "tasks"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Unikalny identyfikator zadania"
    )
    title = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Tytuł zadania"
    )
    description = Column(
        Text,
        nullable=True,
        default="",
        comment="Szczegółowy opis zadania"
    )
    priority = Column(
        Enum(Priority),
        default=Priority.MEDIUM,
        nullable=False,
        comment="Priorytet zadania (low, medium, high, critical)"
    )
    status = Column(
        Enum(Status),
        default=Status.TODO,
        nullable=False,
        index=True,
        comment="Status zadania (todo, in_progress, done, archived)"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Data i czas utworzenia zadania"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Data i czas ostatniej modyfikacji"
    )
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Flaga soft-delete — oznacza zadanie jako usunięte bez fizycznego usuwania"
    )

    def __repr__(self) -> str:
        """Zwrócono czytelną reprezentację obiektu Task (do celów debugowania)."""
        return f"<Task(id={self.id}, title='{self.title}', status={self.status.value})>"
