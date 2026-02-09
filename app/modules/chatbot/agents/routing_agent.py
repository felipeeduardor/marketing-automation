"""Routing Agent: routes the lead to the correct department."""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """Você é um agente especializado em encaminhar clientes para o setor correto.
Com base na conversa, determine para qual setor o cliente deve ser encaminhado:

Setores disponíveis:
- VENDAS: interessado em comprar, contratar, conhecer planos
- SUPORTE: problemas técnicos, bugs, dificuldades com o sistema
- FINANCEIRO: pagamentos, cobranças, notas fiscais, reembolsos
- COMERCIAL: parcerias, propostas corporativas, grandes contas
- SAC: reclamações, elogios, sugestões gerais

Responda SEMPRE em português brasileiro.
Informe ao cliente para qual setor ele será encaminhado e o que esperar.
Inclua no final da sua resposta a tag [SETOR:NOME_DO_SETOR] para roteamento automático.

Contexto da conversa até agora:
{chat_history}
"""


class RoutingAgent:
    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{message}"),
        ])
        self.chain = self.prompt | self.llm

    async def process(self, message: str, chat_history: str = "") -> str:
        logger.info(f"RoutingAgent processing: {message[:50]}...")
        response = await self.chain.ainvoke({
            "message": message,
            "chat_history": chat_history,
        })
        return response.content

    def extract_sector(self, response: str) -> str | None:
        """Extract sector tag from response."""
        import re
        match = re.search(r"\[SETOR:(\w+)\]", response)
        return match.group(1) if match else None
