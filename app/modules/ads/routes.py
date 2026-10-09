"""API endpoint for generating clinic SaaS ad plans."""

from fastapi import APIRouter

from app.modules.ads.agent import ad_agent
from app.schemas.ads import AdGenerationRequest, AdGenerationResponse

router = APIRouter(prefix="/ads", tags=["ads"])


@router.post("/generate", response_model=AdGenerationResponse)
async def generate_ads(payload: AdGenerationRequest):
    """Generate a primary ad, an A/B test variant, creative direction and UTMs."""
    return ad_agent.generate(payload)