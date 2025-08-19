# This file contains basic tests for the FastAPI server.
import pytest
from httpx import AsyncClient
from server.main import app

@pytest.mark.asyncio
async def test_read_main():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to the Trading Bot API. Visit /docs for API documentation."
}

@pytest.mark.asyncio
async def test_list_bots():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/bots")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0
        assert "id" in response.json()[0]
        assert "mode" in response.json()[0]
        assert "status" in response.json()[0]

@pytest.mark.asyncio
async def test_get_global_metrics():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/metrics/global")
        assert response.status_code == 200
        assert "bots_running" in response.json()
        assert "total_equity" in response.json()
