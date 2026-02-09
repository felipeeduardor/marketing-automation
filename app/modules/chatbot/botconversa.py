"""BotConversa integration: send/receive messages via BotConversa API."""

import httpx

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

BOTCONVERSA_API_URL = "https://backend.botconversa.com.br/api/v1"


class BotConversaClient:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.BOTCONVERSA_API_KEY

    async def send_message(self, subscriber_id: str, message: str) -> dict:
        """Send a text message to a subscriber via BotConversa."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BOTCONVERSA_API_URL}/subscribers/{subscriber_id}/send-message/",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"type": "text", "text": message},
                timeout=30,
            )
            response.raise_for_status()
            logger.info(f"Message sent to subscriber {subscriber_id}")
            return response.json()

    async def send_button_message(
        self, subscriber_id: str, text: str, buttons: list[dict]
    ) -> dict:
        """Send a button message (useful for checkout links)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BOTCONVERSA_API_URL}/subscribers/{subscriber_id}/send-message/",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "type": "buttons",
                    "text": text,
                    "buttons": buttons,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

    async def get_subscriber(self, subscriber_id: str) -> dict:
        """Get subscriber info from BotConversa."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BOTCONVERSA_API_URL}/subscribers/{subscriber_id}/",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()


botconversa_client = BotConversaClient()
