"""One-shot: MCP archive_raw + save_memory against local streamable HTTP. Ephemeral demo."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def _parse_tool_payload(result) -> dict:
    if getattr(result, "isError", False):
        parts = [getattr(c, "text", "") for c in (result.content or [])]
        raise RuntimeError("".join(parts).strip() or "tool error")
    if getattr(result, "structuredContent", None) is not None:
        return result.structuredContent
    content = getattr(result, "content", None) or []
    if not content:
        raise RuntimeError("tool result empty")
    text = getattr(content[0], "text", None)
    if not text:
        raise RuntimeError("tool result missing text")
    return json.loads(text)


async def main() -> None:
    base = sys.argv[1].rstrip("/") + "/"
    token = sys.argv[2]
    now = datetime.now(UTC)
    day = now.date().isoformat()
    mcp_id = f"convo-demo-fictional-{now.strftime('%Y%m%d-%H%M%S')}"
    fake_chat = "\n".join(
        [
            "## User",
            "가상 시나리오: MCP 풀라인 데모를 한 번에 돌려줘.",
            "",
            "## Assistant",
            "이 대화는 테스트용 가상 내용입니다. 저장 경로와 메모 ID만 확인하면 됩니다.",
        ]
    )
    headers = {
        "Authorization": token if token.startswith("Bearer ") else f"Bearer {token}",
        "Accept": "text/event-stream",
    }
    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        async with streamable_http_client(base, http_client=client) as streams:
            read_stream, write_stream, _ = streams
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                arch = _parse_tool_payload(
                    await session.call_tool(
                        "archive_raw",
                        {
                            "mcp_id": mcp_id,
                            "source": "cursor-demo-fictional",
                            "body_markdown": fake_chat,
                            "created_by": "fullline-demo",
                            "created_at_utc": now.isoformat().replace("+00:00", "Z"),
                            "conversation_date": day,
                            "project": "demo",
                            "tags": ["demo", "fictional", "fullline"],
                        },
                    )
                )
                mem = _parse_tool_payload(
                    await session.call_tool(
                        "save_memory",
                        {
                            "memory_type": "decision",
                            "title": "가상: MCP 데모 원샷 완료 기록",
                            "content": (
                                "fictional one-shot: raw archived, then pointer memory. "
                                "Cursor subagents/skills are separate from this MCP hop."
                            ),
                            "source": "manual",
                            "project": "demo",
                            "tags": ["demo", "pointer", "fictional"],
                            "raw_refs": [mcp_id],
                            "confidence": 0.77,
                            "append_daily": False,
                        },
                    )
                )
                out = {"archive_raw": arch, "save_memory": mem}
                print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
