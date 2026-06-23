"""
Warstwa logiki biznesowej dla zadan (Service Layer).

Endpointy w routes/tasks.py sa cienkie — tylko HTTP.
Cala logika (SQL, cache, stronicowanie) jest tu.
Dzieki temu mozna testowac logike bez uruchamiania serwera HTTP.
"""

import logging
import math
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Priority, Status, Task
from schemas import TaskCreate, TaskUpdate
from services.cache_service import cache_delete, cache_get, cache_invalidate_pattern, cache_set

logger = logging.getLogger(__name__)

CACHE_PREFIX = "taskflow"
CACHE_TTL = 300  # 5 minut


class TaskService:
    """Logika CRUD dla zadan z integracj Cache-Aside."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task_data: TaskCreate) -> Task:
        """Tworzy zadanie w bazie i uniewa?nia cache list zadan."""
        new_task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
        )
        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task)  # refresh pobiera id nadane przez baze

        # Lista zadan w cache jest juz nieaktualna — usuwamy ja.
        await cache_invalidate_pattern(f"{CACHE_PREFIX}:tasks:*")

        logger.info("[OK] Zadanie utworzone: id=%d, title='%s'", new_task.id, new_task.title)
        return new_task

    async def get_task(self, task_id: int) -> Optional[Task]:
        """
        Pobiera zadanie po ID (Cache-Aside).
        Najpierw sprawdza Redis — przy MISS idzie do bazy i zapisuje wynik do cache.
        """
        cache_key = f"{CACHE_PREFIX}:task:{task_id}"

        cached = await cache_get(cache_key)
        if cached:
            # Cache trzyma tylko marker ze zadanie istnieje — i tak ladujemy z bazy
            # (SQLAlchemy ORM nie serializuje sie trywialnie do JSON)
            return await self._get_task_from_db(task_id)

        task = await self._get_task_from_db(task_id)
        if task:
            await cache_set(cache_key, {"id": task.id, "found": True}, ttl=CACHE_TTL)

        return task

    async def _get_task_from_db(self, task_id: int) -> Optional[Task]:
        """Bezposrednie zapytanie do bazy — wyklucza zadania usuniete (soft-delete)."""
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
        Lista zadan z filtrowaniem, sortowaniem i paginacja.
        Wykonuje dwa zapytania: COUNT(*) dla paginacji + SELECT z danymi.
        """
        per_page = max(1, min(per_page, 100))  # bezpieczny zakres

        # Bazowe zapytania — automatycznie wyklucz usuniete rekordy
        query = select(Task).where(Task.is_deleted.is_(False))
        count_query = select(func.count(Task.id)).where(Task.is_deleted.is_(False))

        # Opcjonalne filtry
        if status:
            query = query.where(Task.status == status)
            count_query = count_query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
            count_query = count_query.where(Task.priority == priority)

        # Dynamiczne sortowanie — sort_by walidowany regexem w routerze
        sort_column = getattr(Task, sort_by, Task.created_at)
        query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        # Paginacja
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        pages = math.ceil(total / per_page) if total > 0 else 1
        offset = (page - 1) * per_page

        result = await self.db.execute(query.offset(offset).limit(per_page))
        tasks = result.scalars().all()

        logger.debug("[OK] Lista zadan: page=%d, per_page=%d, total=%d", page, per_page, total)

        return {"tasks": tasks, "total": total, "page": page, "per_page": per_page, "pages": pages}

    async def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """
        Czesciowa aktualizacja zadania (Partial Update).
        exclude_unset=True — aktualizujemy tylko pola ktore klient faktycznie przeslal.
        """
        task = await self._get_task_from_db(task_id)
        if not task:
            return None

        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        await self.db.commit()
        await self.db.refresh(task)

        # Usuwamy konkretne zadanie i listy z cache
        await cache_delete(f"{CACHE_PREFIX}:task:{task_id}")
        await cache_invalidate_pattern(f"{CACHE_PREFIX}:tasks:*")

        logger.info("[OK] Zadanie zaktualizowane: id=%d, pola=%s", task_id, list(update_data.keys()))
        return task

    async def delete_task(self, task_id: int) -> bool:
        """
        Soft-delete: ustawia is_deleted=True i status=ARCHIVED.
        Rekord pozostaje w bazie — mozliwy audyt i odtworzenie danych.
        """
        task = await self._get_task_from_db(task_id)
        if not task:
            return False

        task.is_deleted = True
        task.status = Status.ARCHIVED
        await self.db.commit()

        await cache_delete(f"{CACHE_PREFIX}:task:{task_id}")
        await cache_invalidate_pattern(f"{CACHE_PREFIX}:tasks:*")

        logger.info("[OK] Zadanie usuniete (soft-delete): id=%d", task_id)
        return True

    async def get_task_stats(self) -> dict:
        """Statystyki zadan dla endpointow /metrics i /prometheus."""
        # Grupowanie po statusie
        status_result = await self.db.execute(
            select(Task.status, func.count(Task.id))
            .where(Task.is_deleted.is_(False))
            .group_by(Task.status)
        )
        tasks_by_status = {row[0].value: row[1] for row in status_result}

        # Grupowanie po priorytecie
        priority_result = await self.db.execute(
            select(Task.priority, func.count(Task.id))
            .where(Task.is_deleted.is_(False))
            .group_by(Task.priority)
        )
        tasks_by_priority = {row[0].value: row[1] for row in priority_result}

        # Suma
        total_result = await self.db.execute(
            select(func.count(Task.id)).where(Task.is_deleted.is_(False))
        )
        total = total_result.scalar() or 0

        return {"total_tasks": total, "tasks_by_status": tasks_by_status,
                "tasks_by_priority": tasks_by_priority}
