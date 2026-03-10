from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


class AskResponse(BaseModel):
    answer: str
    tool_calls: list[dict] = Field(default_factory=list)


class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str
