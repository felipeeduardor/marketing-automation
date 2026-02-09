"""Channel-specific integrations for Facebook, Instagram, WhatsApp, Google Ads."""

from pydantic import BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


# --- Webhook Payloads ---

class FacebookWebhookPayload(BaseModel):
    """Facebook Lead Ads / Conversions API webhook."""
    entry: list[dict] | None = None
    object: str = "page"

    def extract_lead_data(self) -> dict | None:
        """Extract lead info from Facebook webhook payload."""
        if not self.entry:
            return None
        for entry in self.entry:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if "leadgen_id" in value:
                    return {
                        "source": "facebook",
                        "leadgen_id": value.get("leadgen_id"),
                        "page_id": value.get("page_id"),
                        "form_id": value.get("form_id"),
                        "created_time": value.get("created_time"),
                    }
        return None


class InstagramWebhookPayload(BaseModel):
    """Instagram messaging / lead webhook."""
    entry: list[dict] | None = None
    object: str = "instagram"

    def extract_lead_data(self) -> dict | None:
        if not self.entry:
            return None
        for entry in self.entry:
            for message in entry.get("messaging", []):
                sender = message.get("sender", {})
                return {
                    "source": "instagram",
                    "sender_id": sender.get("id"),
                    "message": message.get("message", {}).get("text"),
                    "timestamp": message.get("timestamp"),
                }
        return None


class WhatsAppWebhookPayload(BaseModel):
    """WhatsApp Business API / Cloud API webhook."""
    entry: list[dict] | None = None
    object: str = "whatsapp_business_account"

    def extract_lead_data(self) -> dict | None:
        if not self.entry:
            return None
        for entry in self.entry:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                contacts = value.get("contacts", [])
                messages = value.get("messages", [])
                if contacts and messages:
                    contact = contacts[0]
                    msg = messages[0]
                    return {
                        "source": "whatsapp",
                        "phone": contact.get("wa_id"),
                        "name": contact.get("profile", {}).get("name"),
                        "message": msg.get("text", {}).get("body"),
                        "timestamp": msg.get("timestamp"),
                    }
        return None


class GoogleAdsWebhookPayload(BaseModel):
    """Google Ads lead form extension / conversion data."""
    lead_id: str | None = None
    campaign_id: str | None = None
    form_id: str | None = None
    user_column_data: list[dict] | None = None
    gcl_id: str | None = None

    def extract_lead_data(self) -> dict:
        data = {
            "source": "google_ads",
            "lead_id": self.lead_id,
            "campaign_id": self.campaign_id,
            "gcl_id": self.gcl_id,
        }
        if self.user_column_data:
            for col in self.user_column_data:
                key = col.get("column_id", "").lower()
                value = col.get("string_value", "")
                if "email" in key:
                    data["email"] = value
                elif "name" in key or "nome" in key:
                    data["name"] = value
                elif "phone" in key or "telefone" in key:
                    data["phone"] = value
        return data


# --- Pixel Tracking ---

class PixelTracker:
    """Generates tracking pixel snippets for each channel."""

    @staticmethod
    def facebook_pixel(pixel_id: str) -> str:
        """Return Facebook Pixel JS snippet."""
        return f"""<!-- Facebook Pixel -->
<script>
!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '{pixel_id}');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id={pixel_id}&ev=PageView&noscript=1"/></noscript>
<!-- End Facebook Pixel -->"""

    @staticmethod
    def google_ads_tag(conversion_id: str, conversion_label: str = "") -> str:
        """Return Google Ads conversion tracking snippet."""
        return f"""<!-- Google Ads Tag -->
<script async src="https://www.googletagmanager.com/gtag/js?id={conversion_id}"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{conversion_id}');
</script>
<!-- End Google Ads Tag -->"""

    @staticmethod
    def server_pixel_url(base_url: str, tenant_id: str, channel: str) -> str:
        """Generate a 1x1 transparent pixel URL for server-side tracking."""
        return f"{base_url}/api/v1/tracking/pixel.gif?tenant={tenant_id}&channel={channel}"


pixel_tracker = PixelTracker()
