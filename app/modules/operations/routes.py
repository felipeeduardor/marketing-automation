"""Operational routes for sales activities and marketing campaigns."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.activity import Activity
from app.models.campaign import Campaign
from app.schemas.operations import (
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    CampaignCreate,
    CampaignResponse,
    CampaignUpdate,
    OperationsOverview,
)
from app.utils.multi_tenant import get_tenant_id

router = APIRouter(prefix="/operations", tags=["operations"])


async def get_activity_or_404(db: AsyncSession, tenant_id: str, activity_id: UUID) -> Activity:
    result = await db.execute(
        select(Activity).where(Activity.id == activity_id, Activity.tenant_id == tenant_id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Actividade não encontrada")
    return activity


async def get_campaign_or_404(db: AsyncSession, tenant_id: str, campaign_id: UUID) -> Campaign:
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.tenant_id == tenant_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return campaign


@router.post("/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    payload: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    activity = Activity(tenant_id=tenant_id, **payload.model_dump())
    db.add(activity)
    await db.flush()
    await db.refresh(activity)
    return activity


@router.get("/activities", response_model=list[ActivityResponse])
async def list_activities(
    status_filter: str | None = Query(default=None, alias="status"),
    lead_id: UUID | None = Query(default=None),
    due_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    query = select(Activity).where(Activity.tenant_id == tenant_id)
    if status_filter:
        query = query.where(Activity.status == status_filter)
    if lead_id:
        query = query.where(Activity.lead_id == lead_id)
    if due_only:
        query = query.where(
            Activity.status == "pending",
            Activity.due_at.is_not(None),
            Activity.due_at <= datetime.now(timezone.utc),
        )
    query = query.order_by(Activity.due_at.asc().nullslast(), Activity.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.patch("/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: UUID,
    payload: ActivityUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    activity = await get_activity_or_404(db, tenant_id, activity_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(activity, field, value)
    if data.get("status") == "completed" and not activity.completed_at:
        activity.completed_at = datetime.now(timezone.utc)
    if data.get("status") in {"pending", "cancelled"}:
        activity.completed_at = None
    await db.flush()
    await db.refresh(activity)
    return activity


@router.post("/activities/{activity_id}/complete", response_model=ActivityResponse)
async def complete_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    activity = await get_activity_or_404(db, tenant_id, activity_id)
    activity.status = "completed"
    activity.completed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(activity)
    return activity


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    campaign = Campaign(tenant_id=tenant_id, **payload.model_dump())
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    return campaign


@router.get("/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    query = select(Campaign).where(Campaign.tenant_id == tenant_id)
    if status_filter:
        query = query.where(Campaign.status == status_filter)
    result = await db.execute(query.order_by(Campaign.created_at.desc()))
    return list(result.scalars().all())


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    payload: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    campaign = await get_campaign_or_404(db, tenant_id, campaign_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    await db.flush()
    await db.refresh(campaign)
    return campaign


@router.get("/overview", response_model=OperationsOverview)
async def operations_overview(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    now = datetime.now(timezone.utc)
    pending = await db.scalar(
        select(func.count(Activity.id)).where(
            Activity.tenant_id == tenant_id, Activity.status == "pending"
        )
    )
    overdue = await db.scalar(
        select(func.count(Activity.id)).where(
            Activity.tenant_id == tenant_id,
            Activity.status == "pending",
            Activity.due_at.is_not(None),
            Activity.due_at <= now,
        )
    )
    active_campaigns = await db.scalar(
        select(func.count(Campaign.id)).where(
            Campaign.tenant_id == tenant_id, Campaign.status == "active"
        )
    )
    draft_campaigns = await db.scalar(
        select(func.count(Campaign.id)).where(
            Campaign.tenant_id == tenant_id, Campaign.status == "draft"
        )
    )
    return OperationsOverview(
        pending_activities=pending or 0,
        overdue_activities=overdue or 0,
        active_campaigns=active_campaigns or 0,
        draft_campaigns=draft_campaigns or 0,
    )