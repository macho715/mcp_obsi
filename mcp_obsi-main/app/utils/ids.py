from __future__ import annotations

from datetime import datetime
from uuid import uuid4


def make_memory_id(dt: datetime) -> str:
    return f"MEM-{dt.strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6].upper()}"
