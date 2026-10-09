"""VSL funnel metrics: unique visitors per step and per campaign."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vsl_event import VSLEvent
from app.schemas.vsl import VSLCampaignRow, VSLFunnelStep, VSLMetrics

FUNNEL_STEPS = (
    "page_view",
    "play",
    "progress_25",
    "progress_50",
    "progress_75",
    "progress_100",
    "cta_shown",
    "cta_click",
)
NO_CAMPAIGN = "(sem campanha)"


def _rate(part: int, total: int) -> float:
    return round(part / total * 100, 1) if total else 0.0


def build_funnel(counts: dict[str, int]) -> list[VSLFunnelStep]:
    """Turn unique-visitor counts per event into ordered funnel steps with conversion rates."""
    views = counts.get("page_view", 0)
    steps = []
    previous = views
    for step in FUNNEL_STEPS:
        visitors = counts.get(step, 0)
        steps.append(
            VSLFunnelStep(
                step=step,
                visitors=visitors,
                rate_from_view=_rate(visitors, views),
                rate_from_previous=_rate(visitors, previous),
            )
        )
        previous = visitors
    return steps


def build_campaign_rows(rows: list[tuple[str | None, str, int]]) -> list[VSLCampaignRow]:
    """Group (utm_campaign, event_type, visitors) rows into one row per campaign."""
    by_campaign: dict[str, dict[str, int]] = defaultdict(dict)
    for campaign, event_type, visitors in rows:
        by_campaign[campaign or NO_CAMPAIGN][event_type] = visitors
    result = [
        VSLCampaignRow(
            utm_campaign=campaign,
            page_views=counts.get("page_view", 0),
            plays=counts.get("play", 0),
            cta_clicks=counts.get("cta_click", 0),
            cta_rate=_rate(counts.get("cta_click", 0), counts.get("page_view", 0)),
        )
        for campaign, counts in by_campaign.items()
    ]
    return sorted(result, key=lambda row: (row.cta_clicks, row.page_views), reverse=True)


async def get_vsl_metrics(db: AsyncSession, tenant_id: str, days: int = 30) -> VSLMetrics:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    visitors = func.count(distinct(VSLEvent.visitor_id))
    filters = (VSLEvent.tenant_id == tenant_id, VSLEvent.created_at >= since)

    totals = await db.execute(
        select(VSLEvent.event_type, visitors).where(*filters).group_by(VSLEvent.event_type)
    )
    per_campaign = await db.execute(
        select(VSLEvent.utm_campaign, VSLEvent.event_type, visitors)
        .where(*filters)
        .group_by(VSLEvent.utm_campaign, VSLEvent.event_type)
    )
    counts = dict(totals.all())
    return VSLMetrics(
        days=days,
        funnel=build_funnel(counts),
        specialist_clicks=counts.get("specialist_click", 0),
        by_campaign=build_campaign_rows([tuple(row) for row in per_campaign.all()]),
    )
