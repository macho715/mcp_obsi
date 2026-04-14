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

WRITE_PROFILES = {
    "preview-write-once": {
        "label": "preview",
        "project": "preview",
        "base_tags": ["preview", "verification", "write-check"],
        "initial_title_prefix": "Railway Preview Write Check",
        "updated_title_prefix": "Railway Preview Write Check Updated",
        "initial_content_prefix": "Initial preview write verification",
        "updated_content_prefix": "Updated preview write verification",
    },
    "production-write-once": {
        "label": "production",
        "project": "production",
        "base_tags": ["production", "verification", "write-check"],
        "initial_title_prefix": "Railway Production Write Check",
        "updated_title_prefix": "Railway Production Write Check Updated",
        "initial_content_prefix": "Initial production write verification",
        "updated_content_prefix": "Updated production write verification",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify one live save/update MCP write flow.")
    parser.add_argument("--server-url", default=os.getenv("MCP_SERVER_URL"), required=False)
    parser.add_argument("--token", default=os.getenv("MCP_BEARER_TOKEN"), required=False)
    parser.add_argument(
        "--confirm",
        required=True,
        help="Must be exactly preview-write-once or production-write-once.",
    )
    return parser.parse_args()


def resolve_profile(confirm: str) -> dict:
    try:
        return WRITE_PROFILES[confirm]
    except KeyError as exc:
        raise SystemExit(
            "--confirm must be exactly preview-write-once or production-write-once"
        ) from exc


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


async def run_flow(server_url: str, token: str, profile: dict) -> dict:
    normalized_url = server_url.rstrip("/") + "/"
    now = datetime.now(UTC)
    suffix = now.strftime("%Y%m%d-%H%M%S")
    initial_title = f"{profile['initial_title_prefix']} {suffix}"
    updated_title = f"{profile['updated_title_prefix']} {suffix}"
    initial_content = f"{profile['initial_content_prefix']} at {now.isoformat()}."
    updated_content = f"{profile['updated_content_prefix']} at {now.isoformat()}."
    rollback_tags = [*profile["base_tags"], "rollback-archived"]
    updated_tags = [*profile["base_tags"], "updated"]

    headers = {
        "Authorization": token if token.startswith("Bearer ") else f"Bearer {token}",
        "Accept": "text/event-stream",
    }

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        async with streamable_http_client(normalized_url, http_client=client) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                save_result = await session.call_tool(
                    "save_memory",
                    {
                        "memory_type": "decision",
                        "title": initial_title,
                        "content": initial_content,
                        "source": "manual",
                        "project": profile["project"],
                        "tags": profile["base_tags"],
                        "confidence": 0.81,
                        "append_daily": False,
                    },
                )
                save_data = parse_tool_payload(save_result)
                memory_id = save_data["id"]

                get_after_save = parse_tool_payload(
                    await session.call_tool("get_memory", {"memory_id": memory_id})
                )

                update_data = parse_tool_payload(
                    await session.call_tool(
                        "update_memory",
                        {
                            "memory_id": memory_id,
                            "title": updated_title,
                            "content": updated_content,
                            "tags": updated_tags,
                            "status": "active",
                        },
                    )
                )

                search_after_update = parse_tool_payload(
                    await session.call_tool("search_memory", {"query": updated_title, "limit": 5})
                )
                fetch_after_update = parse_tool_payload(
                    await session.call_tool("fetch", {"id": memory_id})
                )

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
                if update_data.get("status") != "updated":
                    raise RuntimeError("update_memory did not return status=updated")
                if rollback_data.get("status") != "updated":
                    raise RuntimeError("rollback archive update did not return status=updated")
                if get_after_save.get("title") != initial_title:
                    raise RuntimeError("saved title mismatch after get_memory")
                if not search_after_update.get("results"):
                    raise RuntimeError("updated title not found via search_memory")
                if fetch_after_update.get("id") != memory_id:
                    raise RuntimeError("fetch wrapper returned wrong id")
                if get_after_rollback.get("status") != "archived":
                    raise RuntimeError("rollback did not archive the memory")

                return {
                    "saved": save_data,
                    "get_after_save": get_after_save,
                    "updated": update_data,
                    "search_after_update": search_after_update,
                    "fetch_after_update": fetch_after_update,
                    "rollback": rollback_data,
                    "get_after_rollback": get_after_rollback,
                }


def main() -> None:
    args = parse_args()
    if not args.server_url:
        raise SystemExit("--server-url or MCP_SERVER_URL is required")
    if not args.token:
        raise SystemExit("--token or MCP_BEARER_TOKEN is required")
    profile = resolve_profile(args.confirm)

    result = asyncio.run(run_flow(args.server_url, args.token, profile))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(str(exc), file=sys.stderr)
        raise
