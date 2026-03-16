import json
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from .config import settings

IssueStatus = Literal["Fixed", "Dismissed", "Triaged", "New"]
Impact = Literal["Audit","Low", "Medium", "High"]

class ListStreamsArgs(BaseModel):
    model_config = {
        "extra": "forbid",
    }

class SearchIssuesArgs(BaseModel):
    stream: str = Field(..., min_length=1)
    status: list[IssueStatus] | None = None
    impact: list[Impact] | None = None
    limit: int = Field(default=20, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    model_config = {
        "extra": "forbid",
    }

class CountIssuesArgs(BaseModel):
    stream: str = Field(..., min_length=1)
    status: list[IssueStatus] | None = None
    impact: list[Impact] | None = None
    model_config = {
        "extra": "forbid",
    }

class TopIssuesArgs(BaseModel):
    stream: str = Field(..., min_length=1)
    status: list[IssueStatus] | None = None
    impact: list[Impact] | None = None
    limit: int = Field(default=20, ge=1, le=200)
    model_config = {
        "extra": "forbid",
    }

class IssueDetailsArgs(BaseModel):
    cid: str = Field(..., min_length=1)
    stream: str = Field(..., min_length=1)
    model_config = {
        "extra": "forbid",
    }

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
        status: list[IssueStatus] | None = None,
        impact: list[Impact] | None = None,
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

    async def get_issue_details(
            self, 
            cid: str, 
            stream: str
    ) -> dict[str, Any]:
        payload = {
            "cid": cid,
            "stream": stream,
        }

        res = await self._client.post("/issues/details", json=payload)
        res.raise_for_status()
        return res.json()
    

def tool_schema(name: str, description: str, model: type[BaseModel]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": model.model_json_schema(),
        },
    }

TOOL_SCHEMAS = [
    tool_schema("list_streams", "List all available Coverity streams that the agent can access", ListStreamsArgs),
    tool_schema("search_issues", "Search Coverity issues within a stream using status, impact, limit, and offset filters", SearchIssuesArgs),
    tool_schema("count_issues", "Count Coverity issues within a stream using status and impact filters", CountIssuesArgs),
    tool_schema("top_issues", "Get top Coverity issues within a stream using status, impact and limit filters", TopIssuesArgs),
    tool_schema("get_issue_details", "Get detailed information about a specific Coverity issue by CID and stream", IssueDetailsArgs),
]

TOOL_ARG_MODELS: dict[str, type[BaseModel]] = {
    "list_streams": ListStreamsArgs,
    "search_issues": SearchIssuesArgs,
    "count_issues": CountIssuesArgs,
    "top_issues": TopIssuesArgs,
    "get_issue_details": IssueDetailsArgs,
}

async def execute_tool(
    tools: GatewayTools,
    name: str,
    arguments_json: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        raw_args = json.loads(arguments_json or "{}")
    except json.JSONDecodeError as exc:
        result = {"ok": False, "error": f"Invalid tool arguments JSON: {exc}"}
        return {"name": name, "arguments": arguments_json, "result": result}, result

    fn = getattr(tools, name, None)
    model_cls = TOOL_ARG_MODELS.get(name)

    if fn is None or model_cls is None:
        result = {
            "ok": False,
            "error": f"Unknown tool: {name}",
            "available_tools": sorted(TOOL_ARG_MODELS.keys()),
        }
        return {"name": name, "arguments": raw_args, "result": result}, result

    try:
        validated = model_cls.model_validate(raw_args)
        result = await fn(**validated.model_dump(exclude_none=True))
        return {"name": name, "arguments": validated.model_dump(), "result": result}, result
    except httpx.HTTPStatusError as exc:
        try:
            payload = exc.response.json()
        except Exception:
            payload = exc.response.text

        result = {
            "ok": False,
            "error": f"Gateway returned HTTP {exc.response.status_code}",
            "details": payload,
        }
        return {"name": name, "arguments": raw_args, "result": result}, result
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
        return {"name": name, "arguments": raw_args, "result": result}, result
