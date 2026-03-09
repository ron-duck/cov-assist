# Coverity Assistant (Python core + Node gateway)

Internal-only, security-first setup:
- `core/` Python service that talks to Coverity Connect (read-only)
- `gateway/` Node.js gateway that enforces auth, rate limits, audit logs, and forwards to core
- `docker-compose.yml` runs both on an internal host near Coverity

## Quick start (internal VM)
1) Copy `.env.example` to `.env` and fill in values.
2) Generate a strong gateway API key:
   - `python tools/gen_apikey.py`
3) Start:
   - `docker compose up -d --build`
4) Open:
   - Gateway health: `http://localhost:8080/health`
   - Core health: `http://localhost:8000/health`

## Security posture (high level)
- Gateway requires `X-API-Key`
- Per-key stream allow-list enforced at gateway (configurable)
- Rate limiting at gateway
- Core uses TLS verification by default (explicit opt-out available)
- No “dummy” fallback data anywhere
- Strict request validation and hard caps on limit/lookback
- Audit logs (who/what/when/result_count), no secrets

## What you implement next
- Wire real Coverity endpoints in `core/app/coverity_client.py`
- Add additional semantic routes in `core/app/routes.py`
- (Optional) Add an MCP transport layer later; keep semantics in core unchanged


## Notes for your Coverity instance
- Set `COVERITY_BASE_URL` to include `/api/v2` (from your OpenAPI `servers.url`).
- This API uses **HTTP Basic Auth**.
