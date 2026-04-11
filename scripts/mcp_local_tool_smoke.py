"""Live MCP Streamable HTTP smoke: tools + read paths + discoverability surfaces.

- mode=full: /mcp style (search_memory, list_recent_memories, get_memory, fetch).
- mode=wrapper: ChatGPT/Claude read-only (search + fetch + list_recent_memories).
- also reports resource and prompt counts so read-side capability drift is visible.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Literal

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

Mode = Literal["full", "wrapper"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MCP mount smoke (tools + read path).")
    p.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Origin without trailing path",
    )
    p.add_argument("--path", default="/mcp/", help="MCP mount path (ignored if --all-mounts)")
    p.add_argument(
        "--token",
        default=os.getenv("MCP_API_TOKEN"),
        help="Bearer for /mcp (omit for RO mounts)",
    )
    p.add_argument(
        "--main-token",
        default=None,
        help="Override bearer for /mcp only when using --all-mounts (e.g. production token)",
    )
    p.add_argument("--search-query", default="gemma", help="Search query")
    p.add_argument("--label", default="main", help="Label for JSON output")
    p.add_argument(
        "--require-read-hit",
        action="store_true",
        help="Return non-zero when the chosen query does not exercise search/fetch or get/fetch.",
    )
    p.add_argument(
        "--all-mounts",
        action="store_true",
        help="Smoke /mcp (with token), /chatgpt-mcp, /claude-mcp on base-url",
    )
    return p.parse_args()


def parse_tool_payload(result) -> dict:
    if getattr(result, "structuredContent", None) is not None:
        return result.structuredContent
    content = getattr(result, "content", None) or []
    if not content:
        raise RuntimeError("tool result had no structured or text content")
    text = getattr(content[0], "text", None)
    if not text:
        raise RuntimeError("tool text missing")
    return json.loads(text)


def result_items(payload: dict) -> list[dict]:
    for key in ("results", "items", "memories"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


async def smoke_one(
    label: str,
    origin: str,
    path: str,
    token: str | None,
    search_query: str,
    *,
    mode: Mode,
) -> dict:
    path = path if path.startswith("/") else f"/{path}"
    path = path.rstrip("/") + "/"
    url = origin.rstrip("/") + path
    headers: dict[str, str] = {"Accept": "text/event-stream"}
    if token:
        headers["Authorization"] = token if token.startswith("Bearer ") else f"Bearer {token}"

    async with httpx.AsyncClient(headers=headers, timeout=45.0) as client:
        async with streamable_http_client(url, http_client=client) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = sorted(t.name for t in tools.tools)
                resources_result = await session.list_resources()
                prompts_result = await session.list_prompts()
                resource_uris = sorted(
                    str(resource.uri) for resource in resources_result.resources
                )
                prompt_names = sorted(prompt.name for prompt in prompts_result.prompts)

                if mode == "wrapper":
                    recent = parse_tool_payload(
                        await session.call_tool("list_recent_memories", {"limit": 3})
                    )
                    recent_items = result_items(recent)
                    search = parse_tool_payload(
                        await session.call_tool("search", {"query": search_query})
                    )
                    hits = search.get("results") or []
                    extra = False
                    if hits:
                        mid = hits[0]["id"]
                        parse_tool_payload(await session.call_tool("fetch", {"id": mid}))
                        extra = True
                    return {
                        "label": label,
                        "url": url,
                        "mode": mode,
                        "tools": names,
                        "resource_count": len(resource_uris),
                        "resources": resource_uris,
                        "prompt_count": len(prompt_names),
                        "prompts": prompt_names,
                        "list_recent_ok": any(
                            k in recent for k in ("results", "items", "memories")
                        ),
                        "recent_count": len(recent_items),
                        "recent_titles": [item.get("title") for item in recent_items[:3]],
                        "search_hits": len(hits),
                        "read_path_verified": extra,
                        "fetch_called": extra,
                    }

                recent = parse_tool_payload(
                    await session.call_tool("list_recent_memories", {"limit": 3})
                )
                recent_items = result_items(recent)
                search = parse_tool_payload(
                    await session.call_tool(
                        "search_memory",
                        {"query": search_query, "limit": 5},
                    )
                )
                hits = search.get("results") or []
                extra = False
                if hits:
                    mid = hits[0]["id"]
                    parse_tool_payload(await session.call_tool("get_memory", {"memory_id": mid}))
                    if "fetch" in names:
                        parse_tool_payload(await session.call_tool("fetch", {"id": mid}))
                    extra = True

                return {
                    "label": label,
                    "url": url,
                    "mode": mode,
                    "tools": names,
                    "resource_count": len(resource_uris),
                    "resources": resource_uris,
                    "prompt_count": len(prompt_names),
                    "prompts": prompt_names,
                    "list_recent_ok": any(k in recent for k in ("results", "items", "memories")),
                    "recent_count": len(recent_items),
                    "recent_titles": [item.get("title") for item in recent_items[:3]],
                    "search_hits": len(hits),
                    "read_path_verified": extra,
                    "get_fetch_called": extra,
                }


def _required_tools(mode: Mode) -> set[str]:
    if mode == "wrapper":
        return {"search", "fetch", "list_recent_memories"}
    return {"search_memory", "list_recent_memories", "get_memory"}


async def async_main() -> int:
    args = parse_args()
    origin = args.base_url
    if args.all_mounts:
        main_tok = args.main_token if args.main_token is not None else args.token
        batch: list[tuple[str, str, str | None, Mode]] = [
            ("main", "/mcp/", main_tok, "full"),
            ("chatgpt-ro", "/chatgpt-mcp/", None, "wrapper"),
            ("claude-ro", "/claude-mcp/", None, "wrapper"),
        ]
        results = [
            await smoke_one(label, origin, path, tok, args.search_query, mode=mode)
            for label, path, tok, mode in batch
        ]
        print(json.dumps(results, ensure_ascii=False, indent=2))
        code = 0
        for out in results:
            need = _required_tools(out["mode"])
            have = set(out["tools"])
            if not need.issubset(have):
                print(f"[{out['label']}] missing tools: {need - have}", file=sys.stderr)
                code = 1
            if args.require_read_hit and not out.get("read_path_verified", False):
                print(
                    f"[{out['label']}] read path not verified for query={args.search_query!r}",
                    file=sys.stderr,
                )
                code = 1
        return code

    mode: Mode = "wrapper" if "chatgpt-mcp" in args.path or "claude-mcp" in args.path else "full"
    out = await smoke_one(args.label, origin, args.path, args.token, args.search_query, mode=mode)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    required = _required_tools(mode)
    have = set(out["tools"])
    if not required.issubset(have):
        print(f"Missing tools: {required - have}", file=sys.stderr)
        return 1
    if args.require_read_hit and not out.get("read_path_verified", False):
        print(f"Read path not verified for query={args.search_query!r}", file=sys.stderr)
        return 1
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
