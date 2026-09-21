import pytest


@pytest.mark.asyncio
async def test_health_is_safe_and_ready(api_client):
    response = await api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Upwork AI Career Agent",
        "environment": "development",
        "ai_provider": "disabled",
    }
