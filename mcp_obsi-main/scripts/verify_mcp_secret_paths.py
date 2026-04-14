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

SECRET_PROFILES = {
    "preview-secret-paths": {
        "label": "preview",
        "project": "preview",
        "base_tags": ["preview", "verification", "secret-probe"],
        "mixed_title_prefix": "Railway Preview Secret Probe Mixed",
        "reject_title_prefix": "Railway Preview Secret Probe Reject",
        "mixed_content_prefix": "Preview note",
    },
    "production-secret-paths": {
        "label": "production",
        "project": "production",
        "base_tags": ["production", "verification", "secret-probe"],
        "mixed_title_prefix": "Railway Production Secret Probe Mixed",
        "reject_title_prefix": "Railway Production Secret Probe Reject",
        "mixed_content_prefix": "Production note",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify live MCP masking/reject secret paths.")
    parser.add_argument("--server-url", default=os.getenv("MCP_SERVER_URL"), required=False)
    parser.add_argument("--token", default=os.getenv("MCP_BEARER_TOKEN"), required=False)
    parser.add_argument(
        "--confirm",
        required=True,
        help="Must be exactly preview-secret-paths or production-secret-paths.",
    )
    return parser.parse_args()


def resolve_profile(confirm: str) -> dict:
    try:
        return SECRET_PROFILES[confirm]
    except KeyError as exc:
        raise SystemExit(
            "--confirm must be exactly preview-secret-paths or production-secret-paths"
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

    try:
        return json.loads(text)
    except Exception:
        return {"_text": text}


async def run_flow(server_url: str, token: str, profile: dict) -> dict:
    normalized_url = server_url.rstrip("/") + "/"
    now = datetime.now(UTC)
    suffix = now.strftime("%Y%m%d-%H%M%S")
    mixed_title = f"{profile['mixed_title_prefix']} {suffix}"
    reject_title = f"{profile['reject_title_prefix']} {suffix}"
    rollback_tags = [*profile["base_tags"], "rollback-archived"]

    headers = {
        "Authorization": token if token.startswith("Bearer ") else f"Bearer {token}",
        "Accept": "text/event-stream",
    }

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        async with streamable_http_client(normalized_url, http_client=client) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                mixed_result = await session.call_tool(
                    "save_memory",
                    {
                        "memory_type": "decision",
                        "title": mixed_title,
                        "content": (
                            f"{profile['mixed_content_prefix']} with token=supersecret and "
                            "Bearer abcdefghijklmnop inside sentence"
                        ),
                        "source": "manual",
                        "project": profile["project"],
                        "tags": profile["base_tags"],
                        "append_daily": False,
                    },
                )
                mixed_payload = parse_tool_payload(mixed_result)
                if mixed_result.isError:
                    raise RuntimeError(f"mixed payload unexpectedly failed: {mixed_payload}")

                memory_id = mixed_payload["id"]
                mixed_readback = parse_tool_payload(
                    await session.call_tool("get_memory", {"memory_id": memory_id})
                )
                if "supersecret" in mixed_readback["content"]:
                    raise RuntimeError("mixed payload stored raw token value")
                if "[REDACTED]" not in mixed_readback["content"]:
                    raise RuntimeError("mixed payload was not masked")

                rollback = parse_tool_payload(
                    await session.call_tool(
                        "update_memory",
                        {
                            "memory_id": memory_id,
                            "tags": rollback_tags,
                            "status": "archived",
                        },
                    )
                )
                rollback_readback = parse_tool_payload(
                    await session.call_tool("get_memory", {"memory_id": memory_id})
                )
                if rollback_readback["status"] != "archived":
                    raise RuntimeError("mixed payload rollback did not archive the record")

                reject_result = await session.call_tool(
                    "save_memory",
                    {
                        "memory_type": "decision",
                        "title": reject_title,
                        "content": "Bearer abcdefghijklmnop",
                        "source": "manual",
                        "project": profile["project"],
                        "tags": profile["base_tags"],
                        "append_daily": False,
                    },
                )
                reject_payload = parse_tool_payload(reject_result)
                if not reject_result.isError:
                    raise RuntimeError("secret-only payload unexpectedly succeeded")

                reject_search = parse_tool_payload(
                    await session.call_tool("search_memory", {"query": reject_title, "limit": 5})
                )
                if reject_search["results"]:
                    raise RuntimeError(
                        "rejected payload appears to have persisted searchable state"
                    )

                return {
                    "mixed_save": mixed_payload,
                    "mixed_readback": mixed_readback,
                    "mixed_rollback": rollback,
                    "mixed_after_rollback": rollback_readback,
                    "reject_error": reject_payload,
                    "reject_search": reject_search,
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
