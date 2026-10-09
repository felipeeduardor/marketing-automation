"""Tests for the internal-API access control."""

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.utils.auth import require_admin


@pytest.fixture
async def client():
    app = FastAPI()

    @app.get("/internal", dependencies=[Depends(require_admin)])
    async def internal():
        return {"ok": True}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_locked_when_token_not_configured(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "ADMIN_API_TOKEN", "")
    assert (await client.get("/internal", headers={"Authorization": "Bearer qualquer"})).status_code == 503


@pytest.mark.anyio
async def test_rejects_missing_or_wrong_token(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "ADMIN_API_TOKEN", "token-certo")
    assert (await client.get("/internal")).status_code == 401
    assert (await client.get("/internal", headers={"Authorization": "Bearer errado"})).status_code == 401


@pytest.mark.anyio
async def test_accepts_correct_token(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "ADMIN_API_TOKEN", "token-certo")
    response = await client.get("/internal", headers={"Authorization": "Bearer token-certo"})
    assert response.status_code == 200


@pytest.fixture
async def app_client(monkeypatch):
    from app.main import app

    monkeypatch.setattr(get_settings(), "ADMIN_API_TOKEN", "token-certo")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.anyio
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/crm/overview",
        "/api/v1/operations/overview",
        "/api/v1/marketing/insights",
        "/api/v1/vsl/metrics",
        "/api/v1/tracking/leads",
        "/api/v1/tracking/channels/stats",
    ],
)
async def test_internal_routes_require_token(app_client, path):
    assert (await app_client.get(path)).status_code == 401


@pytest.mark.anyio
async def test_vsl_page_stays_public(app_client):
    assert (await app_client.get("/vsl")).status_code == 200
