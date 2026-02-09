"""FAQ Agent: answers questions using RAG (knowledge base)."""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.modules.chatbot.knowledge_base import knowledge_base
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """Você é um agente especializado em responder dúvidas frequentes.
Use APENAS as informações da base de conhecimento fornecida para responder.
Se não souber a resposta, diga que vai encaminhar para um atendente humano.

Base de conhecimento relevante:
{context}

Responda SEMPRE em português brasileiro, de forma clara e objetiva.

Contexto da conversa até agora:
{chat_history}
"""


class FAQAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.2,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{message}"),
        ])
        self.chain = self.prompt | self.llm

    async def process(self, message: str, chat_history: str = "") -> str:
        logger.info(f"FAQAgent processing: {message[:50]}...")

        # Search knowledge base for relevant context
        docs = await knowledge_base.search(message, k=3)
        context = "\n".join([doc.page_content for doc in docs]) if docs else "Nenhuma informação encontrada na base de conhecimento."

        response = await self.chain.ainvoke({
            "message": message,
            "chat_history": chat_history,
            "context": context,
        })
        return response.content
