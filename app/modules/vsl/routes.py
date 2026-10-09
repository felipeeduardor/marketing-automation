"""VSL sales funnel: public video page, event tracking and funnel metrics.

The page sells VitaClini; its call to action sends the visitor to the VitaClini sign-up page.
"""

import json
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.vsl_event import VSLEvent
from app.modules.vsl.funnel import get_vsl_metrics
from app.schemas.vsl import VSLEventCreate, VSLMetrics
from app.utils.auth import require_admin
from app.utils.multi_tenant import get_tenant_id
from app.utils.plans import PLANS, plan_to_dict

router = APIRouter(prefix="/vsl", tags=["vsl"])
pages_router = APIRouter(prefix="/vsl", tags=["vsl-pages"], include_in_schema=False)

PAGES_DIR = Path(__file__).parent / "pages"
ASSETS = {"vsl.js": "application/javascript", "vsl.css": "text/css"}
YOUTUBE_ID = re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/))([\w-]{11})")
TENANT_PATTERN = r"^[\w-]{1,100}$"


def video_config(url: str) -> dict:
    """Describe how the page should embed the configured video."""
    if not url:
        return {"kind": "none"}
    match = YOUTUBE_ID.search(url)
    if match:
        return {"kind": "youtube", "id": match.group(1)}
    return {"kind": "file", "src": url}


def render_page(name: str, config: dict) -> HTMLResponse:
    html = (PAGES_DIR / name).read_text(encoding="utf-8")
    # Escape "<" so config values can never close the <script> tag they are embedded in.
    payload = json.dumps(config, ensure_ascii=False).replace("<", "\\u003c")
    return HTMLResponse(html.replace("__VSL_CONFIG__", payload))


def page_config(tenant: str) -> dict:
    settings = get_settings()
    return {
        "tenant": tenant,
        "apiBase": "/api/v1",
        "headline": settings.VSL_HEADLINE,
        "ctaDelaySeconds": max(settings.VSL_CTA_DELAY_SECONDS, 0),
        "signupUrl": settings.VSL_SIGNUP_URL,
        "whatsappNumber": re.sub(r"\D", "", settings.VSL_WHATSAPP_NUMBER),
        "video": video_config(settings.VSL_VIDEO_URL),
        "plans": [plan_to_dict(plan) for plan in PLANS.values()],
    }


# --- Public page ---


@pages_router.get("", response_class=HTMLResponse)
async def vsl_page(tenant: str = Query(default="default", pattern=TENANT_PATTERN)):
    return render_page("vsl.html", page_config(tenant))


@pages_router.get("/assets/{name}")
async def vsl_asset(name: str):
    if name not in ASSETS:
        raise HTTPException(status_code=404)
    return Response((PAGES_DIR / name).read_text(encoding="utf-8"), media_type=ASSETS[name])


# --- Public API (called by the page) ---


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT)
async def record_event(
    payload: VSLEventCreate,
    tenant: str = Query(default="default", pattern=TENANT_PATTERN),
    db: AsyncSession = Depends(get_db),
):
    db.add(VSLEvent(tenant_id=tenant, **payload.model_dump()))
    await db.flush()


# --- Internal metrics (dashboard) ---


@router.get("/metrics", response_model=VSLMetrics, dependencies=[Depends(require_admin)])
async def vsl_metrics(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Unique visitors per VSL funnel step and per campaign."""
    return await get_vsl_metrics(db, tenant_id, days)
