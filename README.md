# Marketing Automation System

Sistema interno de marketing e vendas para vender o **VitaClini** (vitaclini.com.br) a clínicas:
CRM, página de vendas com vídeo (VSL), tracking de campanhas, agentes de marketing e anúncios e dashboard.

## Stack

- **Backend:** Python + FastAPI
- **Banco de Dados:** PostgreSQL
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

## Segurança

A API interna (CRM, operações, agentes, métricas, leads) exige `Authorization: Bearer <ADMIN_API_TOKEN>`.
Sem `ADMIN_API_TOKEN` configurado, essas rotas respondem 503 (ficam trancadas).
Continuam públicas apenas: a página `/vsl` e os seus eventos, o pixel/registo de leads e os webhooks
(a verificação da Meta exige `META_VERIFY_TOKEN`).

O dashboard pede a senha `DASHBOARD_PASSWORD` e usa o mesmo `ADMIN_API_TOKEN` para falar com a API:

```bash
ADMIN_API_TOKEN=... DASHBOARD_PASSWORD=... streamlit run dashboard/app.py
```

## API Docs

Acesse `http://localhost:8000/docs` para a documentação interativa (Swagger).

Documentação detalhada em [docs/API.md](docs/API.md).

## Módulos

| Módulo | Status | Descrição |
|--------|--------|-----------|
| Funil VSL | Implementado | Página de vendas com vídeo, tracking de retenção e ida ao cadastro do VitaClini |
| Rastreamento | Implementado | UTM + pixel tracking por canal |
| CRM de clínicas | Implementado | Pipeline comercial, follow-ups, demos e pilotos |
| Dashboard | Implementado | Visão do funil comercial e gestão de clínicas em Streamlit |
| Agente de marketing | Implementado | Prioridades diárias, gargalos do funil e templates de venda |
| Agente de anúncios | Implementado | Copy, criativos, UTMs e plano A/B para campanhas de clínicas |
| Operação comercial | Implementado | Actividades, tarefas vencidas e registo de campanhas |
| Multi-tenant | Fase 5 | Arquitetura replicável por cliente |

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

## CRM interno para vender o SaaS a clínicas

O dashboard em `dashboard/app.py` liga-se à API e permite gerir o funil:

```text
Novo → Contactado → Respondeu → Decisor identificado → Demo agendada
→ Demo realizada → Piloto proposto → Piloto activo → Cliente pago / Perdido
```

Para iniciar o dashboard localmente, com a API a correr em paralelo:

```bash
streamlit run dashboard/app.py
```

Por defeito, o dashboard usa `http://localhost:8000/api/v1`. Pode alterar esta ligação com a variável de ambiente `API_BASE_URL`.

### Importante: base de dados já existente

O projecto usa `Base.metadata.create_all()`, que cria tabelas em bases novas, mas não adiciona
colunas a uma tabela `leads` já existente. Se já tiver uma base PostgreSQL com a tabela `leads`,
crie uma migração Alembic antes de fazer deploy para acrescentar os campos CRM definidos em
`app/models/lead.py`.

## Agente de marketing e funil

O endpoint `GET /api/v1/marketing/insights` lê os dados do CRM e entrega:

- follow-ups vencidos e clínicas sem próxima acção;
- prioridade comercial do dia;
- alertas de gargalo entre resposta, demo, piloto e cliente;
- métricas de avanço no funil;
- distribuição por origem e especialidade;
- templates de primeiro contacto, follow-up, demo, piloto e conversão.

O agente usa regras determinísticas para que as recomendações continuem disponíveis mesmo
quando não houver chave de IA configurada. A camada de IA pode ser acrescentada depois para
criar análises narrativas e variações de copy a partir destes dados.

## Agente de anúncios

O endpoint `POST /api/v1/ads/generate` gera uma campanha de aquisição para o SaaS de
WhatsApp de clínicas: anúncio A, anúncio B para teste, público recomendado, direcção de
criativo, script curto de vídeo, UTMs e limites de comunicação. O agente não publica
campanhas, não acede a contas de anúncios e não gasta orçamento automaticamente.


## Actividades e campanhas

O módulo operacional expõe actividades ligadas a clínicas (follow-up, chamada, demo,
proposta, onboarding ou tarefa) e campanhas de aquisição. Isto garante que cada lead tem
uma próxima acção e que cada campanha pode ser ligada às UTMs usadas no tracking.
## Funil VSL

Página de vendas com vídeo para vender o **VitaClini** (vitaclini.com.br) às clínicas:

```text
anúncio com UTMs → /vsl (vídeo + oferta) → cadastro grátis no VitaClini → upgrade pelo Stripe dentro do produto
```

- **Vídeo:** defina `VSL_VIDEO_URL` (arquivo `.mp4`/`.webm` ou link do YouTube). A oferta aparece depois de
  `VSL_CTA_DELAY_SECONDS` segundos de vídeo realmente assistido (0 = desde o início).
- **Oferta:** botão "Criar conta grátis" (`VSL_SIGNUP_URL`, por defeito `https://vitaclini.com.br/login?aba=cadastro`)
  com as UTMs do anúncio, e os planos Free / Pro / Enterprise de `app/utils/plans.py`
  (manter igual a `backend/app/planos.py` e `frontend/src/pages/Planos.jsx` do VitaClini).
- **Falar com especialista:** defina `VSL_WHATSAPP_NUMBER` (ex.: `5511999999999`) para mostrar um botão de WhatsApp.
- **Tracking:** cada visitante gera eventos (visita, play, 25/50/75/100%, oferta vista, ida ao cadastro, especialista),
  guardados em `vsl_events` com as UTMs. Use `?tenant=<id>` e as UTMs no link do anúncio.
- **Métricas:** `GET /api/v1/vsl/metrics?days=30` e o separador "Funil VSL" no dashboard.
