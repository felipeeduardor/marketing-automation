"""Tests for the chatbot module."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"


@pytest.mark.anyio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.anyio
@patch("app.modules.chatbot.agent_manager.agent_manager.process_message")
async def test_chat_endpoint(mock_process, client):
    mock_process.return_value = ("Olá! Como posso ajudar?", "FAQ")

    response = await client.post(
        "/api/v1/chatbot/chat",
        json={
            "session_id": "test-123",
            "message": "Olá, quero saber sobre os planos",
            "channel": "web",
        },
        headers={"X-Tenant-ID": "test-tenant"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-123"
    assert data["agent_used"] == "FAQ"
    assert "Olá" in data["response"]


@pytest.mark.anyio
async def test_session_history(client):
    response = await client.get("/api/v1/chatbot/sessions/nonexistent/history")
    assert response.status_code == 200
    data = response.json()
    assert data["messages"] == []


@pytest.mark.anyio
async def test_clear_session(client):
    response = await client.delete("/api/v1/chatbot/sessions/test-123")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
