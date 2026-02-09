from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CustomerCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    lead_id: UUID | None = None
    source_channel: str | None = None


class CustomerResponse(BaseModel):
    id: UUID
    tenant_id: str
    name: str
    email: str | None
    phone: str | None
    total_spent: float
    source_channel: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
