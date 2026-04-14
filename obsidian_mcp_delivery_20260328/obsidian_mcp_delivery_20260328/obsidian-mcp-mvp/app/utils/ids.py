from __future__ import annotations

from datetime import datetime
from secrets import token_hex


def make_memory_id(dt: datetime) -> str:
    return f"MEM-{dt.strftime('%Y%m%d-%H%M%S')}-{token_hex(3).upper()}"
