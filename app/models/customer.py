import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True, default="default")
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)
    source_channel: Mapped[str | None] = mapped_column(String(100))
    crm_id: Mapped[str | None] = mapped_column(String(255))  # ID in external CRM
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
