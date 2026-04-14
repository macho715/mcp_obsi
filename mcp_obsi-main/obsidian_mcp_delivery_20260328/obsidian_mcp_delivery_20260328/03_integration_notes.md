# 통합 메모

## 1. 어떤 클라이언트가 어떤 방식으로 붙는가

| 클라이언트 | 로컬 localhost 가능 | public HTTPS 필요 | 비고 |
|---|---:|---:|---|
| Cursor | 예 | 아니오 | stdio / SSE / Streamable HTTP 지원 |
| Claude Code | 예 | 아니오 | 로컬/원격 MCP 모두 가능 |
| OpenAI Responses API | 아니오 | 예 | remote MCP tool |
| Anthropic Messages API | 아니오 | 예 | MCP connector, tool calls only |

---

## 2. OpenAI 예시 개념

```python
from openai import OpenAI
import os

client = OpenAI()

resp = client.responses.create(
    model="gpt-5",
    input="최근 project_fact 메모를 찾아 요약해줘.",
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
```

---

## 3. Anthropic 예시 개념

```python
import os
import anthropic

client = anthropic.Anthropic()

resp = client.beta.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=800,
    betas=["mcp-client-2025-04-04"],
    messages=[
        {"role": "user", "content": "최근 decision 메모를 찾아줘."}
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

print(resp.content)
```

---

## 4. 설계 원칙

- 저장은 Markdown이 정본
- 검색은 SQLite 인덱스 활용
- write는 보수적 승인
- read는 넓게 열고 write는 좁게 연다
- OpenAI/Anthropic API 연동은 public HTTPS 이후
