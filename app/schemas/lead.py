from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class LeadCreate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    source_channel: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None


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
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    status: str | None = None
    interests: str | None = None
    assigned_sector: str | None = None
