from pydantic import BaseModel


class BotConversaWebhook(BaseModel):
    """Payload received from BotConversa webhook."""
    subscriber_id: str
    name: str | None = None
    phone: str | None = None
    message: str
    channel: str = "whatsapp"


class ChatMessage(BaseModel):
    """Generic chat message for direct API usage."""
    session_id: str
    message: str
    channel: str = "web"
    phone: str | None = None
    name: str | None = None
    metadata: dict | None = None


class ChatResponse(BaseModel):
    """Response from the chatbot."""
    session_id: str
    response: str
    agent_used: str
    lead_id: str | None = None
