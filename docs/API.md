# API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Internal endpoints (CRM, operations, agents, metrics, lead queries) require
`Authorization: Bearer <ADMIN_API_TOKEN>` plus the `X-Tenant-ID` header.
Public endpoints (VSL page and events, pixel, lead capture, webhooks) take the tenant
from the `tenant` query parameter or the `X-Tenant-ID` header.

## Endpoints

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
