"""CRM API endpoints for the clinic SaaS sales pipeline."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lead import Lead
from app.schemas.lead import CRMOverview, ClinicLeadCreate, LeadResponse, LeadStageUpdate, LeadUpdate
from app.utils.multi_tenant import get_tenant_id

router = APIRouter(prefix="/crm", tags=["crm"])

PIPELINE_STAGES = (
    "new",
    "contacted",
    "responded",
    "decision_maker_identified",
    "demo_scheduled",
    "demo_completed",
    "pilot_proposed",
    "pilot_active",
    "customer",
    "lost",
)


async def get_lead_or_404(db: AsyncSession, tenant_id: str, lead_id: UUID) -> Lead:
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.tenant_id == tenant_id)
    )
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead


@router.get("/pipeline", response_model=list[str])
async def get_pipeline():
    """Return the ordered sales stages used by the clinic CRM."""
    return list(PIPELINE_STAGES)


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_clinic_lead(
    payload: ClinicLeadCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a manually prospectable clinic lead."""
    lead = Lead(tenant_id=tenant_id, **payload.model_dump())
    db.add(lead)
    await db.flush()
    await db.refresh(lead)
    return lead


@router.get("/leads", response_model=list[LeadResponse])
async def list_crm_leads(
    stage: str | None = Query(default=None),
    follow_up_due: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """List clinic leads, optionally by stage or follow-ups due now."""
    query = select(Lead).where(Lead.tenant_id == tenant_id)
    if stage:
        query = query.where(Lead.status == stage)
    if follow_up_due:
        query = query.where(
            Lead.next_follow_up_at.is_not(None),
            Lead.next_follow_up_at <= datetime.now(timezone.utc),
            Lead.status.notin_(("customer", "lost")),
        )
    query = query.order_by(Lead.next_follow_up_at.asc().nullslast(), Lead.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_crm_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    return await get_lead_or_404(db, tenant_id, lead_id)


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_crm_lead(
    lead_id: UUID,
    payload: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Update clinic data, notes, demo details and follow-up dates."""
    lead = await get_lead_or_404(db, tenant_id, lead_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    await db.flush()
    await db.refresh(lead)
    return lead


@router.post("/leads/{lead_id}/stage", response_model=LeadResponse)
async def move_lead_stage(
    lead_id: UUID,
    payload: LeadStageUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Move a lead through the clinic sales pipeline."""
    lead = await get_lead_or_404(db, tenant_id, lead_id)
    lead.status = payload.status
    if payload.status in {"contacted", "responded"}:
        lead.last_contact_at = datetime.now(timezone.utc)
    if payload.status == "pilot_active" and not lead.pilot_started_at:
        lead.pilot_started_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(lead)
    return lead


@router.get("/overview", response_model=CRMOverview)
async def crm_overview(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Return dashboard metrics for clinic SaaS acquisition."""
    now = datetime.now(timezone.utc)
    counts_result = await db.execute(
        select(Lead.status, func.count(Lead.id))
        .where(Lead.tenant_id == tenant_id)
        .group_by(Lead.status)
    )
    funnel = {stage: 0 for stage in PIPELINE_STAGES}
    funnel.update({stage: count for stage, count in counts_result.all()})

    follow_ups_due = await db.scalar(
        select(func.count(Lead.id)).where(
            Lead.tenant_id == tenant_id,
            Lead.next_follow_up_at.is_not(None),
            Lead.next_follow_up_at <= now,
            Lead.status.notin_(("customer", "lost")),
        )
    )
    total_leads = sum(funnel.values())
    return CRMOverview(
        total_leads=total_leads,
        contacted_leads=sum(funnel[stage] for stage in ("contacted", "responded", "decision_maker_identified")),
        demos_scheduled=funnel["demo_scheduled"],
        active_pilots=funnel["pilot_active"],
        customers=funnel["customer"],
        follow_ups_due=follow_ups_due or 0,
        funnel=funnel,
    )