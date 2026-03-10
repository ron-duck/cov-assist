from pydantic import BaseModel, Field
from typing import Literal

Impact = Literal["Audit","Low", "Medium", "High"]
IssueStatus = Literal["Fixed", "Dismissed", "Triaged", "New"]

class AppliedIssueFilters(BaseModel):
    impact: list[Impact] | None = None
    status: list[IssueStatus] | None = None

class StreamsListResponse(BaseModel):
    streams: list[str]

class IssuesTopRequest(BaseModel):
    stream: str = Field(..., min_length=1)
    impact: list[Impact] | None = None
    status: list[IssueStatus] | None = None
    limit: int = Field(default=20, ge=1, le=200)

class IssueSummary(BaseModel):
    cid: str | None = None
    checker: str | None = None
    impact: str | None = None
    status: str | None = None
    file: str | None = None
    function: str | None = None
    first_detected: str | None = None
    last_detected: str | None = None
    message: str | None = None

class IssuesTopResponse(BaseModel):
    stream: str
    limit: int
    total_available: int
    total_returned: int
    filters: AppliedIssueFilters
    issues: list[IssueSummary]

class IssuesCountRequest(BaseModel):
    stream: str = Field(..., min_length=1)
    impact: list[Impact] | None = None
    status: list[IssueStatus] | None = None

class IssuesCountResponse(BaseModel):
    stream: str
    count: int
    filters: AppliedIssueFilters

class IssuesSearchRequest(BaseModel):
    stream: str = Field(..., min_length=1)
    impact: list[Impact] | None = None
    status: list[IssueStatus] | None = None   
    limit: int = Field(default=20, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

class IssuesSearchResponse(BaseModel):
    stream: str
    limit: int
    total_available: int
    total_returned: int
    filters: AppliedIssueFilters
    issues: list[IssueSummary]