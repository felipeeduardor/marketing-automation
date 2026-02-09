# Marketing Automation System

Sistema completo de automação de marketing e vendas com chatbot multi-agentes IA.

## Stack

- **Backend:** Python + FastAPI
- **Banco de Dados:** PostgreSQL
- **IA/Chatbot:** LangChain + OpenAI
- **Dashboard:** Streamlit
- **Hospedagem:** Railway

## Quick Start

### 1. Clone e configure

```bash
cp .env.example .env
# Edite o .env com suas chaves de API
```

### 2. Com Docker (recomendado)

```bash
docker-compose up -d
```

### 3. Sem Docker

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Dashboard

```bash
streamlit run dashboard/app.py
```

## API Docs

Acesse `http://localhost:8000/docs` para a documentação interativa (Swagger).

Documentação detalhada em [docs/API.md](docs/API.md).

## Módulos

| Módulo | Status | Descrição |
|--------|--------|-----------|
| Chatbot IA | Implementado | Multi-agentes com LangChain + RAG |
| Rastreamento | Implementado | UTM + pixel tracking por canal |
| CRM | Fase 3 | Integração RD Station / HubSpot |
| Dashboard | Fase 4 | Métricas e relatórios Streamlit |
| Multi-tenant | Fase 5 | Arquitetura replicável por cliente |

## Arquitetura

O chatbot usa um sistema de multi-agentes com classificação automática de intenção:

1. **Lead Agent** - Identifica origem do lead e coleta dados
2. **Interest Agent** - Descobre interesses e necessidades
3. **FAQ Agent** - Responde dúvidas com RAG (base de conhecimento)
4. **Routing Agent** - Encaminha para o setor correto
5. **Checkout Agent** - Finaliza vendas e envia link de pagamento

## Rastreamento de Leads

O sistema de tracking suporta múltiplos canais com atribuição automática:

- **UTM Parameters** - Rastreamento via `utm_source`, `utm_medium`, `utm_campaign`
- **Pixel Tracking** - Pixel server-side (1x1 GIF) + snippets Facebook/Google Ads
- **Webhooks** - Recebe dados direto de Facebook, Instagram, WhatsApp e Google Ads
- **Detecção automática** - Identifica o canal de origem do lead pelos UTM params

## Testes

```bash
pip install pytest anyio httpx
pytest tests/
```
