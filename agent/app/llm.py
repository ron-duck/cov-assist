from typing import Any

import httpx

from .config import settings


SYSTEM_PROMPT = """You are a Coverity assistant. Answer user questions by using tools when needed.
Use the available tools to inspect streams and issues. Do not invent streams, counts, or issues.
If the user's stream is unclear, you may call list_streams first.
Be concise and factual. Prefer grounded answers based on tool output.
"""


class LlmClient:
    def __init__(self) -> None:
        headers = {"Content-Type": "application/json"}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"
        self._client = httpx.AsyncClient(
            base_url=settings.llm_base_url.rstrip("/"),
            timeout=settings.llm_timeout_seconds,
            headers=headers,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def create_chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": settings.llm_temperature,
        }
        res = await self._client.post("/v1/chat/completions", json=payload)
        res.raise_for_status()
        return res.json()
