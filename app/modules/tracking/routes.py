"""Tracking API endpoints for UTM, pixel, and channel webhooks."""

import base64
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.lead import LeadCreate, LeadResponse
from app.modules.tracking.tracker import UTMParams, lead_tracker
from app.modules.tracking.channels import (
    FacebookWebhookPayload,
    InstagramWebhookPayload,
    WhatsAppWebhookPayload,
    GoogleAdsWebhookPayload,
    pixel_tracker,
)
from app.config import get_settings
from app.utils.auth import require_admin
from app.utils.multi_tenant import get_tenant_id
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tracking", tags=["tracking"])

# 1x1 transparent GIF
PIXEL_GIF = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)


def verify_meta_subscription(mode: str | None, token: str | None) -> bool:
    """Meta webhook handshake: accept only our own verify token."""
    expected = get_settings().META_VERIFY_TOKEN
    return mode == "subscribe" and bool(expected) and token is not None and secrets.compare_digest(token, expected)


# --- UTM Tracking ---


@router.post("/track", response_model=LeadResponse)
async def track_lead(
    lead_data: LeadCreate,
    utm_source: str | None = Query(None),
    utm_medium: str | None = Query(None),
    utm_campaign: str | None = Query(None),
    utm_term: str | None = Query(None),
    utm_content: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Track a new lead with UTM parameters."""
    utm = UTMParams(
        utm_source=utm_source or lead_data.utm_source,
        utm_medium=utm_medium or lead_data.utm_medium,
        utm_campaign=utm_campaign or lead_data.utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
    )

    lead = await lead_tracker.track_lead(
        db=db,
        tenant_id=tenant_id,
        utm=utm,
        name=lead_data.name,
        email=lead_data.email,
        phone=lead_data.phone,
    )
    return lead


# --- Pixel Tracking ---


@router.get("/pixel.gif")
async def tracking_pixel(
    request: Request,
    tenant: str = Query(default="default"),
    channel: str = Query(default="direct"),
    db: AsyncSession = Depends(get_db),
):
    """Serve a 1x1 tracking pixel and log the visit."""
    # Extract UTM params from the full URL
    params = dict(request.query_params)
    utm = UTMParams.from_dict(params)
    if not utm.utm_source:
        utm.utm_source = channel

    await lead_tracker.track_lead(db=db, tenant_id=tenant, utm=utm)

    logger.info(f"Pixel hit: tenant={tenant}, channel={channel}")
    return Response(
        content=PIXEL_GIF,
        media_type="image/gif",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@router.get("/pixel/snippet", dependencies=[Depends(require_admin)])
async def get_pixel_snippet(
    request: Request,
    channel: str = Query(..., description="facebook, google_ads, or server"),
    pixel_id: str = Query(default="", description="Pixel/Tag ID"),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get the tracking pixel/tag snippet for a channel."""
    if channel == "facebook":
        if not pixel_id:
            raise HTTPException(400, "pixel_id is required for Facebook")
        return {"snippet": pixel_tracker.facebook_pixel(pixel_id)}
    elif channel == "google_ads":
        if not pixel_id:
            raise HTTPException(400, "pixel_id (conversion_id) is required for Google Ads")
        return {"snippet": pixel_tracker.google_ads_tag(pixel_id)}
    elif channel == "server":
        url = pixel_tracker.server_pixel_url(
            base_url=str(request.base_url).rstrip("/"),
            tenant_id=tenant_id,
            channel="server",
        )
        return {"snippet": f'<img src="{url}" height="1" width="1" style="display:none" />'}
    else:
        raise HTTPException(400, f"Unsupported channel: {channel}")


# --- Channel Webhooks ---


@router.post("/webhook/facebook")
async def facebook_webhook(
    payload: FacebookWebhookPayload,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Receive lead data from Facebook Lead Ads."""
    lead_data = payload.extract_lead_data()
    if not lead_data:
        return {"status": "ignored", "reason": "no lead data found"}

    utm = UTMParams(utm_source="facebook", utm_medium="paid_social")
    lead = await lead_tracker.track_lead(
        db=db, tenant_id=tenant_id, utm=utm
    )

    logger.info(f"Facebook lead received: {lead.id}")
    return {"status": "ok", "lead_id": str(lead.id)}


@router.get("/webhook/facebook")
async def facebook_webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Facebook webhook verification endpoint."""
    if verify_meta_subscription(hub_mode, hub_verify_token) and hub_challenge:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(403, "Verification failed")


@router.post("/webhook/instagram")
async def instagram_webhook(
    payload: InstagramWebhookPayload,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Receive lead data from Instagram."""
    lead_data = payload.extract_lead_data()
    if not lead_data:
        return {"status": "ignored", "reason": "no lead data found"}

    utm = UTMParams(utm_source="instagram", utm_medium="social")
    lead = await lead_tracker.track_lead(
        db=db, tenant_id=tenant_id, utm=utm,
        name=lead_data.get("sender_id"),
    )

    logger.info(f"Instagram lead received: {lead.id}")
    return {"status": "ok", "lead_id": str(lead.id)}


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    payload: WhatsAppWebhookPayload,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Receive lead data from WhatsApp Business API."""
    lead_data = payload.extract_lead_data()
    if not lead_data:
        return {"status": "ignored", "reason": "no lead data found"}

    utm = UTMParams(utm_source="whatsapp", utm_medium="messaging")
    lead = await lead_tracker.track_lead(
        db=db, tenant_id=tenant_id, utm=utm,
        name=lead_data.get("name"),
        phone=lead_data.get("phone"),
    )

    logger.info(f"WhatsApp lead received: {lead.id}")
    return {"status": "ok", "lead_id": str(lead.id)}


@router.get("/webhook/whatsapp")
async def whatsapp_webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """WhatsApp Cloud API webhook verification."""
    if verify_meta_subscription(hub_mode, hub_verify_token) and hub_challenge:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(403, "Verification failed")


@router.post("/webhook/google-ads")
async def google_ads_webhook(
    payload: GoogleAdsWebhookPayload,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Receive lead data from Google Ads lead form extensions."""
    lead_data = payload.extract_lead_data()

    utm = UTMParams(
        utm_source="google",
        utm_medium="cpc",
        utm_campaign=lead_data.get("campaign_id"),
    )
    lead = await lead_tracker.track_lead(
        db=db, tenant_id=tenant_id, utm=utm,
        name=lead_data.get("name"),
        email=lead_data.get("email"),
        phone=lead_data.get("phone"),
    )

    logger.info(f"Google Ads lead received: {lead.id}")
    return {"status": "ok", "lead_id": str(lead.id)}


# --- Lead Queries ---


@router.get("/leads", response_model=list[LeadResponse], dependencies=[Depends(require_admin)])
async def list_leads(
    channel: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """List leads, optionally filtered by channel or status."""
    from sqlalchemy import select
    from app.models.lead import Lead

    query = select(Lead).where(Lead.tenant_id == tenant_id)
    if channel:
        query = query.where(Lead.source_channel == channel)
    if status:
        query = query.where(Lead.status == status)
    query = query.order_by(Lead.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/leads/{lead_id}", response_model=LeadResponse, dependencies=[Depends(require_admin)])
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get a specific lead by ID."""
    lead = await lead_tracker.get_lead_by_id(db, tenant_id, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


@router.get("/channels/stats", dependencies=[Depends(require_admin)])
async def channel_stats(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get lead count stats per channel."""
    channels = await lead_tracker.get_channel_stats(db, tenant_id)
    return [
        {
            "name": ch.name,
            "total_leads": ch.total_leads,
            "active": ch.active,
        }
        for ch in channels
    ]
