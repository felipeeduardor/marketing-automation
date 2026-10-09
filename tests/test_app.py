"""Smoke tests for the application entrypoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


@pytest.mark.anyio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_database_url_gets_async_driver():
    from app.database import async_database_url

    assert async_database_url("postgresql://u:p@host:5432/db") == "postgresql+asyncpg://u:p@host:5432/db"
    assert async_database_url("postgres://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"
    assert async_database_url("postgresql+asyncpg://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"
