"""
Moduł endpointów CRUD zadań aplikacji TaskFlow.

Zaimplementowano pełen zestaw operacji REST API:
- POST   /api/v1/tasks      — utworzenie nowego zadania
- GET    /api/v1/tasks      — pobranie listy zadań
- GET    /api/v1/tasks/{id} — pobranie pojedynczego zadania
- PATCH  /api/v1/tasks/{id} — aktualizacja zadania
- DELETE /api/v1/tasks/{id} — usunięcie zadania (soft-delete)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Priority, Status
from schemas import MessageResponse, TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from services.task_service import TaskService

router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["Zadania (Tasks)"],
    responses={404: {"description": "Zadanie nie znalezione"}},
)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED,
             summary="Utwórz nowe zadanie")
async def create_task(task_data: TaskCreate, db: AsyncSession = Depends(get_db)):
    """Endpoint tworzenia nowego zadania."""
    service = TaskService(db)
    return await service.create_task(task_data)


@router.get("/", response_model=TaskListResponse, summary="Pobierz listę zadań")
async def get_tasks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    task_status: Optional[Status] = Query(None, alias="status"),
    priority: Optional[Priority] = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|title|priority|status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint pobierania listy zadań z filtrowaniem i paginacją."""
    service = TaskService(db)
    return await service.get_tasks(page=page, per_page=per_page, status=task_status,
                                   priority=priority, sort_by=sort_by, sort_order=sort_order)


@router.get("/{task_id}", response_model=TaskResponse, summary="Pobierz zadanie po ID")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Endpoint pobierania pojedynczego zadania."""
    service = TaskService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Zadanie o id={task_id} nie znalezione.")
    return task


@router.patch("/{task_id}", response_model=TaskResponse, summary="Zaktualizuj zadanie")
async def update_task(task_id: int, task_data: TaskUpdate, db: AsyncSession = Depends(get_db)):
    """Endpoint aktualizacji zadania (partial update)."""
    service = TaskService(db)
    task = await service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail=f"Zadanie o id={task_id} nie znalezione.")
    return task


@router.delete("/{task_id}", response_model=MessageResponse, summary="Usuń zadanie")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Endpoint usuwania zadania (soft-delete)."""
    service = TaskService(db)
    deleted = await service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Zadanie o id={task_id} nie znalezione.")
    return MessageResponse(message="Zadanie usunięte.", detail=f"Zadanie id={task_id} zarchiwizowane.")
