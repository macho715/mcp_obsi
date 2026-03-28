from __future__ import annotations

import os

import anthropic


def main() -> None:
    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=800,
        betas=["mcp-client-2025-04-04"],
        messages=[
            {
                "role": "user",
                "content": "최근 project_fact 메모를 찾아 간단히 요약해줘.",
            }
        ],
        mcp_servers=[
            {
                "type": "url",
                "url": os.environ["MCP_SERVER_URL"],
                "name": "obsidian-memory",
                "authorization_token": os.environ["MCP_BEARER_TOKEN"],
            }
        ],
    )
    print(response.content)


if __name__ == "__main__":
    main()
