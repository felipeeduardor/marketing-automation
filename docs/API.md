# API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All endpoints require the `X-Tenant-ID` header for multi-tenant isolation.

## Endpoints

### Chatbot

#### POST /chatbot/chat
Send a message and get an AI response.

**Request:**
```json
{
  "session_id": "unique-session-id",
  "message": "Olá, quero saber sobre os planos",
  "channel": "web",
  "phone": "+5511999999999",
  "name": "João"
}
```

**Response:**
```json
{
  "session_id": "unique-session-id",
  "response": "Olá João! Temos três planos disponíveis...",
  "agent_used": "FAQ",
  "lead_id": null
}
```

#### POST /chatbot/webhook/botconversa
Webhook endpoint for BotConversa integration.

**Request (from BotConversa):**
```json
{
  "subscriber_id": "12345",
  "name": "Maria",
  "phone": "+5511888888888",
  "message": "Quero contratar o plano profissional",
  "channel": "whatsapp"
}
```

#### GET /chatbot/sessions/{session_id}/history
Get chat history for a specific session.

#### DELETE /chatbot/sessions/{session_id}
Clear chat history for a session.

## Agent Types
- `LEAD` - Identifies lead origin and collects contact info
- `INTEREST` - Discovers product/service interests
- `FAQ` - Answers questions using knowledge base (RAG)
- `ROUTING` - Routes to the correct department
- `CHECKOUT` - Handles purchase flow and payment links

---

### Tracking (Rastreamento de Leads)

#### POST /tracking/track
Track a new lead with UTM parameters.

**Query params:** `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`

**Request:**
```json
{
  "name": "João",
  "email": "joao@email.com",
  "phone": "+5511999999999",
  "source_channel": "facebook"
}
```

**Response:** LeadResponse object

#### GET /tracking/pixel.gif
Serve a 1x1 tracking pixel (server-side tracking).

**Query params:** `tenant`, `channel`, `utm_source`, `utm_medium`, `utm_campaign`

Returns a transparent 1x1 GIF and logs the visit.

#### GET /tracking/pixel/snippet
Get the tracking pixel/tag HTML snippet for a channel.

**Query params:** `channel` (facebook, google_ads, server), `pixel_id`

#### GET /tracking/leads
List leads with optional filters.

**Query params:** `channel`, `status`

#### GET /tracking/leads/{lead_id}
Get a specific lead by ID.

#### GET /tracking/channels/stats
Get lead count statistics per channel.

### Channel Webhooks

#### POST /tracking/webhook/facebook
Receive leads from Facebook Lead Ads. Also supports GET for webhook verification.

#### POST /tracking/webhook/instagram
Receive leads from Instagram messaging.

#### POST /tracking/webhook/whatsapp
Receive leads from WhatsApp Business API. Also supports GET for webhook verification.

#### POST /tracking/webhook/google-ads
Receive leads from Google Ads lead form extensions.
