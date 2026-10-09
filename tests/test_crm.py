"""Unit tests for the clinic SaaS CRM rules."""

from app.modules.crm.routes import PIPELINE_STAGES
from app.modules.ads.agent import ad_agent
from app.modules.marketing.agent import MarketingFunnelAgent
from app.schemas.ads import AdGenerationRequest
from app.schemas.operations import ActivityCreate, CampaignCreate
from app.schemas.lead import ClinicLeadCreate, LeadStageUpdate


def test_pipeline_contains_expected_sales_stages():
    assert PIPELINE_STAGES == (
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
    )


def test_clinic_lead_defaults_to_new_outbound_lead():
    lead = ClinicLeadCreate(company_name="Clínica Exemplo")
    assert lead.status == "new"
    assert lead.source_channel == "outbound"


def test_stage_update_accepts_pilot_active():
    update = LeadStageUpdate(status="pilot_active")
    assert update.status == "pilot_active"


def test_marketing_agent_prioritizes_due_follow_ups():
    recommendations = MarketingFunnelAgent._build_recommendations(
        funnel={stage: 0 for stage in PIPELINE_STAGES},
        follow_ups_due=3,
        leads_without_follow_up=0,
    )
    assert recommendations[0]["priority"] == "alta"
    assert "follow-up" in recommendations[0]["title"].lower()


def test_marketing_agent_detects_demo_bottleneck():
    funnel = {stage: 0 for stage in PIPELINE_STAGES}
    funnel["responded"] = 3
    recommendations = MarketingFunnelAgent._build_recommendations(
        funnel=funnel,
        follow_ups_due=0,
        leads_without_follow_up=0,
    )
    assert any("demonstrações" in item["title"].lower() for item in recommendations)


def test_ad_agent_generates_two_trackable_variants():
    result = ad_agent.generate(
        AdGenerationRequest(
            campaign_name="clinicas-whatsapp",
            angle="after_hours",
            destination_url="https://example.com/demo",
        )
    )
    assert result.primary_variant.id == "AD-A"
    assert result.test_variant.id == "AD-B"
    assert result.primary_variant.tracking_url is not None
    assert "utm_campaign=clinicas-whatsapp" in result.primary_variant.tracking_url


def test_sales_activity_defaults_to_pending():
    activity = ActivityCreate(title="Fazer follow-up")
    assert activity.activity_type == "task"


def test_campaign_defaults_to_draft_and_demo_goal():
    campaign = CampaignCreate(name="Campanha de clínicas", channel="meta")
    assert campaign.status == "draft"
    assert campaign.objective == "Gerar demonstrações"
