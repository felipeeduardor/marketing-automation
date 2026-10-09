from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_leads: int
    converted_leads: int
    conversion_rate: float
    total_interactions: int
    leads_by_channel: dict[str, int]
    plan: str
    max_leads: int
    max_interactions: int
