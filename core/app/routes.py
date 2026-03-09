import httpx
from fastapi import APIRouter, HTTPException
from .models import StreamsListResponse, IssuesTopRequest, IssuesTopResponse, IssueSummary,IssuesCountRequest, IssuesCountResponse
from .coverity_client import CoverityClient

router = APIRouter()

@router.get("/health", response_model=dict)
async def health():
    return {"ok": True, "service": "core", "version": "0.2.0"}

@router.get("/streams", response_model=StreamsListResponse)
async def list_streams():
    client = CoverityClient()
    try:
        streams = await client.list_streams()
        return StreamsListResponse(streams=sorted(set(streams)))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Coverity streams query failed: {e}")
    finally:
        await client.close()

@router.post("/issues/top", response_model=IssuesTopResponse)
async def issues_top(req: IssuesTopRequest):
    client = CoverityClient()
    try:
        table = await client.issues_top(stream=req.stream, impact=req.impact, status=req.status, limit=req.limit)
        issues: list[IssueSummary] = []

        for row in table.rows[:req.limit]:
            issues.append(IssueSummary(
                cid=row.get("cid") or row.get("CID"),
                checker=row.get("checker"),
                impact=row.get("displayImpact"),
                status=row.get("status"),
                file=row.get("displayFile") or row.get("file"),
                function=row.get("displayFunction") or row.get("function"),
                first_detected=row.get("displayFirstDetected") or row.get("firstDetected"),
                last_detected=row.get("displayLastDetected") or row.get("lastDetected"),
                message=row.get("displayType") or row.get("message") or row.get("summary"),
            ))

        return IssuesTopResponse(stream=req.stream, total_returned=len(issues), issues=issues)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Coverity HTTP error: {e.response.status_code} {e.response.text[:500]}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Coverity issues query failed: {e}")
    finally:
        await client.close()

@router.post("/issues/count", response_model=IssuesCountResponse)
async def issues_count(req: IssuesCountRequest):
    client = CoverityClient()
    try:
        result = await client.issues_count(stream=req.stream, impact=req.impact, status=req.status)
        return IssuesCountResponse(**result)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Coverity HTTP error: {e.response.status_code} {e.response.text[:500]}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Coverity issues count query failed: {e}")
    finally:
        await client.close()        