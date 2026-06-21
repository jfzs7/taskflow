"""
Testy endpointów CRUD zadań aplikacji TaskFlow.

Przetestowano pełen cykl operacji na zadaniach:
tworzenie, odczyt, aktualizację, usuwanie, filtrowanie i paginację.
"""

import pytest


@pytest.mark.asyncio
async def test_create_task(client):
    """Sprawdzono tworzenie nowego zadania z poprawnymi danymi."""
    response = await client.post("/api/v1/tasks/", json={
        "title": "Testowe zadanie",
        "description": "Opis testowego zadania",
        "priority": "high",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Testowe zadanie"
    assert data["priority"] == "high"
    assert data["status"] == "todo"
    assert data["is_deleted"] is False


@pytest.mark.asyncio
async def test_create_task_minimal(client):
    """Sprawdzono tworzenie zadania z minimalnymi danymi (tylko tytuł)."""
    response = await client.post("/api/v1/tasks/", json={"title": "Minimalne zadanie"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimalne zadanie"
    assert data["priority"] == "medium"  # domyślny priorytet


@pytest.mark.asyncio
async def test_create_task_empty_title(client):
    """Sprawdzono odrzucenie zadania z pustym tytułem."""
    response = await client.post("/api/v1/tasks/", json={"title": ""})
    assert response.status_code == 422  # Validation Error


@pytest.mark.asyncio
async def test_get_tasks_empty(client):
    """Sprawdzono pobranie pustej listy zadań."""
    response = await client.get("/api/v1/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert data["tasks"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_tasks_with_data(client):
    """Sprawdzono pobranie listy z utworzonymi zadaniami."""
    # Utworzono 3 zadania
    for i in range(3):
        await client.post("/api/v1/tasks/", json={"title": f"Zadanie {i+1}"})

    response = await client.get("/api/v1/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["tasks"]) == 3


@pytest.mark.asyncio
async def test_get_task_by_id(client):
    """Sprawdzono pobranie zadania po identyfikatorze."""
    # Utworzono zadanie
    create_resp = await client.post("/api/v1/tasks/", json={"title": "Do pobrania"})
    task_id = create_resp.json()["id"]

    # Pobrano zadanie
    response = await client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Do pobrania"


@pytest.mark.asyncio
async def test_get_task_not_found(client):
    """Sprawdzono odpowiedź 404 dla nieistniejącego zadania."""
    response = await client.get("/api/v1/tasks/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task(client):
    """Sprawdzono aktualizację zadania (partial update)."""
    create_resp = await client.post("/api/v1/tasks/", json={"title": "Do aktualizacji"})
    task_id = create_resp.json()["id"]

    response = await client.patch(f"/api/v1/tasks/{task_id}", json={
        "title": "Zaktualizowane",
        "status": "in_progress",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Zaktualizowane"
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_delete_task(client):
    """Sprawdzono usuwanie zadania (soft-delete)."""
    create_resp = await client.post("/api/v1/tasks/", json={"title": "Do usunięcia"})
    task_id = create_resp.json()["id"]

    # Usunięto zadanie
    response = await client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200

    # Sprawdzono, że zadanie nie jest już dostępne
    get_resp = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_filter_by_status(client):
    """Sprawdzono filtrowanie zadań po statusie."""
    await client.post("/api/v1/tasks/", json={"title": "Zadanie TODO"})
    create_resp = await client.post("/api/v1/tasks/", json={"title": "Zadanie IN_PROGRESS"})
    task_id = create_resp.json()["id"]
    await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "in_progress"})

    # Filtrowanie po statusie 'todo'
    response = await client.get("/api/v1/tasks/?status=todo")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_pagination(client):
    """Sprawdzono paginację listy zadań."""
    for i in range(5):
        await client.post("/api/v1/tasks/", json={"title": f"Zadanie {i+1}"})

    # Strona 1, po 2 elementy
    response = await client.get("/api/v1/tasks/?page=1&per_page=2")
    data = response.json()
    assert len(data["tasks"]) == 2
    assert data["total"] == 5
    assert data["pages"] == 3
