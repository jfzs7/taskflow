"""
Testy endpointów health check aplikacji TaskFlow.

Przetestowano endpointy monitoringu: /health i /.
"""

import pytest


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Sprawdzono endpoint główny (/) — zwraca stronę HTML panelu użytkownika."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TaskFlow" in response.text



@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Sprawdzono endpoint health check (/health)."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["app_name"] == "TaskFlow"
    assert "database" in data
    assert "redis" in data
