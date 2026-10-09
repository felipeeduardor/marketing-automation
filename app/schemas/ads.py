from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


AdChannel = Literal["meta", "instagram", "facebook", "google_display"]
AdAngle = Literal[
    "after_hours",
    "reception_overload",
    "confirmation",
    "scheduling",
    "lead_conversion",
]


class AdGenerationRequest(BaseModel):
    campaign_name: str = Field(min_length=3, max_length=100)
    channel: AdChannel = "meta"
    angle: AdAngle = "after_hours"
    specialty: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    destination_url: str | None = Field(default=None, max_length=1000)
    cta: str = Field(default="Criar conta grátis", min_length=2, max_length=60)


class AdVariant(BaseModel):
    id: str
    angle: str
    objective: str
    headline: str
    primary_text: str
    description: str
    cta: str
    creative_direction: str
    video_script: list[str]
    utm_parameters: dict[str, str]
    tracking_url: str | None = None


class AdGenerationResponse(BaseModel):
    campaign_name: str
    channel: str
    audience: str
    primary_variant: AdVariant
    test_variant: AdVariant
    ab_test_plan: list[str]
    compliance_notes: list[str]