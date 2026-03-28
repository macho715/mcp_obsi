from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify ChatGPT-only read-only MCP profile.")
    parser.add_argument("--server-url", default=os.getenv("MCP_SERVER_URL"), required=False)
    parser.add_argument("--expected-title", default="RailwayProductionDecision")
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


async def run_checks(server_url: str, expected_title: str) -> dict:
    normalized_url = server_url.rstrip("/") + "/"
    headers = {"Accept": "text/event-stream"}

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        async with streamable_http_client(normalized_url, http_client=client) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                if tool_names != ["search", "fetch"]:
                    raise RuntimeError(f"unexpected tool set: {tool_names}")

                search_result = await session.call_tool("search", {"query": expected_title})
                search_data = parse_tool_payload(search_result)
                results = search_data["results"]
                if not results:
                    raise RuntimeError("search returned no results")

                memory_id = results[0]["id"]
                fetch_result = await session.call_tool("fetch", {"id": memory_id})
                fetch_data = parse_tool_payload(fetch_result)
                if fetch_data.get("id") != memory_id:
                    raise RuntimeError("fetch returned wrong id")

                return {
                    "tools": tool_names,
                    "search": search_data,
                    "fetch": fetch_data,
                }


def main() -> None:
    args = parse_args()
    if not args.server_url:
        raise SystemExit("--server-url or MCP_SERVER_URL is required")

    result = asyncio.run(run_checks(args.server_url, args.expected_title))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(str(exc), file=sys.stderr)
        raise
