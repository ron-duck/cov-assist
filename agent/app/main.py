import json
import logging
from contextlib import asynccontextmanager
from typing import Any

import uuid
import uvicorn
import httpx
from fastapi import FastAPI, HTTPException, Request

from .config import settings
from .llm import LlmClient, SYSTEM_PROMPT
from .models import AskRequest, AskResponse, HealthResponse, SessionState, ConversationTurn, ToolCallRecord 
from .tools import GatewayTools, TOOL_SCHEMAS, execute_tool


logger = logging.getLogger(__name__)
sessions: dict[str, SessionState] = {}

def get_or_create_session(session_id: str) -> SessionState:
    if session_id not in sessions:
        sessions[session_id] = SessionState(session_id=session_id)
    return sessions[session_id]

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.llm_client = LlmClient()
    app.state.gateway_tools = GatewayTools()
    try:
        yield
    finally:
        await app.state.llm_client.aclose()
        await app.state.gateway_tools.aclose()


app = FastAPI(title="Coverity Agent", version="0.1.0", lifespan=lifespan)


def get_llm_client(request: Request) -> LlmClient:
    return request.app.state.llm_client


def get_gateway_tools(request: Request) -> GatewayTools:
    return request.app.state.gateway_tools


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(ok=True, service="agent", version="0.1.0")


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest, request: Request) -> AskResponse:
    session_id = req.session_id or str(uuid.uuid4())
    state = get_or_create_session(session_id)
    llm = get_llm_client(request)
    tools = get_gateway_tools(request)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.question},
    ]
    tool_log: list[ToolCallRecord] = []

    for _ in range(settings.llm_max_tool_round_trips):
        try:
            completion = await llm.create_chat_completion(messages=messages, tools=TOOL_SCHEMAS)
        except httpx.HTTPStatusError as exc:  # type: ignore[name-defined]
            raise HTTPException(status_code=502, detail=f"LLM HTTP error: {exc.response.status_code}")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}")

        choice = completion.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls") or []

        assistant_message: dict[str, Any] = {"role": "assistant"}
        if message.get("content") is not None:
            assistant_message["content"] = message.get("content")
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls
        messages.append(assistant_message)

        if not tool_calls:
            answer = message.get("content") or "I could not produce an answer."
            turn = ConversationTurn(question=req.question, answer=answer, tool_calls=tool_log)
            state.recent_turns.append(turn)
            state.recent_turns = state.recent_turns[-10:]
            for call in tool_log:
                if call.tool_call_id:
                    args = call.arguments or {}

                    stream = args.get("stream")
                    if isinstance(stream, str) and stream.strip():
                        state.last_stream = stream

                    cid = args.get("cid")
                    if isinstance(cid, str) and cid.strip():
                        state.last_cid = cid

            return AskResponse(answer=answer, tool_calls=tool_log)

        for tool_call in tool_calls:
            fn = tool_call.get("function", {})
            tool_name = fn.get("name")
            tool_args = fn.get("arguments", "{}")
            log_entry, result = await execute_tool(tools, tool_name, tool_args)
            #log_entry["id"] = tool_call.get("id")
            log_entry.tool_call_id = tool_call.get("id")
            tool_log.append(log_entry)            
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.get("id"),
                    "content": json.dumps(result),
                }
            )

    raise HTTPException(status_code=502, detail="LLM exceeded tool round-trip limit")


def main() -> None:
    logging.basicConfig(level=getattr(logging, settings.agent_log_level.upper(), logging.INFO))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.agent_port,
        log_level=settings.agent_log_level.lower(),
    )


if __name__ == "__main__":
    main()
