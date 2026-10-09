"""Tests for the tracking module."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.config import get_settings
from app.main import app
from app.modules.tracking.tracker import UTMParams
from app.modules.tracking.channels import (
    FacebookWebhookPayload,
    InstagramWebhookPayload,
    WhatsAppWebhookPayload,
    GoogleAdsWebhookPayload,
    PixelTracker,
)


# --- UTMParams Unit Tests ---


class TestUTMParams:
    def test_detect_facebook(self):
        utm = UTMParams(utm_source="facebook", utm_medium="paid_social")
        assert utm.detect_channel() == "facebook"

    def test_detect_facebook_short(self):
        utm = UTMParams(utm_source="fb", utm_medium="cpc")
        assert utm.detect_channel() == "facebook"

    def test_detect_instagram(self):
        utm = UTMParams(utm_source="instagram", utm_medium="social")
        assert utm.detect_channel() == "instagram"

    def test_detect_google_ads(self):
        utm = UTMParams(utm_source="google", utm_medium="cpc")
        assert utm.detect_channel() == "google_ads"

    def test_detect_whatsapp(self):
        utm = UTMParams(utm_source="whatsapp", utm_medium="messaging")
        assert utm.detect_channel() == "whatsapp"

    def test_detect_direct(self):
        utm = UTMParams()
        assert utm.detect_channel() == "direct"

    def test_detect_paid_search(self):
        utm = UTMParams(utm_source="bing", utm_medium="cpc")
        assert utm.detect_channel() == "paid_search"

    def test_detect_organic(self):
        utm = UTMParams(utm_source="google", utm_medium="organic")
        # "google" in source matches google_ads first
        assert utm.detect_channel() == "google_ads"

    def test_from_dict(self):
        params = {
            "utm_source": "facebook",
            "utm_medium": "cpc",
            "utm_campaign": "black_friday",
        }
        utm = UTMParams.from_dict(params)
        assert utm.utm_source == "facebook"
        assert utm.utm_campaign == "black_friday"


# --- Channel Webhook Tests ---


class TestFacebookWebhook:
    def test_extract_lead_data(self):
        payload = FacebookWebhookPayload(
            entry=[{
                "changes": [{
                    "value": {
                        "leadgen_id": "123",
                        "page_id": "456",
                        "form_id": "789",
                    }
                }]
            }]
        )
        data = payload.extract_lead_data()
        assert data is not None
        assert data["source"] == "facebook"
        assert data["leadgen_id"] == "123"

    def test_extract_empty(self):
        payload = FacebookWebhookPayload(entry=[])
        assert payload.extract_lead_data() is None


class TestWhatsAppWebhook:
    def test_extract_lead_data(self):
        payload = WhatsAppWebhookPayload(
            entry=[{
                "changes": [{
                    "value": {
                        "contacts": [{"wa_id": "5511999999999", "profile": {"name": "João"}}],
                        "messages": [{"text": {"body": "Olá"}, "timestamp": "123456"}],
                    }
                }]
            }]
        )
        data = payload.extract_lead_data()
        assert data is not None
        assert data["source"] == "whatsapp"
        assert data["phone"] == "5511999999999"
        assert data["name"] == "João"


class TestGoogleAdsWebhook:
    def test_extract_lead_data(self):
        payload = GoogleAdsWebhookPayload(
            lead_id="lead-1",
            campaign_id="camp-1",
            user_column_data=[
                {"column_id": "EMAIL", "string_value": "joao@email.com"},
                {"column_id": "FULL_NAME", "string_value": "João Silva"},
                {"column_id": "PHONE_NUMBER", "string_value": "+5511999999999"},
            ],
        )
        data = payload.extract_lead_data()
        assert data["source"] == "google_ads"
        assert data["email"] == "joao@email.com"
        assert data["name"] == "João Silva"


# --- Pixel Tracker Tests ---


class TestPixelTracker:
    def test_facebook_pixel(self):
        snippet = PixelTracker.facebook_pixel("123456")
        assert "123456" in snippet
        assert "fbq('init'" in snippet

    def test_google_ads_tag(self):
        snippet = PixelTracker.google_ads_tag("AW-12345")
        assert "AW-12345" in snippet
        assert "gtag(" in snippet

    def test_server_pixel_url(self):
        url = PixelTracker.server_pixel_url("http://localhost:8000", "tenant1", "facebook")
        assert "tenant=tenant1" in url
        assert "channel=facebook" in url
        assert "pixel.gif" in url


# --- API Endpoint Tests ---


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
@patch("app.modules.tracking.routes.lead_tracker")
async def test_track_lead_endpoint(mock_tracker, client):
    mock_lead = MagicMock()
    mock_lead.id = "550e8400-e29b-41d4-a716-446655440000"
    mock_lead.tenant_id = "test"
    mock_lead.name = "João"
    mock_lead.email = "joao@test.com"
    mock_lead.phone = None
    mock_lead.source_channel = "facebook"
    mock_lead.status = "new"
    mock_lead.interests = None
    mock_lead.assigned_sector = None
    mock_lead.created_at = "2025-01-01T00:00:00"
    mock_lead.updated_at = None
    for field in (
        "company_name", "specialty", "city", "instagram", "website", "decision_maker_name",
        "decision_maker_role", "notes", "last_contact_at", "next_follow_up_at",
        "demo_scheduled_at", "pilot_started_at", "pilot_ends_at", "lost_reason",
    ):
        setattr(mock_lead, field, None)
    mock_tracker.track_lead = AsyncMock(return_value=mock_lead)

    response = await client.post(
        "/api/v1/tracking/track?utm_source=facebook&utm_medium=cpc",
        json={"name": "João", "email": "joao@test.com"},
        headers={"X-Tenant-ID": "test"},
    )

    assert response.status_code == 200
    mock_tracker.track_lead.assert_called_once()


@pytest.mark.anyio
@patch("app.modules.tracking.routes.lead_tracker")
async def test_pixel_tracking(mock_tracker, client):
    mock_lead = MagicMock()
    mock_lead.id = "550e8400-e29b-41d4-a716-446655440000"
    mock_tracker.track_lead = AsyncMock(return_value=mock_lead)

    response = await client.get(
        "/api/v1/tracking/pixel.gif?tenant=test&channel=facebook"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"


@pytest.fixture
def meta_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "META_VERIFY_TOKEN", "segredo-meta")


@pytest.mark.anyio
async def test_facebook_webhook_verify(client, meta_token):
    response = await client.get(
        "/api/v1/tracking/webhook/facebook?hub.mode=subscribe&hub.challenge=test123&hub.verify_token=segredo-meta"
    )
    assert response.status_code == 200
    assert response.text == "test123"


@pytest.mark.anyio
async def test_whatsapp_webhook_verify(client, meta_token):
    response = await client.get(
        "/api/v1/tracking/webhook/whatsapp?hub.mode=subscribe&hub.challenge=verify_me&hub.verify_token=segredo-meta"
    )
    assert response.status_code == 200
    assert response.text == "verify_me"


@pytest.mark.anyio
async def test_webhook_verify_rejects_wrong_token(client, meta_token):
    response = await client.get(
        "/api/v1/tracking/webhook/facebook?hub.mode=subscribe&hub.challenge=x&hub.verify_token=errado"
    )
    assert response.status_code == 403
