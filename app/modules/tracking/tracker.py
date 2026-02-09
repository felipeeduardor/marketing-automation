"""UTM and pixel tracking system for lead attribution."""

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.channel import Channel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UTMParams:
    """Parsed UTM parameters from a URL or request."""

    def __init__(
        self,
        utm_source: str | None = None,
        utm_medium: str | None = None,
        utm_campaign: str | None = None,
        utm_term: str | None = None,
        utm_content: str | None = None,
    ):
        self.utm_source = utm_source
        self.utm_medium = utm_medium
        self.utm_campaign = utm_campaign
        self.utm_term = utm_term
        self.utm_content = utm_content

    @classmethod
    def from_dict(cls, params: dict) -> "UTMParams":
        return cls(
            utm_source=params.get("utm_source"),
            utm_medium=params.get("utm_medium"),
            utm_campaign=params.get("utm_campaign"),
            utm_term=params.get("utm_term"),
            utm_content=params.get("utm_content"),
        )

    def detect_channel(self) -> str:
        """Infer the source channel from UTM parameters."""
        source = (self.utm_source or "").lower()
        medium = (self.utm_medium or "").lower()

        channel_map = {
            "facebook": "facebook",
            "fb": "facebook",
            "instagram": "instagram",
            "ig": "instagram",
            "google": "google_ads",
            "googleads": "google_ads",
            "whatsapp": "whatsapp",
            "wpp": "whatsapp",
            "email": "email",
            "linkedin": "linkedin",
            "tiktok": "tiktok",
            "youtube": "youtube",
        }

        for key, channel in channel_map.items():
            if key in source or key in medium:
                return channel

        if medium in ("cpc", "ppc"):
            return "paid_search"
        if medium == "organic":
            return "organic"
        if medium == "referral":
            return "referral"

        return "direct"


class LeadTracker:
    """Tracks lead origins and saves attribution data."""

    async def track_lead(
        self,
        db: AsyncSession,
        tenant_id: str,
        utm: UTMParams,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> Lead:
        """Create or update a lead with tracking data."""
        channel = utm.detect_channel()

        # Check if lead already exists (by email or phone)
        existing_lead = None
        if email:
            result = await db.execute(
                select(Lead).where(Lead.email == email, Lead.tenant_id == tenant_id)
            )
            existing_lead = result.scalar_one_or_none()
        if not existing_lead and phone:
            result = await db.execute(
                select(Lead).where(Lead.phone == phone, Lead.tenant_id == tenant_id)
            )
            existing_lead = result.scalar_one_or_none()

        if existing_lead:
            # Update UTM data if lead already exists but came from a new source
            if utm.utm_source and not existing_lead.utm_source:
                existing_lead.utm_source = utm.utm_source
                existing_lead.utm_medium = utm.utm_medium
                existing_lead.utm_campaign = utm.utm_campaign
                existing_lead.source_channel = channel
            logger.info(f"Updated existing lead {existing_lead.id} with tracking data")
            return existing_lead

        # Create new lead
        lead = Lead(
            tenant_id=tenant_id,
            name=name,
            email=email,
            phone=phone,
            source_channel=channel,
            utm_source=utm.utm_source,
            utm_medium=utm.utm_medium,
            utm_campaign=utm.utm_campaign,
        )
        db.add(lead)
        await db.flush()

        # Increment channel lead count
        await self._increment_channel_count(db, tenant_id, channel)

        logger.info(f"New lead tracked: {lead.id} from {channel}")
        return lead

    async def _increment_channel_count(
        self, db: AsyncSession, tenant_id: str, channel_name: str
    ):
        """Increment the lead count for a channel, creating it if needed."""
        result = await db.execute(
            select(Channel).where(
                Channel.name == channel_name, Channel.tenant_id == tenant_id
            )
        )
        channel = result.scalar_one_or_none()

        if channel:
            channel.total_leads += 1
        else:
            channel = Channel(
                tenant_id=tenant_id,
                name=channel_name,
                total_leads=1,
            )
            db.add(channel)

    async def get_lead_by_id(
        self, db: AsyncSession, tenant_id: str, lead_id: uuid.UUID
    ) -> Lead | None:
        result = await db.execute(
            select(Lead).where(Lead.id == lead_id, Lead.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_leads_by_channel(
        self, db: AsyncSession, tenant_id: str, channel: str
    ) -> list[Lead]:
        result = await db.execute(
            select(Lead).where(
                Lead.source_channel == channel, Lead.tenant_id == tenant_id
            )
        )
        return list(result.scalars().all())

    async def get_channel_stats(
        self, db: AsyncSession, tenant_id: str
    ) -> list[Channel]:
        result = await db.execute(
            select(Channel).where(Channel.tenant_id == tenant_id).order_by(Channel.total_leads.desc())
        )
        return list(result.scalars().all())


# Singleton
lead_tracker = LeadTracker()
