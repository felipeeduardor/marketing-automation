from typing import Literal

from pydantic import BaseModel, Field


# Ordered funnel steps. Each step is counted once per visitor.
# The funnel ends at cta_click: the visitor leaves for the VitaClini sign-up page.
VSLEventType = Literal[
    "page_view",
    "play",
    "progress_25",
    "progress_50",
    "progress_75",
    "progress_100",
    "cta_shown",
    "cta_click",
    "specialist_click",
]


class VSLEventCreate(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=64)
    event_type: VSLEventType
    video_seconds: int | None = Field(default=None, ge=0, le=86400)
    utm_source: str | None = Field(default=None, max_length=255)
    utm_medium: str | None = Field(default=None, max_length=255)
    utm_campaign: str | None = Field(default=None, max_length=255)
    utm_content: str | None = Field(default=None, max_length=255)


class VSLFunnelStep(BaseModel):
    step: str
    visitors: int
    rate_from_view: float
    rate_from_previous: float


class VSLCampaignRow(BaseModel):
    utm_campaign: str
    page_views: int
    plays: int
    cta_clicks: int
    cta_rate: float


class VSLMetrics(BaseModel):
    days: int
    funnel: list[VSLFunnelStep]
    specialist_clicks: int
    by_campaign: list[VSLCampaignRow]
