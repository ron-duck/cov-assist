from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import httpx

from .config import settings


@dataclass(frozen=True)
class TableResult:
    offset: int
    total_rows: int
    columns: list[str]
    rows: list[dict[str, str]]  # columnKey -> value (string)


class CoverityClient:
    def __init__(self) -> None:
        verify: bool | str = settings.coverity_tls_verify
        if settings.coverity_ca_bundle:
            verify = settings.coverity_ca_bundle

        # BasicAuth per OpenAPI security scheme
        self._client = httpx.AsyncClient(
            base_url=settings.coverity_base_url.rstrip("/"),
            timeout=httpx.Timeout(settings.http_timeout_seconds),
            verify=verify,
            auth=(settings.coverity_username, settings.coverity_password),
        )

        self._issues_columns_cache: dict[str, str] | None = None  # columnKey -> displayName

    async def close(self) -> None:
        await self._client.aclose()

    async def list_streams(self) -> list[str]:
        # GET /streams
        resp = await self._client.get("/streams")
        resp.raise_for_status()
        data = resp.json()

        # Spec: StreamsOrError -> Streams{streams:[Stream]}
        if isinstance(data, dict) and isinstance(data.get("streams"), list):
            out: list[str] = []
            for s in data["streams"]:
                if isinstance(s, dict) and s.get("name"):
                    out.append(str(s["name"]))
            return out

        raise ValueError("Unexpected /streams response shape")

    async def issues_columns(self) -> dict[str, str]:
        # GET /issues/columns -> [{columnKey,name},...]
        if self._issues_columns_cache is not None:
            return self._issues_columns_cache

        resp = await self._client.get("/issues/columns")
        resp.raise_for_status()
        data = resp.json()

        mapping: dict[str, str] = {}
        if isinstance(data, list):
            for it in data:
                if isinstance(it, dict) and it.get("columnKey"):
                    mapping[str(it["columnKey"])] = str(it.get("name") or it["columnKey"])
        if not mapping:
            raise ValueError("Unexpected /issues/columns response shape")

        self._issues_columns_cache = mapping
        return mapping

    async def issues_search(
        self,
        *,
        stream: str,
        impact: list[str],
        status: list[str],
        limit: int,
        offset: int = 0,
        columns: list[str] | None = None,
        sort_column: str = "impact",
        sort_order: str = "DESC",
        locale: str | None = None,
        by_snapshot: bool = True,
        snapshot_scope_show: str = "last()",
    ) -> TableResult:
        # Build SearchRequest per OpenAPI schema
        # Stream filter uses NameMatcher with columnKey "streams" (per NameMatcher docs)
        filters = [{
            "columnKey": "streams",
            "matchMode": "oneOrMoreMatch",
            "matchers": [{"type": "nameMatcher", "class": "Stream", "name": stream}],
        }]

        if status:
            filters.append({
                "columnKey": "status",
                "matchMode": "oneOrMoreMatch",
                "matchers": [{"type": "keyMatcher", "key": s} for s in status],
            })

        if impact:
            filters.append({
                "columnKey": "displayImpact",
                "matchMode": "oneOrMoreMatch",
                "matchers": [{"type": "keyMatcher", "key": v} for v in impact],
            })

        body = {"columns": (columns if columns else ["cid", "displayImpact", "status"]), "filters": filters}
        params = {"includeColumnLabels": False, "offset": offset, "rowCount": limit}
        resp = await self._client.post("/issues/search", params=params, json=body)
        resp.raise_for_status()
        data = resp.json()

        # SearchResponse: {offset,totalRows,columns:[ColumnKey],rows:[[DataRow]]}
        if not isinstance(data, dict):
            raise ValueError("Unexpected /issues/search response shape (not an object)")

        columns_resp = data.get("columns") or []
        rows_resp = data.get("rows") or []
        off = int(data.get("offset") or 0)
        total = int(data.get("totalRows") or 0)

        normalized_rows: list[dict[str, str]] = []
        if isinstance(rows_resp, list):
            for row in rows_resp:
                row_map: dict[str, str] = {}
                if isinstance(row, list):
                    for cell in row:
                        if isinstance(cell, dict):
                            k = cell.get("key")
                            v = cell.get("value")
                            if isinstance(k, str) and v is not None:
                                row_map[k] = str(v)
                if row_map:
                    normalized_rows.append(row_map)

        cols_list = [str(c) for c in columns_resp] if isinstance(columns_resp, list) else []

        return TableResult(offset=off, total_rows=total, columns=cols_list, rows=normalized_rows)

    async def issues_count(
        self,
        *,
        stream: str,
        impact: list[str],
        status: list[str],
    ) -> dict[str, Any]:
        table = await self.issues_search(
        stream=stream,
        impact=impact,
        status=status,
        limit=1,
        offset=0,
        columns=["cid"],  # minimal payload since we only care about totalRows
        sort_column="Impact",
        sort_order="DESC",
        by_snapshot=True,
        snapshot_scope_show="last()",
    )
        return {"stream": stream, "count": table.total_rows, "filters": {"impact": impact, "status": status}}

    async def issues_top(
        self,
        *,
        stream: str,
        impact: list[str],
        status: list[str],
        limit: int,
        preferred_columns: list[str] | None = None,
    ) -> TableResult:
        # Resolve columns safely: only request columns that exist for Issues view.
        cols_map = await self.issues_columns()

        if preferred_columns is None:
            # Conservative defaults; will be intersected with actual available keys
            preferred_columns = [
                "cid",
                "checker",
                "impact",
                "status",
                "displayImpact",
                "displayType",
                "displayFile",
                "displayFunction",
                "displayFirstDetected",
                "displayLastDetected",
            ]

        requested = [c for c in preferred_columns if c in cols_map]
        # If none match, let server return default columns.
        fallback = list(cols_map.keys())[:20]
        cols = requested if requested else None

        return await self.issues_search(
            stream=stream,
            impact=impact,
            status=status,
            limit=limit,
            offset=0,
            columns=cols,
            sort_column="impact",
            sort_order="DESC",
            by_snapshot=True,
            snapshot_scope_show="last()",
        )
