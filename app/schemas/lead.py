from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Literal


LeadStatus = Literal[
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
]


class LeadCreate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    source_channel: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None


class ClinicLeadCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    specialty: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    instagram: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    decision_maker_name: str | None = Field(default=None, max_length=255)
    decision_maker_role: str | None = Field(default=None, max_length=100)
    source_channel: str = Field(default="outbound", max_length=100)
    status: LeadStatus = "new"
    notes: str | None = None
    next_follow_up_at: datetime | None = None
    demo_scheduled_at: datetime | None = None


class LeadResponse(BaseModel):
    id: UUID
    tenant_id: str
    name: str | None
    email: str | None
    phone: str | None
    source_channel: str | None
    status: str
    interests: str | None
    assigned_sector: str | None
    company_name: str | None = None
    specialty: str | None = None
    city: str | None = None
    instagram: str | None = None
    website: str | None = None
    decision_maker_name: str | None = None
    decision_maker_role: str | None = None
    notes: str | None = None
    last_contact_at: datetime | None = None
    next_follow_up_at: datetime | None = None
    demo_scheduled_at: datetime | None = None
    pilot_started_at: datetime | None = None
    pilot_ends_at: datetime | None = None
    lost_reason: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company_name: str | None = Field(default=None, min_length=2, max_length=255)
    specialty: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    instagram: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    decision_maker_name: str | None = Field(default=None, max_length=255)
    decision_maker_role: str | None = Field(default=None, max_length=100)
    status: LeadStatus | None = None
    interests: str | None = None
    assigned_sector: str | None = None
    notes: str | None = None
    last_contact_at: datetime | None = None
    next_follow_up_at: datetime | None = None
    demo_scheduled_at: datetime | None = None
    pilot_started_at: datetime | None = None
    pilot_ends_at: datetime | None = None
    lost_reason: str | None = None


class LeadStageUpdate(BaseModel):
    status: LeadStatus


class CRMOverview(BaseModel):
    total_leads: int
    contacted_leads: int
    demos_scheduled: int
    active_pilots: int
    customers: int
    follow_ups_due: int
    funnel: dict[str, int]
