from datetime import datetime, timedelta, timezone
from .config import settings

def clamp_limit(limit: int) -> int:
    return min(max(1, limit), settings.max_limit)

def clamp_lookback_days(days: int) -> int:
    return min(max(1, days), settings.max_lookback_days)

def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def iso_utc_days_ago(days: int) -> str:
    d = clamp_lookback_days(days)
    return (datetime.now(timezone.utc) - timedelta(days=d)).isoformat()
