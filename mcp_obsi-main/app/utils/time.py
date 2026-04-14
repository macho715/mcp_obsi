from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def now_tz(tz_name: str | None) -> datetime:
    if not tz_name:
        return datetime.now().astimezone()
    try:
        return datetime.now(ZoneInfo(tz_name))
    except ZoneInfoNotFoundError:
        return datetime.now().astimezone()
