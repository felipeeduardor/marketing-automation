"""Tests for the VSL sales funnel."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.modules.vsl.funnel import FUNNEL_STEPS, NO_CAMPAIGN, build_campaign_rows, build_funnel
from app.modules.vsl.routes import pages_router, video_config
from app.schemas.vsl import VSLEventCreate
from app.utils.plans import PLANS, plan_to_dict


def test_funnel_rates_relative_to_views_and_previous_step():
    steps = build_funnel({"page_view": 200, "play": 100, "progress_25": 50, "cta_click": 4})
    by_step = {step.step: step for step in steps}

    assert [step.step for step in steps] == list(FUNNEL_STEPS)
    assert by_step["play"].rate_from_view == 50.0
    assert by_step["progress_25"].rate_from_previous == 50.0
    assert by_step["progress_50"].visitors == 0
    assert by_step["cta_click"].rate_from_view == 2.0


def test_funnel_without_views_has_zero_rates():
    steps = build_funnel({})
    assert all(step.visitors == 0 and step.rate_from_view == 0.0 for step in steps)


def test_campaign_rows_group_events_and_sort_by_signup_clicks():
    rows = build_campaign_rows(
        [
            ("dor_whatsapp", "page_view", 100),
            ("dor_whatsapp", "cta_click", 1),
            ("recepcao", "page_view", 50),
            ("recepcao", "cta_click", 3),
            (None, "page_view", 10),
        ]
    )
    assert [row.utm_campaign for row in rows] == ["recepcao", "dor_whatsapp", NO_CAMPAIGN]
    assert rows[0].cta_rate == 6.0


def test_video_config_detects_youtube_and_files():
    assert video_config("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == {"kind": "youtube", "id": "dQw4w9WgXcQ"}
    assert video_config("https://youtu.be/dQw4w9WgXcQ?t=3") == {"kind": "youtube", "id": "dQw4w9WgXcQ"}
    assert video_config("https://cdn.exemplo.com/vsl.mp4") == {"kind": "file", "src": "https://cdn.exemplo.com/vsl.mp4"}
    assert video_config("") == {"kind": "none"}


def test_plans_match_vitaclini_prices():
    assert [plan_to_dict(plan)["price_display"] for plan in PLANS.values()] == ["R$ 0", "R$ 97", "R$ 247"]


def test_specialist_click_is_a_valid_event():
    assert VSLEventCreate(visitor_id="visitor-123", event_type="specialist_click").event_type == "specialist_click"


def test_event_rejects_unknown_type():
    with pytest.raises(ValidationError):
        VSLEventCreate(visitor_id="visitor-123", event_type="hacked")


@pytest.fixture
async def pages_client():
    app = FastAPI()
    app.include_router(pages_router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_page_renders_config(pages_client):
    response = await pages_client.get("/vsl", params={"tenant": "clinica-1"})
    assert response.status_code == 200
    assert "__VSL_CONFIG__" not in response.text
    assert '"tenant": "clinica-1"' in response.text
    assert '"signupUrl": "https://vitaclini.com.br/login?aba=cadastro"' in response.text


@pytest.mark.anyio
async def test_pages_reject_invalid_tenant(pages_client):
    response = await pages_client.get("/vsl", params={"tenant": "</script><script>alert(1)"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_assets_are_whitelisted(pages_client):
    assert (await pages_client.get("/vsl/assets/vsl.js")).status_code == 200
    assert (await pages_client.get("/vsl/assets/vsl.html")).status_code == 404
