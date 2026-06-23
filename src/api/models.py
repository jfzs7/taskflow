"""
Model zadania (Task) w bazie danych.

Tabela 'tasks' w PostgreSQL. Zamiast fizycznego DELETE uzywamy soft-delete
(flaga is_deleted), dzieki czemu dane sa zachowane do ewentualnego audytu.
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
    """Priorytety zadan — baza odrzuci kazda wartosc spoza tej listy."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(str, enum.Enum):
    """Statusy cyklu zycia zadania."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class Task(Base):
    """
    Rekord zadania w tabeli 'tasks'.

    Indeksy na title i status przyspieszaja najczestsze zapytania (filtrowanie, wyszukiwanie).
    is_deleted = True oznacza zadanie usuniete przez uzytkownika — soft-delete.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True,
                comment="Identyfikator zadania")
    title = Column(String(255), nullable=False, index=True,
                   comment="Tytul zadania")
    description = Column(Text, nullable=True, default="",
                         comment="Szczegolowy opis")
    priority = Column(Enum(Priority), default=Priority.MEDIUM, nullable=False,
                      comment="Priorytet (low, medium, high, critical)")
    status = Column(Enum(Status), default=Status.TODO, nullable=False, index=True,
                    comment="Status (todo, in_progress, done, archived)")

    # Znaczniki czasu ustawiane automatycznie przez ORM — nie trzeba ich recznie wypelniac.
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc), nullable=False,
                        comment="Data utworzenia")
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
                        comment="Data aktualizacji")

    is_deleted = Column(Boolean, default=False, nullable=False,
                        comment="Flaga soft-delete — rekord pozostaje w bazie")

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status={self.status.value})>"
