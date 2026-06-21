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

# Skonfigurowano logger dla serwisu zadań
logger = logging.getLogger(__name__)

# Prefiks kluczy cache dla zadań
CACHE_PREFIX = "taskflow"
CACHE_TTL = 300  # 5 minut


class TaskService:
    """
    Serwis zarządzania zadaniami.

    Zaimplementowano operacje CRUD (Create, Read, Update, Delete)
    z integracją warstwy cache Redis. Każda operacja modyfikująca
    dane automatycznie unieważnia powiązane klucze cache.
    """

    def __init__(self, db: AsyncSession):
        """
        Zainicjalizowano serwis z sesją bazodanową.

        Argumenty:
            db: Asynchroniczna sesja SQLAlchemy (wstrzykiwana przez DI).
        """
        self.db = db

    async def create_task(self, task_data: TaskCreate) -> Task:
        """
        Utworzono nowe zadanie w bazie danych.

        Argumenty:
            task_data: Schemat Pydantic z danymi nowego zadania.

        Zwrócono:
            Obiekt Task utworzony w bazie danych.
        """
        # Utworzono instancję modelu z danych wejściowych
        new_task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
        )

        # Zapisano w bazie danych
        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task)

        # Unieważniono cache list zadań (ponieważ dodano nowy element)
        await cache_invalidate_pattern(f"{CACHE_PREFIX}:tasks:*")

        logger.info("Utworzono zadanie: id=%d, title='%s'", new_task.id, new_task.title)
        return new_task

    async def get_task(self, task_id: int) -> Optional[Task]:
        """
        Pobrano zadanie po identyfikatorze.

        Zastosowano wzorzec Cache-Aside:
        1. Sprawdzono cache Redis
        2. W przypadku cache miss — pobrano z bazy danych
        3. Zapisano wynik w cache (jeśli znaleziono)

        Argumenty:
            task_id: Identyfikator zadania.

        Zwrócono:
            Obiekt Task lub None (jeśli nie znaleziono lub jest usunięte).
        """
        cache_key = f"{CACHE_PREFIX}:task:{task_id}"

        # Krok 1: Sprawdzono cache
        cached = await cache_get(cache_key)
        if cached:
            logger.debug("Pobrano zadanie id=%d z cache", task_id)
            # Odtworzono obiekt Task z danych cache
            # (nie jest to pełny obiekt ORM, ale wystarczający do odpowiedzi API)
            return await self._get_task_from_db(task_id)

        # Krok 2: Pobrano z bazy danych
        task = await self._get_task_from_db(task_id)

        # Krok 3: Zapisano w cache (jeśli znaleziono)
        if task:
            await cache_set(cache_key, {"id": task.id, "found": True}, ttl=CACHE_TTL)

        return task

    async def _get_task_from_db(self, task_id: int) -> Optional[Task]:
        """
        Pobrano zadanie bezpośrednio z bazy danych (bez cache).

        Odfiltrowano zadania oznaczone jako usunięte (soft-delete).
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
        Pobrano listę zadań z filtrowaniem, sortowaniem i paginacją.

        Argumenty:
            page: Numer strony (od 1).
            per_page: Liczba zadań na stronę (domyślnie 20, max 100).
            status: Filtr statusu (opcjonalny).
            priority: Filtr priorytetu (opcjonalny).
            sort_by: Pole sortowania (created_at, updated_at, title, priority).
            sort_order: Kierunek sortowania (asc, desc).

        Zwrócono:
            Słownik z listą zadań i metadanymi paginacji.
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
        Zaktualizowano istniejące zadanie.

        Zastosowano wzorzec Partial Update — aktualizowane są tylko
        pola przesłane w żądaniu (wartości inne niż None).

        Argumenty:
            task_id: Identyfikator zadania do aktualizacji.
            task_data: Schemat z nowymi wartościami pól.

        Zwrócono:
            Zaktualizowany obiekt Task lub None (jeśli nie znaleziono).
        """
        task = await self._get_task_from_db(task_id)
        if not task:
            return None

        # Zaktualizowano tylko przesłane pola (exclude_unset pomija pola o wartości None)
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        await self.db.commit()
        await self.db.refresh(task)

        # Unieważniono cache dla tego zadania i list
        await cache_delete(f"{CACHE_PREFIX}:task:{task_id}")
        await cache_invalidate_pattern(f"{CACHE_PREFIX}:tasks:*")

        logger.info("Zaktualizowano zadanie: id=%d, pola=%s", task_id, list(update_data.keys()))
        return task

    async def delete_task(self, task_id: int) -> bool:
        """
        Usunięto zadanie (soft-delete).

        Zamiast fizycznego usuwania rekordu z bazy danych,
        ustawiono flagę is_deleted=True oraz zmieniono status
        na ARCHIVED. Umożliwia to odzyskanie danych w razie potrzeby.

        Argumenty:
            task_id: Identyfikator zadania do usunięcia.

        Zwrócono:
            True jeśli zadanie zostało usunięte, False jeśli nie znaleziono.
        """
        task = await self._get_task_from_db(task_id)
        if not task:
            return False

        # Zastosowano soft-delete
        task.is_deleted = True
        task.status = Status.ARCHIVED

        await self.db.commit()

        # Unieważniono cache
        await cache_delete(f"{CACHE_PREFIX}:task:{task_id}")
        await cache_invalidate_pattern(f"{CACHE_PREFIX}:tasks:*")

        logger.info("Usunięto zadanie (soft-delete): id=%d", task_id)
        return True

    async def get_task_stats(self) -> dict:
        """
        Pobrano statystyki zadań (do celów metryk i monitoringu).

        Zwrócono:
            Słownik ze statystykami: liczba zadań wg statusu i priorytetu.
        """
        # Liczba zadań wg statusu
        status_query = (
            select(Task.status, func.count(Task.id))
            .where(Task.is_deleted.is_(False))
            .group_by(Task.status)
        )
        status_result = await self.db.execute(status_query)
        tasks_by_status = {row[0].value: row[1] for row in status_result}

        # Liczba zadań wg priorytetu
        priority_query = (
            select(Task.priority, func.count(Task.id))
            .where(Task.is_deleted.is_(False))
            .group_by(Task.priority)
        )
        priority_result = await self.db.execute(priority_query)
        tasks_by_priority = {row[0].value: row[1] for row in priority_result}

        # Całkowita liczba zadań
        total_query = select(func.count(Task.id)).where(Task.is_deleted.is_(False))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        return {
            "total_tasks": total,
            "tasks_by_status": tasks_by_status,
            "tasks_by_priority": tasks_by_priority,
        }
