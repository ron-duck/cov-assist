import json
from typing import Any

import httpx

from .config import settings


class GatewayTools:
    def __init__(self) -> None:
        limits = httpx.Limits(
            max_connections=20,
            max_keepalive_connections=10,
        )
        
        self._client = httpx.AsyncClient(
            base_url=settings.gateway_base_url.rstrip("/"),
            timeout=30.0,
            headers={"X-API-Key": settings.gateway_api_key},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def list_streams(self) -> dict[str, Any]:
        res = await self._client.get("/streams")
        res.raise_for_status()
        return res.json()

    async def search_issues(
        self,
        stream: str,
        status: list[str] | None = None,
        impact: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        payload = {
            "stream": stream,
            "limit": limit,
            "offset": offset,
        }
        if status is not None:
            payload["status"] = status
        if impact is not None:
            payload["impact"] = impact  

        res = await self._client.post("/issues/search", json=payload)
        res.raise_for_status()
        return res.json()

    async def count_issues(
        self,
        stream: str,
        status: list[str] | None = None,
        impact: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "stream": stream,
        }
        if status is not None:
            payload["status"] = status
        if impact is not None:
            payload["impact"] = impact

        res = await self._client.post("/issues/count", json=payload)
        res.raise_for_status()
        return res.json()

    async def top_issues(
        self,
        stream: str,
        status: list[str] | None = None,
        impact: list[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        payload = {
            "stream": stream,
            "limit": limit,
        }
        if status is not None:
            payload["status"] = status

        if impact is not None:
            payload["impact"] = impact  

        res = await self._client.post("/issues/top", json=payload)
        res.raise_for_status()
        return res.json()


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_streams",
            "description": "List available Coverity streams that the agent can access.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_issues",
            "description": "Search Coverity issues within a stream using status, impact, limit, and offset filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stream": {"type": "string"},
                    "status": {"type": "array", "items": {"type": "string"}},
                    "impact": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                    "offset": {"type": "integer", "minimum": 0},
                },
                "required": ["stream"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_issues",
            "description": "Count Coverity issues within a stream using status and impact filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stream": {"type": "string"},
                    "status": {"type": "array", "items": {"type": "string"}},
                    "impact": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["stream"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_issues",
            "description": "Return a top slice of Coverity issues within a stream using status, impact, and limit filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stream": {"type": "string"},
                    "status": {"type": "array", "items": {"type": "string"}},
                    "impact": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                },
                "required": ["stream"],
                "additionalProperties": False,
            },
        },
    },
]


async def execute_tool(tools: GatewayTools, name: str, arguments_json: str) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        args = json.loads(arguments_json or "{}")
    except json.JSONDecodeError as exc:
        result = {"ok": False, "error": f"Invalid tool arguments JSON: {exc}"}
        return {"name": name, "arguments": arguments_json, "result": result}, result

    fn = getattr(tools, name, None)
    if fn is None:
        result = {"ok": False, "error": f"Unknown tool: {name}"}
        return {"name": name, "arguments": args, "result": result}, result

    try:
        result = await fn(**args)
        return {"name": name, "arguments": args, "result": result}, result
    except httpx.HTTPStatusError as exc:
        payload: Any
        try:
            payload = exc.response.json()
        except Exception:
            payload = exc.response.text
        result = {
            "ok": False,
            "error": f"Gateway returned HTTP {exc.response.status_code}",
            "details": payload,
        }
        return {"name": name, "arguments": args, "result": result}, result
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
        return {"name": name, "arguments": args, "result": result}, result
