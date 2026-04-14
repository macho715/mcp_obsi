from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

DEFAULT_BEARER_TOKEN = os.getenv("MCP_BEARER_TOKEN") or os.getenv("MCP_PRODUCTION_BEARER_TOKEN")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Claude-only read-only MCP profile.")
    parser.add_argument("--server-url", default=os.getenv("MCP_SERVER_URL"), required=False)
    parser.add_argument("--expected-title", default=None)
    parser.add_argument("--token", default=DEFAULT_BEARER_TOKEN, required=False)
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


async def resolve_expected_memory(
    server_url: str, token: str | None, expected_title: str | None
) -> dict[str, str | None]:
    if expected_title:
        return {"id": None, "title": expected_title}

    headers = {
        "Accept": "application/json, text/event-stream",
    }
    if token:
        headers["Authorization"] = token if token.startswith("Bearer ") else f"Bearer {token}"
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        async with streamable_http_client(
            server_url.rstrip("/") + "/",
            http_client=client,
        ) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                recent = parse_tool_payload(
                    await session.call_tool("list_recent_memories", {"limit": 5})
                )
                items = result_items(recent)
                if not items:
                    raise RuntimeError("list_recent_memories returned no items on /mcp")
                return {"id": items[0].get("id"), "title": items[0]["title"]}


async def run_checks(server_url: str, expected_title: str | None, token: str | None) -> dict:
    normalized_url = server_url.rstrip("/") + "/"
    headers = {"Accept": "application/json, text/event-stream"}
    expected_memory = await resolve_expected_memory(server_url, token, expected_title)
    resolved_title = str(expected_memory["title"])

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        async with streamable_http_client(normalized_url, http_client=client) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                if tool_names != [
                    "search",
                    "fetch",
                    "list_recent_memories",
                    "search_wiki",
                    "fetch_wiki",
                ]:
                    raise RuntimeError(f"unexpected tool set: {tool_names}")

                recent_result = await session.call_tool("list_recent_memories", {"limit": 5})
                recent_data = parse_tool_payload(recent_result)
                recent_items = result_items(recent_data)
                if not recent_items:
                    raise RuntimeError("list_recent_memories returned no items")

                search_result = await session.call_tool("search", {"query": resolved_title})
                search_data = parse_tool_payload(search_result)
                results = search_data["results"]
                if not results:
                    raise RuntimeError("search returned no results")

                match = find_matching_item(
                    results,
                    expected_id=expected_memory["id"],
                    expected_title=resolved_title,
                )
                if match is None:
                    raise RuntimeError("search returned results but not the expected memory")

                memory_id = match["id"]
                fetch_result = await session.call_tool("fetch", {"id": memory_id})
                fetch_data = parse_tool_payload(fetch_result)
                if fetch_data.get("id") != memory_id:
                    raise RuntimeError("fetch returned wrong id")

                wiki_search_result = await session.call_tool(
                    "search_wiki",
                    {
                        "query": resolved_title,
                        "path_prefix": "wiki/analyses",
                        "limit": 3,
                    },
                )
                wiki_search_data = parse_tool_payload(wiki_search_result)
                wiki_results = result_items(wiki_search_data)
                wiki_fetch_data = None
                if wiki_results:
                    first = wiki_results[0]
                    wiki_fetch_result = await session.call_tool(
                        "fetch_wiki",
                        {"path": str(first["path"]).removesuffix(".md")},
                    )
                    wiki_fetch_data = parse_tool_payload(wiki_fetch_result)

                return {
                    "resolved_title": resolved_title,
                    "tools": tool_names,
                    "recent": recent_data,
                    "search": search_data,
                    "fetch": fetch_data,
                    "wiki_search": wiki_search_data,
                    "wiki_fetch": wiki_fetch_data,
                }


def main() -> None:
    args = parse_args()
    if not args.server_url:
        raise SystemExit("--server-url or MCP_SERVER_URL is required")

    result = asyncio.run(run_checks(args.server_url, args.expected_title, args.token))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(str(exc), file=sys.stderr)
        raise
