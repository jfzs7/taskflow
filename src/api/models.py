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
    Priorytety zadań.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(str, enum.Enum):
    """
    Statusy cyklu życia zadań.
    """
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class Task(Base):
    """
    Model reprezentujący tabelę zadań (tasks).

    Zastosowano soft-delete (pole is_deleted) zamiast
    fizycznego usuwania rekordów z bazy.
    """
    __tablename__ = "tasks"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Identyfikator zadania"
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
        comment="Szczegółowy opis"
    )
    priority = Column(
        Enum(Priority),
        default=Priority.MEDIUM,
        nullable=False,
        comment="Priorytet (low, medium, high, critical)"
    )
    status = Column(
        Enum(Status),
        default=Status.TODO,
        nullable=False,
        index=True,
        comment="Status (todo, in_progress, done, archived)"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Data utworzenia"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Data aktualizacji"
    )
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Flaga soft-delete"
    )

    def __repr__(self) -> str:
        """Reprezentacja tekstowa modelu (do debugowania)."""
        return f"<Task(id={self.id}, title='{self.title}', status={self.status.value})>"
