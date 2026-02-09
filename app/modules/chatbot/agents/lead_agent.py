"""Lead Agent: identifies the origin of the lead and collects basic info."""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """Você é um agente especializado em identificar a origem de leads.
Sua função é:
1. Identificar de qual canal o lead veio (WhatsApp, Instagram, Facebook, Google Ads, site, indicação)
2. Coletar informações básicas: nome, e-mail e telefone
3. Ser cordial e profissional

Responda SEMPRE em português brasileiro.
Se o lead não fornecer informações, peça educadamente.
Retorne as informações coletadas em formato estruturado ao final.

Contexto da conversa até agora:
{chat_history}
"""


class LeadAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{message}"),
        ])
        self.chain = self.prompt | self.llm

    async def process(self, message: str, chat_history: str = "") -> str:
        logger.info(f"LeadAgent processing: {message[:50]}...")
        response = await self.chain.ainvoke({
            "message": message,
            "chat_history": chat_history,
        })
        return response.content
