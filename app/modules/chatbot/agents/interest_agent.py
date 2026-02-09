"""Interest Agent: discovers what the lead is interested in."""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """Você é um agente especializado em descobrir os interesses do cliente.
Sua função é:
1. Entender qual produto ou serviço o lead está procurando
2. Identificar o nível de urgência (baixa, média, alta)
3. Entender o orçamento disponível, se possível
4. Mapear as necessidades específicas do lead

Seja consultivo, faça perguntas abertas e demonstre interesse genuíno.
Responda SEMPRE em português brasileiro.

Contexto da conversa até agora:
{chat_history}
"""


class InterestAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.5,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{message}"),
        ])
        self.chain = self.prompt | self.llm

    async def process(self, message: str, chat_history: str = "") -> str:
        logger.info(f"InterestAgent processing: {message[:50]}...")
        response = await self.chain.ainvoke({
            "message": message,
            "chat_history": chat_history,
        })
        return response.content
