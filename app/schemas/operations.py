from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


ActivityType = Literal["follow_up", "call", "demo", "proposal", "onboarding", "task"]
ActivityStatus = Literal["pending", "completed", "cancelled"]
CampaignStatus = Literal["draft", "active", "paused", "completed"]


class ActivityCreate(BaseModel):
    lead_id: UUID | None = None
    activity_type: ActivityType = "task"
    title: str = Field(min_length=2, max_length=255)
    notes: str | None = None
    due_at: datetime | None = None


class ActivityUpdate(BaseModel):
    activity_type: ActivityType | None = None
    title: str | None = Field(default=None, min_length=2, max_length=255)
    notes: str | None = None
    status: ActivityStatus | None = None
    due_at: datetime | None = None


class ActivityResponse(BaseModel):
    id: UUID
    tenant_id: str
    lead_id: UUID | None
    activity_type: str
    title: str
    notes: str | None
    status: str
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CampaignCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    channel: str = Field(min_length=2, max_length=100)
    objective: str = Field(default="Gerar demonstrações", min_length=2, max_length=255)
    status: CampaignStatus = "draft"
    utm_source: str | None = Field(default=None, max_length=100)
    utm_medium: str | None = Field(default=None, max_length=100)
    utm_campaign: str | None = Field(default=None, max_length=255)
    destination_url: str | None = Field(default=None, max_length=1000)
    daily_budget: float | None = Field(default=None, ge=0)
    notes: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=255)
    channel: str | None = Field(default=None, min_length=2, max_length=100)
    objective: str | None = Field(default=None, min_length=2, max_length=255)
    status: CampaignStatus | None = None
    utm_source: str | None = Field(default=None, max_length=100)
    utm_medium: str | None = Field(default=None, max_length=100)
    utm_campaign: str | None = Field(default=None, max_length=255)
    destination_url: str | None = Field(default=None, max_length=1000)
    daily_budget: float | None = Field(default=None, ge=0)
    notes: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class CampaignResponse(BaseModel):
    id: UUID
    tenant_id: str
    name: str
    channel: str
    objective: str
    status: str
    utm_source: str | None
    utm_medium: str | None
    utm_campaign: str | None
    destination_url: str | None
    daily_budget: float | None
    notes: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class OperationsOverview(BaseModel):
    pending_activities: int
    overdue_activities: int
    active_campaigns: int
    draft_campaigns: int