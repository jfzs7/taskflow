"""
Testy CRUD zadan (POST/GET/PATCH/DELETE) przez HTTP.
Kazdy test dziala na czystej bazie SQLite — patrz conftest.py.
"""

import pytest


@pytest.mark.asyncio
async def test_create_task(client):
    """Sprawdzenie tworzenia nowego zadania z poprawnymi danymi."""
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
    """Sprawdzenie tworzenia zadania z minimalnymi danymi (tylko tytuł)."""
    response = await client.post("/api/v1/tasks/", json={"title": "Minimalne zadanie"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimalne zadanie"
    assert data["priority"] == "medium"  # domyślny priorytet


@pytest.mark.asyncio
async def test_create_task_empty_title(client):
    """Sprawdzenie odrzucenia zadania z pustym tytułem."""
    response = await client.post("/api/v1/tasks/", json={"title": ""})
    assert response.status_code == 422  # Validation Error


@pytest.mark.asyncio
async def test_get_tasks_empty(client):
    """Sprawdzenie pobrania pustej listy zadań."""
    response = await client.get("/api/v1/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert data["tasks"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_tasks_with_data(client):
    """Sprawdzenie pobrania listy z utworzonymi zadaniami."""
    # Tworzenie 3 zadań
    for i in range(3):
        await client.post("/api/v1/tasks/", json={"title": f"Zadanie {i+1}"})

    response = await client.get("/api/v1/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["tasks"]) == 3


@pytest.mark.asyncio
async def test_get_task_by_id(client):
    """Sprawdzenie pobrania zadania po ID."""
    # Tworzenie zadania
    create_resp = await client.post("/api/v1/tasks/", json={"title": "Do pobrania"})
    task_id = create_resp.json()["id"]

    # Pobranie zadania
    response = await client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Do pobrania"


@pytest.mark.asyncio
async def test_get_task_not_found(client):
    """Sprawdzenie odpowiedzi 404 dla nieistniejącego zadania."""
    response = await client.get("/api/v1/tasks/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task(client):
    """Sprawdzenie aktualizacji zadania (partial update)."""
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
    """Sprawdzenie usuwania zadania (soft-delete)."""
    create_resp = await client.post("/api/v1/tasks/", json={"title": "Do usunięcia"})
    task_id = create_resp.json()["id"]

    # Usunięcie zadania
    response = await client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200

    # Sprawdzenie czy jest niedostępne
    get_resp = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_filter_by_status(client):
    """Sprawdzenie filtrowania zadań po statusie."""
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
    """Sprawdzenie paginacji listy zadań."""
    for i in range(5):
        await client.post("/api/v1/tasks/", json={"title": f"Zadanie {i+1}"})

    # Strona 1, po 2 elementy
    response = await client.get("/api/v1/tasks/?page=1&per_page=2")
    data = response.json()
    assert len(data["tasks"]) == 2
    assert data["total"] == 5
    assert data["pages"] == 3
