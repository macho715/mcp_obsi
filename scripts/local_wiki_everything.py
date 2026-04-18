from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import ParseResult, urlencode, urlparse, urlunparse

import requests

DEFAULT_EVERYTHING_HTTP_BASE_URL = "http://127.0.0.1:8080"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class EverythingHttpError(RuntimeError):
    pass


def ensure_loopback_base_url(value: str) -> str:
    stripped = value.strip().rstrip("/")
    parsed = urlparse(stripped)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Everything HTTP base URL must use http or https")
    if parsed.hostname not in LOOPBACK_HOSTS:
        raise ValueError("Everything HTTP base URL must be loopback-only")
    return stripped


def resolve_everything_base_url() -> str:
    configured = os.getenv("EVERYTHING_HTTP_BASE_URL", DEFAULT_EVERYTHING_HTTP_BASE_URL)
    return ensure_loopback_base_url(configured)


def build_everything_url(
    base_url: str,
    query: str,
    limit: int,
    sort: str = "date_modified",
    ascending: bool = False,
) -> ParseResult:
    parsed = urlparse(ensure_loopback_base_url(base_url))
    params = {
        "search": query,
        "json": "1",
        "count": str(max(1, min(limit, 1000))),
        "path_column": "1",
        "size_column": "1",
        "date_modified_column": "1",
        "sort": sort,
        "ascending": "1" if ascending else "0",
    }
    return parsed._replace(path=parsed.path or "/", query=urlencode(params))


def parse_everything_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raise EverythingHttpError("Everything response did not include results[]")

    results: list[dict[str, Any]] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        parent = str(item.get("path") or "").strip()
        if not name or not parent:
            continue
        size = _parse_int_or_none(item.get("size"))
        full_path = str(Path(parent) / name)
        results.append(
            {
                "name": name,
                "path": full_path,
                "extension": Path(name).suffix.lower(),
                "size": size,
                "modifiedAt": _format_date_modified(item.get("date_modified")),
                "source": "everything-http",
            }
        )
    return results


def search_everything(
    query: str,
    limit: int = 100,
    base_url: str | None = None,
    timeout_sec: float = 5.0,
) -> list[dict[str, Any]]:
    url = build_everything_url(
        base_url or resolve_everything_base_url(),
        query=query,
        limit=limit,
    )
    try:
        response = requests.get(urlunparse(url), timeout=timeout_sec)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise EverythingHttpError(f"Everything HTTP is not reachable: {exc}") from exc
    except ValueError as exc:
        raise EverythingHttpError("Everything HTTP did not return JSON") from exc

    if not isinstance(payload, dict):
        raise EverythingHttpError("Everything HTTP JSON root was not an object")
    return parse_everything_results(payload)


def _parse_int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _format_date_modified(value: Any) -> str:
    if value in (None, ""):
        return ""
    raw = str(value).strip()
    try:
        numeric = float(raw)
    except ValueError:
        return raw
    if numeric > 10_000_000_000_000_000:
        unix_seconds = (numeric - 116_444_736_000_000_000) / 10_000_000
        return datetime.fromtimestamp(unix_seconds).strftime("%Y-%m-%d %H:%M:%S")
    if numeric > 1_000_000_000:
        return datetime.fromtimestamp(numeric).strftime("%Y-%m-%d %H:%M:%S")
    return raw
