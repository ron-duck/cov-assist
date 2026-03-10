# Coverity Assistant

Three-service layout:
- `core/` Python service that talks to Coverity Connect
- `gateway/` Node.js gateway that enforces auth, rate limits, audit logs, and forwards to core
- `agent/` Python NLQ agent that uses an LLM plus the gateway tools

## Quick start
1. Copy `.env.example` to `.env` and fill in values.
2. Generate a strong gateway API key with `python tools/gen_apikey.py`.
3. Set `AGENT_GATEWAY_API_KEY` to one of the values in `GATEWAY_API_KEYS`.
4. Configure the LLM settings:
   - `LLM_BASE_URL`
   - `LLM_MODEL`
   - `LLM_API_KEY` if your provider requires one
5. Start the stack:
   - `docker compose up -d --build`

## Endpoints
- Gateway health: `http://localhost:8080/health`
- Agent health: `http://localhost:8090/health`
- Agent ask: `POST http://localhost:8090/ask`

Example:

```bash
curl -X POST http://localhost:8090/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What high impact new issues exist in pygoat-master?"}'
```

## Notes
- `core` stays internal-only.
- The agent calls the gateway, not core directly.
- The agent expects an OpenAI-compatible chat completions endpoint at `LLM_BASE_URL`.
