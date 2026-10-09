"""API routes for marketing and sales-funnel recommendations."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.marketing.agent import marketing_funnel_agent
from app.utils.multi_tenant import get_tenant_id

router = APIRouter(prefix="/marketing", tags=["marketing"])


@router.get("/insights")
async def marketing_insights(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Return daily funnel priorities, breakdowns and sales-message templates."""
    return await marketing_funnel_agent.get_insights(db, tenant_id)