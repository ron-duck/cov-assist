import httpx
from fastapi import APIRouter, HTTPException, Request
from .models import (
    StreamsListResponse,
    IssuesTopRequest,
    IssuesTopResponse,
    IssueSummary,
    IssuesCountRequest,
    IssuesCountResponse,
    AppliedIssueFilters,
    IssuesSearchRequest,
    IssuesSearchResponse,
)
from .coverity_client import CoverityClient

router = APIRouter()


def get_coverity_client(request: Request) -> CoverityClient:
    client = getattr(request.app.state, "coverity_client", None)
    if client is None:
        raise RuntimeError("Coverity client not initialized")
    return client

def map_issue_row_to_summary(row: dict) -> IssueSummary:
    return IssueSummary(
        cid=row.get("cid") or row.get("CID"),
        checker=row.get("checker"),
        impact=row.get("displayImpact"),
        status=row.get("status"),
        file=row.get("displayFile") or row.get("file"),
        function=row.get("displayFunction") or row.get("function"),
        first_detected=row.get("displayFirstDetected") or row.get("firstDetected"),
        last_detected=row.get("displayLastDetected") or row.get("lastDetected"),
        message=row.get("displayType") or row.get("message") or row.get("summary"),
    )

@router.get("/health", response_model=dict)
async def health(request: Request):
    client_ready = getattr(request.app.state, "coverity_client", None) is not None
    return {
        "ok": True,
        "service": "core",
        "version": "0.2.0",
        "clientReady": client_ready,
    }


@router.get("/streams", response_model=StreamsListResponse)
async def list_streams(request: Request):
    client = get_coverity_client(request)
    try:
        streams = await client.list_streams()
        return StreamsListResponse(streams=sorted(set(streams)))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Coverity streams query failed: {e}")


@router.post("/issues/top", response_model=IssuesTopResponse)
async def issues_top(req: IssuesTopRequest, request: Request):
    client = get_coverity_client(request)
    try:
        table = await client.issues_top(
            stream=req.stream,
            impact=req.impact,
            status=req.status,
            limit=req.limit,
        )
        issues: list[IssueSummary] = []

        for row in table.rows[:req.limit]:
            issues.append(
                IssueSummary(
                    cid=row.get("cid") or row.get("CID"),
                    checker=row.get("checker"),
                    impact=row.get("displayImpact"),
                    status=row.get("status"),
                    file=row.get("displayFile") or row.get("file"),
                    function=row.get("displayFunction") or row.get("function"),
                    first_detected=row.get("displayFirstDetected") or row.get("firstDetected"),
                    last_detected=row.get("displayLastDetected") or row.get("lastDetected"),
                    message=row.get("displayType") or row.get("message") or row.get("summary"),
                )
            )

        return IssuesTopResponse(
            stream=req.stream,
            limit=req.limit,
            total_available=table.total_rows,
            total_returned=len(issues),
            filters=AppliedIssueFilters(
                impact=req.impact,
                status=req.status,
            ),
            issues=issues,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Coverity HTTP error: {e.response.status_code} {e.response.text[:500]}",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Coverity issues query failed: {e}")


@router.post("/issues/count", response_model=IssuesCountResponse)
async def issues_count(req: IssuesCountRequest, request: Request):
    client = get_coverity_client(request)
    try:
        result = await client.issues_count(
            stream=req.stream,
            impact=req.impact,
            status=req.status,
        )
        return IssuesCountResponse(
            stream=result["stream"],
            count=result["count"],
            filters=AppliedIssueFilters(**result["filters"]),
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Coverity HTTP error: {e.response.status_code} {e.response.text[:500]}",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Coverity issues count query failed: {e}")

@router.post("/issues/search", response_model=IssuesSearchResponse)
async def issues_search(req: IssuesSearchRequest, request: Request):
    client = get_coverity_client(request)
    try:
        cols = await client.resolve_issue_columns()

        table = await client.issues_search(
            stream=req.stream,
            impact=req.impact,
            status=req.status,
            limit=req.limit,
            offset=req.offset,
            columns=cols,
        )
        issues: list[IssueSummary] = []

        for row in table.rows:
            issues.append(map_issue_row_to_summary(row))

        return IssuesSearchResponse(
            stream=req.stream,
            limit=req.limit,
            total_available=table.total_rows,
            total_returned=len(issues),
            filters=AppliedIssueFilters(
                impact=req.impact,
                status=req.status,
            ),
            issues=issues,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Coverity HTTP error: {e.response.status_code} {e.response.text[:500]}",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Coverity issues search query failed: {e}")