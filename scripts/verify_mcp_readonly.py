from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

DEFAULT_RAW_EXCLUSION_QUERY = "raw conversation body only"
DEFAULT_BEARER_TOKEN = os.getenv("MCP_BEARER_TOKEN") or os.getenv("MCP_PRODUCTION_BEARER_TOKEN")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify live read-only MCP behavior.")
    parser.add_argument("--server-url", default=os.getenv("MCP_SERVER_URL"), required=False)
    parser.add_argument("--token", default=DEFAULT_BEARER_TOKEN, required=False)
    parser.add_argument("--expected-title", default=None)
    parser.add_argument("--raw-exclusion-query", default=DEFAULT_RAW_EXCLUSION_QUERY)
    return parser.parse_args()


def parse_tool_payload(result) -> dict:
    if getattr(result, "structuredContent", None) is not None:
        return result.structuredContent

    content = getattr(result, "content", None) or []
    if not content:
        raise RuntimeError("tool result contained no structuredContent or text content")

    text = getattr(content[0], "text", None)
    if not text:
        raise RuntimeError("tool result text payload missing")

    return json.loads(text)


def result_items(payload: dict) -> list[dict]:
    for key in ("results", "items", "memories"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def find_matching_item(
    items: list[dict], *, expected_id: str | None, expected_title: str
) -> dict | None:
    if expected_id:
        match = next((item for item in items if item.get("id") == expected_id), None)
        if match is not None:
            return match
    title_matches = [item for item in items if item.get("title") == expected_title]
    if len(title_matches) > 1:
        raise RuntimeError(
            "multiple memories matched the expected title; pass a unique target instead"
        )
    return title_matches[0] if title_matches else None


async def run_checks(
    server_url: str, token: str | None, expected_title: str | None, raw_exclusion_query: str
) -> dict:
    normalized_url = server_url.rstrip("/") + "/"
    headers = {"Accept": "text/event-stream"}
    if token:
        headers["Authorization"] = token if token.startswith("Bearer ") else f"Bearer {token}"

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        async with streamable_http_client(normalized_url, http_client=client) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]

                recent = await session.call_tool("list_recent_memories", {"limit": 5})
                recent_data = parse_tool_payload(recent)
                recent_items = result_items(recent_data)
                resolved_title = expected_title
                expected_memory_id = None
                if resolved_title is None:
                    if not recent_items:
                        raise RuntimeError(
                            "list_recent_memories returned no items; pass --expected-title "
                            "to verify an empty dataset explicitly"
                        )
                    resolved_title = recent_items[0]["title"]
                    expected_memory_id = recent_items[0].get("id")
                memory_search = await session.call_tool(
                    "search_memory", {"query": resolved_title, "limit": 5}
                )
                memory_search_data = parse_tool_payload(memory_search)
                raw_search = await session.call_tool(
                    "search_memory", {"query": raw_exclusion_query, "limit": 5}
                )
                raw_search_data = parse_tool_payload(raw_search)
                wrapper_search = await session.call_tool("search", {"query": resolved_title})
                wrapper_search_data = parse_tool_payload(wrapper_search)
                wrapper_hits = result_items(wrapper_search_data)
                if not wrapper_hits:
                    raise RuntimeError("wrapper search returned no results")
                wrapper_match = find_matching_item(
                    wrapper_hits,
                    expected_id=expected_memory_id,
                    expected_title=resolved_title,
                )
                if wrapper_match is None:
                    raise RuntimeError("wrapper search did not return the expected memory")

                memory_hits = result_items(memory_search_data)
                if not memory_hits:
                    raise RuntimeError("search_memory returned no normalized hits")
                memory_match = find_matching_item(
                    memory_hits,
                    expected_id=expected_memory_id,
                    expected_title=resolved_title,
                )
                if memory_match is None:
                    raise RuntimeError("search_memory did not return the expected memory")
                memory_id = memory_match["id"]

                get_result = await session.call_tool("get_memory", {"memory_id": memory_id})
                get_result_data = parse_tool_payload(get_result)
                fetch_result = await session.call_tool("fetch", {"id": wrapper_match["id"]})
                fetch_result_data = parse_tool_payload(fetch_result)

                summary = {
                    "tools": tool_names,
                    "resolved_title": resolved_title,
                    "recent": recent_data,
                    "search_memory": memory_search_data,
                    "search_raw": raw_search_data,
                    "search_wrapper": wrapper_search_data,
                    "get_memory": get_result_data,
                    "fetch": fetch_result_data,
                }

                titles = [item["title"] for item in memory_hits]
                if resolved_title not in titles and expected_memory_id is None:
                    raise RuntimeError("expected normalized memory title not found")
                if raw_search_data["results"]:
                    raise RuntimeError("raw archive query leaked into normalized search")
                if wrapper_match["id"] != memory_id:
                    raise RuntimeError("wrapper search resolved a different memory id")
                if fetch_result_data.get("id") != wrapper_match["id"]:
                    raise RuntimeError("fetch wrapper did not resolve the expected memory id")

                return summary


def main() -> None:
    args = parse_args()
    if not args.server_url:
        raise SystemExit("--server-url or MCP_SERVER_URL is required")

    result = asyncio.run(
        run_checks(args.server_url, args.token, args.expected_title, args.raw_exclusion_query)
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(str(exc), file=sys.stderr)
        raise
