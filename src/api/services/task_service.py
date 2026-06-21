"""
Moduł serwisu zadań (Task Service) aplikacji TaskFlow.

Zaimplementowano warstwę logiki biznesowej oddzielającą
endpointy API od bezpośrednich operacji na bazie danych.
Zastosowano wzorzec Repository/Service Layer w celu
zapewnienia separacji odpowiedzialności (Separation of Concerns).
"""

import logging
import math
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Priority, Status, Task
from schemas import TaskCreate, TaskUpdate
from services.cache_service import cache_delete, cache_get, cache_invalidate_pattern, cache_set

# Logger dla serwisu zadań
logger = logging.getLogger(__name__)

# Prefiks kluczy cache dla zadań
CACHE_PREFIX = "taskflow"
CACHE_TTL = 300  # 5 minut


class TaskService:
    """
    Logika biznesowa do zarządzania zadaniami.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicjalizacja serwisu sesją bazy danych.
        """
        self.db = db

    async def create_task(self, task_data: TaskCreate) -> Task:
        """
        Dodanie nowego zadania do bazy danych.
        """
        # Tworzenie obiektu modelu z danych wejściowych
        new_task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
        )

        # Zapis do bazy
        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task)

        # Unieważnienie cache list zadań
        await cache_invalidate_pattern(f"{CACHE_PREFIX}:tasks:*")

        logger.info("Utworzono zadanie: id=%d, title='%s'", new_task.id, new_task.title)
        return new_task

    async def get_task(self, task_id: int) -> Optional[Task]:
        """
        Pobranie zadania po ID (wzorzec Cache-Aside).
        """
        cache_key = f"{CACHE_PREFIX}:task:{task_id}"

        # 1. Sprawdzenie cache
        cached = await cache_get(cache_key)
        if cached:
            logger.debug("Pobrano zadanie id=%d z cache", task_id)
            return await self._get_task_from_db(task_id)

        # 2. Pobranie z bazy danych
        task = await self._get_task_from_db(task_id)

        # 3. Zapis do cache w razie trafienia
        if task:
            await cache_set(cache_key, {"id": task.id, "found": True}, ttl=CACHE_TTL)

        return task

    async def _get_task_from_db(self, task_id: int) -> Optional[Task]:
        """
        Pobranie zadania bezpośrednio z bazy danych (bez cache).
        """
        query = select(Task).where(Task.id == task_id, Task.is_deleted.is_(False))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_tasks(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[Status] = None,
        priority: Optional[Priority] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict:
        """
        Pobranie listy zadań z filtrowaniem, sortowaniem i paginacją.
        """
        # Ograniczono per_page do zakresu 1-100
        per_page = max(1, min(per_page, 100))

        # Zbudowano zapytanie bazowe — wykluczono zadania usunięte
        query = select(Task).where(Task.is_deleted.is_(False))
        count_query = select(func.count(Task.id)).where(Task.is_deleted.is_(False))

        # Zastosowano filtry (jeśli podano)
        if status:
            query = query.where(Task.status == status)
            count_query = count_query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
            count_query = count_query.where(Task.priority == priority)

        # Zastosowano sortowanie
        sort_column = getattr(Task, sort_by, Task.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Obliczono paginację
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        pages = math.ceil(total / per_page) if total > 0 else 1
        offset = (page - 1) * per_page

        # Wykonano zapytanie z paginacją
        query = query.offset(offset).limit(per_page)
        result = await self.db.execute(query)
        tasks = result.scalars().all()

        logger.debug(
            "Pobrano listę zadań: page=%d, per_page=%d, total=%d",
            page, per_page, total
        )

        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    async def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """
        Aktualizacja istniejącego zadania.

        Zastosowano wzorzec Partial Update — zmieniamy tylko przesłane pola.
        """
        task = await self._get_task_from_db(task_id)
        if not task:
            return None

        # Aktualizacja tylko przesłanych pól (exclude_unset=True pomija None)
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        await self.db.commit()
        await self.db.refresh(task)

        # Usunięcie starych danych z cache
        await cache_delete(f"{CACHE_PREFIX}:task:{task_id}")
        await cache_invalidate_pattern(f"{CACHE_PREFIX}:tasks:*")

        logger.info("Zaktualizowano zadanie: id=%d, pola=%s", task_id, list(update_data.keys()))
        return task

    async def delete_task(self, task_id: int) -> bool:
        """
        Usunięcie zadania (soft-delete).

        Ustawia flagę is_deleted=True i zmienia status na ARCHIVED.
        """
        task = await self._get_task_from_db(task_id)
        if not task:
            return False

        # Soft-delete
        task.is_deleted = True
        task.status = Status.ARCHIVED

        await self.db.commit()

        # Usunięcie z cache
        await cache_delete(f"{CACHE_PREFIX}:task:{task_id}")
        await cache_invalidate_pattern(f"{CACHE_PREFIX}:tasks:*")

        logger.info("Usunięto zadanie (soft-delete): id=%d", task_id)
        return True

    async def get_task_stats(self) -> dict:
        """
        Pobranie statystyk zadań (na potrzeby metryk).
        """
        # Grupowanie po statusie
        status_query = (
            select(Task.status, func.count(Task.id))
            .where(Task.is_deleted.is_(False))
            .group_by(Task.status)
        )
        status_result = await self.db.execute(status_query)
        tasks_by_status = {row[0].value: row[1] for row in status_result}

        # Grupowanie po priorytecie
        priority_query = (
            select(Task.priority, func.count(Task.id))
            .where(Task.is_deleted.is_(False))
            .group_by(Task.priority)
        )
        priority_result = await self.db.execute(priority_query)
        tasks_by_priority = {row[0].value: row[1] for row in priority_result}

        # Łączna liczba zadań
        total_query = select(func.count(Task.id)).where(Task.is_deleted.is_(False))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        return {
            "total_tasks": total,
            "tasks_by_status": tasks_by_status,
            "tasks_by_priority": tasks_by_priority,
        }
