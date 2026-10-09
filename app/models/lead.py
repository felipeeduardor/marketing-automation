import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(100), index=True, default="default")
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    source_channel: Mapped[str | None] = mapped_column(String(100))  # whatsapp, instagram, facebook, google_ads
    utm_source: Mapped[str | None] = mapped_column(String(255))
    utm_medium: Mapped[str | None] = mapped_column(String(255))
    utm_campaign: Mapped[str | None] = mapped_column(String(255))
    interests: Mapped[str | None] = mapped_column(Text)  # JSON string of interests
    status: Mapped[str] = mapped_column(String(50), default="new")  # new, qualified, converted, lost
    assigned_sector: Mapped[str | None] = mapped_column(String(100))

    # CRM fields used to sell the clinic WhatsApp assistant.
    # They are nullable so leads received by pixels/webhooks continue to work.
    company_name: Mapped[str | None] = mapped_column(String(255), index=True)
    specialty: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(255))
    instagram: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(500))
    decision_maker_name: Mapped[str | None] = mapped_column(String(255))
    decision_maker_role: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    demo_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    pilot_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pilot_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lost_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
