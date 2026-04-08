from pydantic import BaseModel, Field
from typing import Any, Optional


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


class AskResponse(BaseModel):
    answer: str
    tool_calls: list[dict] = Field(default_factory=list)


class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str

class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None

class SessionState(BaseModel):
    session_id: str
    last_stream: str | None = None
    last_cid: str | None = None
    recent_turns: list[ConversationTurn] = Field(default_factory=list)
    
class ConversationTurn(BaseModel):
    question: str
    answer: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
