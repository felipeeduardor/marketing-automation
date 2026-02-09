"""Chatbot API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lead import Lead
from app.models.interaction import Interaction
from app.schemas.webhook import BotConversaWebhook, ChatMessage, ChatResponse
from app.modules.chatbot.agent_manager import agent_manager
from app.modules.chatbot.botconversa import botconversa_client
from app.utils.multi_tenant import get_tenant_id
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Process a chat message and return AI response."""
    try:
        response, agent_used = await agent_manager.process_message(
            session_id=message.session_id,
            message=message.message,
        )

        # Save interaction to database
        interaction = Interaction(
            tenant_id=tenant_id,
            channel=message.channel,
            agent_type=agent_used,
            user_message=message.message,
            bot_response=response,
        )
        db.add(interaction)
        await db.flush()

        return ChatResponse(
            session_id=message.session_id,
            response=response,
            agent_used=agent_used,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar mensagem")


@router.post("/webhook/botconversa")
async def botconversa_webhook(
    payload: BotConversaWebhook,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Receive webhook from BotConversa and respond."""
    try:
        session_id = f"bc_{payload.subscriber_id}"

        response, agent_used = await agent_manager.process_message(
            session_id=session_id,
            message=payload.message,
        )

        # Save interaction
        interaction = Interaction(
            tenant_id=tenant_id,
            channel=payload.channel,
            agent_type=agent_used,
            user_message=payload.message,
            bot_response=response,
        )
        db.add(interaction)
        await db.flush()

        # Send response back via BotConversa
        await botconversa_client.send_message(payload.subscriber_id, response)

        return {"status": "ok", "agent_used": agent_used}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar webhook")


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get chat history for a session."""
    history = agent_manager.sessions.get(session_id, [])
    return {"session_id": session_id, "messages": history}


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear chat history for a session."""
    agent_manager.sessions.pop(session_id, None)
    return {"status": "ok", "message": "Sessão limpa"}
