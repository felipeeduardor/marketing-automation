"""RAG-based knowledge base for the FAQ agent."""

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeBase:
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.settings.OPENAI_API_KEY)
        self.vectorstore: FAISS | None = None
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

    async def load_documents(self, texts: list[str], metadatas: list[dict] | None = None):
        """Load text documents into the vector store."""
        docs = [
            Document(page_content=text, metadata=meta or {})
            for text, meta in zip(texts, metadatas or [{}] * len(texts))
        ]
        chunks = self.splitter.split_documents(docs)
        self.vectorstore = await FAISS.afrom_documents(chunks, self.embeddings)
        logger.info(f"Loaded {len(chunks)} chunks into knowledge base")

    async def search(self, query: str, k: int = 3) -> list[Document]:
        """Search the knowledge base for relevant documents."""
        if not self.vectorstore:
            return []
        return await self.vectorstore.asimilarity_search(query, k=k)

    def load_default_knowledge(self):
        """Load default company knowledge base. Override per tenant."""
        default_docs = [
            "Nossa empresa oferece soluções de automação de marketing e vendas.",
            "Nossos planos incluem: Básico (R$99/mês), Profissional (R$299/mês) e Enterprise (R$799/mês).",
            "O plano Básico inclui: chatbot com IA, rastreamento de leads e dashboard básico.",
            "O plano Profissional inclui tudo do Básico mais: integração CRM, relatórios avançados e suporte prioritário.",
            "O plano Enterprise inclui tudo do Profissional mais: multi-agentes IA, API dedicada e gerente de conta.",
            "Horário de atendimento: Segunda a Sexta, 9h às 18h.",
            "Para suporte técnico, entre em contato pelo e-mail suporte@empresa.com.",
            "Aceitamos pagamento via cartão de crédito, boleto e PIX.",
            "Oferecemos 14 dias de teste gratuito em todos os planos.",
            "Nossa política de cancelamento permite cancelar a qualquer momento sem multa.",
        ]
        import asyncio
        asyncio.create_task(self.load_documents(default_docs))


# Singleton
knowledge_base = KnowledgeBase()
