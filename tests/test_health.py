"""
Testy endpointów monitoringu: / (strona HTML) i /health (status aplikacji).
"""

import pytest


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Strona glowna powinna zwracac HTML ze slowem 'TaskFlow'."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TaskFlow" in response.text



@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Health check powinien zwracac status, nazwe aplikacji i informacje o DB i Redis."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["app_name"] == "TaskFlow"
    assert "database" in data
    assert "redis" in data
