from pydantic import BaseModel, Field


class PlanResponse(BaseModel):
    id: str
    name: str
    price_monthly: int
    price_display: str
    features: list[str]


class CheckoutRequest(BaseModel):
    plan_id: str = Field(pattern="^(pro|enterprise)$")


class CheckoutResponse(BaseModel):
    checkout_url: str


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_end: str | None
