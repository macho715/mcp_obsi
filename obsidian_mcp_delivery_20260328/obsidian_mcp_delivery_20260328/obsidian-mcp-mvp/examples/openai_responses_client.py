from __future__ import annotations

import os

from openai import OpenAI


def main() -> None:
    client = OpenAI()

    resp = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5"),
        input="최근 decision 메모를 찾아 간단히 요약해줘.",
        tools=[
            {
                "type": "mcp",
                "server_label": "obsidian_memory",
                "server_description": "Obsidian memory MCP server",
                "server_url": os.environ["MCP_SERVER_URL"],
                "authorization": os.environ["MCP_BEARER_TOKEN"],
                "require_approval": "never",
            }
        ],
    )
    print(resp.output_text)


if __name__ == "__main__":
    main()
