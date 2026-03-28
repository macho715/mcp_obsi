from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

DEFAULT_EXPECTED_TITLE = "Railway Preview Decision"
DEFAULT_RAW_EXCLUSION_QUERY = "raw conversation body only"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify live read-only MCP behavior.")
    parser.add_argument("--server-url", default=os.getenv("MCP_SERVER_URL"), required=False)
    parser.add_argument("--token", default=os.getenv("MCP_BEARER_TOKEN"), required=False)
    parser.add_argument("--expected-title", default=DEFAULT_EXPECTED_TITLE)
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


async def run_checks(
    server_url: str, token: str | None, expected_title: str, raw_exclusion_query: str
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
                memory_search = await session.call_tool(
                    "search_memory", {"query": expected_title, "limit": 5}
                )
                memory_search_data = parse_tool_payload(memory_search)
                raw_search = await session.call_tool(
                    "search_memory", {"query": raw_exclusion_query, "limit": 5}
                )
                raw_search_data = parse_tool_payload(raw_search)
                wrapper_search = await session.call_tool("search", {"query": expected_title})
                wrapper_search_data = parse_tool_payload(wrapper_search)

                memory_hits = memory_search_data["results"]
                if not memory_hits:
                    raise RuntimeError("search_memory returned no normalized hits")
                memory_id = memory_hits[0]["id"]

                get_result = await session.call_tool("get_memory", {"memory_id": memory_id})
                get_result_data = parse_tool_payload(get_result)
                fetch_result = await session.call_tool("fetch", {"id": memory_id})
                fetch_result_data = parse_tool_payload(fetch_result)

                summary = {
                    "tools": tool_names,
                    "recent": recent_data,
                    "search_memory": memory_search_data,
                    "search_raw": raw_search_data,
                    "search_wrapper": wrapper_search_data,
                    "get_memory": get_result_data,
                    "fetch": fetch_result_data,
                }

                titles = [item["title"] for item in memory_hits]
                if expected_title not in titles:
                    raise RuntimeError("expected normalized memory title not found")
                if raw_search_data["results"]:
                    raise RuntimeError("raw archive query leaked into normalized search")
                if fetch_result_data.get("id") != memory_id:
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
