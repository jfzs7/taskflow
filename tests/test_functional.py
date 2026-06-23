"""
Funkcjonalne testy integracyjne (End-to-End) dla API TaskFlow.
Te testy sprawdzają złożone scenariusze biznesowe i przypadki użycia,
obejmujące wiele zapytań HTTP w jednym ciągu.
"""

import pytest

@pytest.mark.asyncio
async def test_full_task_lifecycle(client):
    """
    Scenariusz 1: Pełen cykl życia zadania.
    Kroki:
    1. Utworzenie zadania
    2. Sprawdzenie, czy zostało poprawnie dodane do bazy (GET)
    3. Zmiana priorytetu i statusu zadania (PATCH)
    4. Usunięcie zadania (DELETE - soft delete)
    5. Próba pobrania usuniętego zadania (oczekiwane 404)
    """
    # 1. Tworzenie
    create_response = await client.post("/api/v1/tasks/", json={
        "title": "Zadanie do pełnego cyklu",
        "description": "Testowy opis zadania, które przejdzie przez wszystkie stany",
        "priority": "low"
    })
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    # 2. Odczyt i weryfikacja
    get_response = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == 200
    task_data = get_response.json()
    assert task_data["title"] == "Zadanie do pełnego cyklu"
    assert task_data["status"] == "todo"
    assert task_data["priority"] == "low"

    # 3. Aktualizacja statusu i priorytetu
    update_response = await client.patch(f"/api/v1/tasks/{task_id}", json={
        "status": "done",
        "priority": "high",
        "description": "Zaktualizowany opis"
    })
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["status"] == "done"
    assert updated_data["priority"] == "high"
    assert updated_data["description"] == "Zaktualizowany opis"

    # 4. Usunięcie zadania (soft-delete)
    delete_response = await client.delete(f"/api/v1/tasks/{task_id}")
    assert delete_response.status_code == 200

    # 5. Weryfikacja usunięcia
    get_deleted_response = await client.get(f"/api/v1/tasks/{task_id}")
    assert get_deleted_response.status_code == 404


@pytest.mark.asyncio
async def test_filtering_and_pagination_combination(client):
    """
    Scenariusz 2: Łączenie filtrowania, paginacji i sortowania.
    Kroki:
    1. Utworzenie serii zadań z różnymi statusami.
    2. Pobranie zadań z określonym statusem (todo) na drugiej stronie (page=2, per_page=2).
    """
    # 1. Przygotowanie danych
    for i in range(5):
        await client.post("/api/v1/tasks/", json={"title": f"Zadanie TODO {i}"})
    for i in range(3):
        await client.post("/api/v1/tasks/", json={"title": f"Zadanie IN_PROGRESS {i}"})
        task_id = (await client.get("/api/v1/tasks/") ).json()["tasks"][0]["id"]
        await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "in_progress"})
        
    # Pobranie strony 2, tylko dla statusu 'todo', rozmiar strony: 2
    # Skoro stworzyliśmy 5 zadań TODO, powinno być 3 strony (2, 2, 1)
    response = await client.get("/api/v1/tasks/?status=todo&page=2&per_page=2")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["per_page"] == 2
    assert data["pages"] == 3
    assert len(data["tasks"]) == 2
    for task in data["tasks"]:
        assert task["status"] == "todo"


@pytest.mark.asyncio
async def test_validation_and_error_handling(client):
    """
    Scenariusz 3: Walidacja danych biznesowych i błędy API.
    Kroki:
    1. Próba dodania zadania bez wymaganego tytułu (422)
    2. Próba aktualizacji nieistniejącego zadania (404)
    3. Próba ustawienia nieprawidłowego statusu w PATCH
    """
    # 1. Walidacja wymaganego pola 'title'
    invalid_create = await client.post("/api/v1/tasks/", json={
        "description": "Brak tytułu"
    })
    assert invalid_create.status_code == 422
    assert "detail" in invalid_create.json()

    # 2. Aktualizacja nieistniejącego zadania
    not_found_update = await client.patch("/api/v1/tasks/99999", json={
        "status": "done"
    })
    assert not_found_update.status_code == 404

    # 3. Dodanie zadania, a potem próba nadania nieprawidłowego statusu
    create_response = await client.post("/api/v1/tasks/", json={"title": "Poprawne"})
    task_id = create_response.json()["id"]

    invalid_patch = await client.patch(f"/api/v1/tasks/{task_id}", json={
        "status": "nieistniejacy_status"
    })
    assert invalid_patch.status_code == 422
