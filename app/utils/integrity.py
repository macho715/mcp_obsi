from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections.abc import Mapping
from typing import Any

HMAC_PREFIX = "hmac-sha256:"


def _normalized(value):
    if isinstance(value, Mapping):
        return {key: _normalized(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalized(item) for item in value]
    return value


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    normalized = {key: value for key, value in payload.items() if key != "mcp_sig"}
    return json.dumps(
        _normalized(normalized),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def sign_payload(secret: str, payload: dict[str, Any]) -> str:
    digest = hmac.new(secret.encode("utf-8"), _canonical_bytes(payload), hashlib.sha256).digest()
    encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"{HMAC_PREFIX}{encoded}"


def verify_payload(secret: str, payload: dict[str, Any], signature: str | None) -> bool:
    if not signature:
        return False
    return hmac.compare_digest(signature, sign_payload(secret, payload))
