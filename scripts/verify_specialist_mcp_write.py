from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

SPECIALIST_PROFILES = {
    "chatgpt": {
        "tool_set": [
            "search",
            "fetch",
            "list_recent_memories",
            "save_memory",
            "get_memory",
            "update_memory",
            "sync_wiki_index",
            "append_wiki_log",
            "write_wiki_page",
            "lint_wiki",
            "reconcile_conflict",
        ],
        "title_prefix": "ChatGPT Specialist Write Check",
        "content_prefix": "ChatGPT specialist write verification",
        "tags": ["production", "verification", "specialist-write", "chatgpt"],
    },
    "claude": {
        "tool_set": [
            "search",
            "fetch",
            "list_recent_memories",
            "save_memory",
            "get_memory",
            "update_memory",
            "sync_wiki_index",
            "append_wiki_log",
            "write_wiki_page",
            "lint_wiki",
            "reconcile_conflict",
        ],
        "title_prefix": "Claude Specialist Write Check",
        "content_prefix": "Claude specialist write verification",
        "tags": ["production", "verification", "specialist-write", "claude"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify authenticated specialist MCP write route.")
    parser.add_argument("--server-url", default=os.getenv("MCP_SERVER_URL"), required=False)
    parser.add_argument("--token", default=os.getenv("MCP_BEARER_TOKEN"), required=False)
    parser.add_argument("--profile", choices=sorted(SPECIALIST_PROFILES), required=True)
    return parser.parse_args()


def parse_tool_payload(result) -> dict:
    if getattr(result, "structuredContent", None) is not None:
        payload = result.structuredContent
        if isinstance(payload, dict) and isinstance(payload.get("result"), str):
            try:
                return json.loads(payload["result"])
            except Exception:
                return payload
        return payload

    content = getattr(result, "content", None) or []
    if not content:
        raise RuntimeError("tool result contained no structuredContent or text content")

    text = getattr(content[0], "text", None)
    if not text:
        raise RuntimeError("tool result text payload missing")

    return json.loads(text)


async def run_flow(server_url: str, token: str, profile_name: str) -> dict:
    profile = SPECIALIST_PROFILES[profile_name]
    normalized_url = server_url.rstrip("/") + "/"
    now = datetime.now(UTC)
    suffix = now.strftime("%Y%m%d-%H%M%S")
    title = f"{profile['title_prefix']} {suffix}"
    content = f"{profile['content_prefix']} at {now.isoformat()}."
    rollback_tags = [*profile["tags"], "rollback-archived"]

    headers = {
        "Authorization": token if token.startswith("Bearer ") else f"Bearer {token}",
        "Accept": "text/event-stream",
    }

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        async with streamable_http_client(normalized_url, http_client=client) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                if tool_names != profile["tool_set"]:
                    raise RuntimeError(f"unexpected tool set: {tool_names}")

                save_result = await session.call_tool(
                    "save_memory",
                    {
                        "memory_type": "decision",
                        "title": title,
                        "content": content,
                        "source": "manual",
                        "project": "production",
                        "tags": profile["tags"],
                        "append_daily": False,
                    },
                )
                save_data = parse_tool_payload(save_result)
                memory_id = save_data["id"]

                recent_data = parse_tool_payload(
                    await session.call_tool("list_recent_memories", {"limit": 3})
                )
                fetch_data = parse_tool_payload(await session.call_tool("fetch", {"id": memory_id}))
                get_data = parse_tool_payload(
                    await session.call_tool("get_memory", {"memory_id": memory_id})
                )
                search_data = parse_tool_payload(
                    await session.call_tool("search", {"query": title})
                )
                wiki_index_data = parse_tool_payload(
                    await session.call_tool("sync_wiki_index", {"limit": 10})
                )
                wiki_log_data = parse_tool_payload(
                    await session.call_tool(
                        "append_wiki_log",
                        {
                            "message": f"{profile_name} specialist write verification",
                            "category": "verification",
                            "related_ids": [memory_id],
                        },
                    )
                )
                wiki_lint_data = parse_tool_payload(await session.call_tool("lint_wiki", {}))
                rollback_data = parse_tool_payload(
                    await session.call_tool(
                        "update_memory",
                        {
                            "memory_id": memory_id,
                            "tags": rollback_tags,
                            "status": "archived",
                        },
                    )
                )
                get_after_rollback = parse_tool_payload(
                    await session.call_tool("get_memory", {"memory_id": memory_id})
                )

                if save_data.get("status") != "saved":
                    raise RuntimeError("save_memory did not return status=saved")
                if not recent_data.get("results"):
                    raise RuntimeError("list_recent_memories returned no items")
                if fetch_data.get("id") != memory_id:
                    raise RuntimeError("fetch returned wrong id")
                if get_data.get("id") != memory_id:
                    raise RuntimeError("get_memory returned wrong id")
                if not search_data.get("results"):
                    raise RuntimeError("search did not find the newly saved note")
                if wiki_index_data.get("status") != "synced":
                    raise RuntimeError("sync_wiki_index did not return status=synced")
                if wiki_log_data.get("status") != "appended":
                    raise RuntimeError("append_wiki_log did not return status=appended")
                if wiki_lint_data.get("status") != "completed":
                    raise RuntimeError("lint_wiki did not return status=completed")
                if rollback_data.get("status") != "updated":
                    raise RuntimeError("update_memory did not archive the note")
                if get_after_rollback.get("status") != "archived":
                    raise RuntimeError("archived status not persisted after rollback")

                return {
                    "tools": tool_names,
                    "saved": save_data,
                    "recent_after_save": recent_data,
                    "fetch_after_save": fetch_data,
                    "get_after_save": get_data,
                    "search_after_save": search_data,
                    "wiki_index_sync": wiki_index_data,
                    "wiki_log_append": wiki_log_data,
                    "wiki_lint": wiki_lint_data,
                    "rollback": rollback_data,
                    "get_after_rollback": get_after_rollback,
                }


def main() -> None:
    args = parse_args()
    if not args.server_url:
        raise SystemExit("--server-url or MCP_SERVER_URL is required")
    if not args.token:
        raise SystemExit("--token or MCP_BEARER_TOKEN is required")

    result = asyncio.run(run_flow(args.server_url, args.token, args.profile))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(str(exc), file=sys.stderr)
        raise
