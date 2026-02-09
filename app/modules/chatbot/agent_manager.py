"""Agent Manager: orchestrates multi-agent routing based on user intent."""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.modules.chatbot.agents.lead_agent import LeadAgent
from app.modules.chatbot.agents.interest_agent import InterestAgent
from app.modules.chatbot.agents.faq_agent import FAQAgent
from app.modules.chatbot.agents.routing_agent import RoutingAgent
from app.modules.chatbot.agents.checkout_agent import CheckoutAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)

CLASSIFIER_PROMPT = """Analise a mensagem do usuário e classifique a intenção principal.
Retorne APENAS uma das seguintes categorias (sem explicação):

- LEAD: o usuário é novo, quer se apresentar, ou precisa fornecer dados de contato
- INTEREST: o usuário quer saber sobre produtos, serviços ou planos disponíveis
- FAQ: o usuário tem uma dúvida ou pergunta geral (preços, horários, políticas)
- ROUTING: o usuário quer falar com um setor específico ou humano
- CHECKOUT: o usuário quer comprar, contratar, fazer pagamento ou fechar negócio

Histórico da conversa:
{chat_history}

Mensagem do usuário: {message}

Categoria:"""


class AgentManager:
    def __init__(self):
        settings = get_settings()
        self.classifier = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0,
        )
        self.classifier_prompt = ChatPromptTemplate.from_template(CLASSIFIER_PROMPT)
        self.classifier_chain = self.classifier_prompt | self.classifier

        self.agents = {
            "LEAD": LeadAgent(),
            "INTEREST": InterestAgent(),
            "FAQ": FAQAgent(),
            "ROUTING": RoutingAgent(),
            "CHECKOUT": CheckoutAgent(),
        }

        # In-memory session store (replace with Redis in production)
        self.sessions: dict[str, list[dict]] = {}

    async def classify_intent(self, message: str, chat_history: str) -> str:
        """Classify user message intent to route to correct agent."""
        response = await self.classifier_chain.ainvoke({
            "message": message,
            "chat_history": chat_history,
        })
        intent = response.content.strip().upper()

        # Validate intent
        if intent not in self.agents:
            logger.warning(f"Unknown intent '{intent}', defaulting to FAQ")
            intent = "FAQ"

        logger.info(f"Classified intent: {intent}")
        return intent

    def get_chat_history(self, session_id: str) -> str:
        """Get formatted chat history for a session."""
        history = self.sessions.get(session_id, [])
        return "\n".join(
            f"{'Usuário' if m['role'] == 'user' else 'Bot'}: {m['content']}"
            for m in history[-10:]  # Last 10 messages
        )

    def save_message(self, session_id: str, role: str, content: str):
        """Save a message to session history."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({"role": role, "content": content})

    async def process_message(self, session_id: str, message: str) -> tuple[str, str]:
        """Process a message and return (response, agent_type)."""
        chat_history = self.get_chat_history(session_id)
        self.save_message(session_id, "user", message)

        # Classify intent
        intent = await self.classify_intent(message, chat_history)

        # Route to appropriate agent
        agent = self.agents[intent]
        response = await agent.process(message, chat_history)

        self.save_message(session_id, "assistant", response)
        logger.info(f"Session {session_id}: {intent} agent responded")

        return response, intent


# Singleton
agent_manager = AgentManager()
