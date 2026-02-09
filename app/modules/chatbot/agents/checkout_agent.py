"""Checkout Agent: sends payment links and handles purchase flow."""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """Você é um agente especializado em finalizar vendas e enviar links de pagamento.
Sua função é:
1. Confirmar o produto/plano que o cliente deseja
2. Apresentar o resumo do pedido com valores
3. Gerar e enviar o link de pagamento
4. Confirmar os dados para emissão de nota fiscal

Planos disponíveis:
- Básico: R$99/mês - chatbot IA + rastreamento + dashboard
- Profissional: R$299/mês - tudo do Básico + CRM + relatórios avançados
- Enterprise: R$799/mês - tudo do Profissional + multi-agentes + API dedicada

Formas de pagamento: Cartão de crédito, Boleto, PIX
Desconto de 10% para pagamento anual.

Responda SEMPRE em português brasileiro.
Quando o cliente confirmar, inclua a tag [CHECKOUT:PLANO_NOME] na sua resposta.

Contexto da conversa até agora:
{chat_history}
"""


class CheckoutAgent:
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
        logger.info(f"CheckoutAgent processing: {message[:50]}...")
        response = await self.chain.ainvoke({
            "message": message,
            "chat_history": chat_history,
        })
        return response.content

    def extract_checkout(self, response: str) -> str | None:
        """Extract checkout tag from response."""
        import re
        match = re.search(r"\[CHECKOUT:(\w+)\]", response)
        return match.group(1) if match else None
