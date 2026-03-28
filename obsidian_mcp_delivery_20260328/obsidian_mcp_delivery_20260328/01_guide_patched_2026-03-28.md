# guide.md 패치본 (2026-03-28)

## 1. 결론

원래 가이드의 큰 구조는 맞다.

- **Obsidian Vault = SSOT**
- **FastAPI + FastMCP = 공용 기억 API**
- **SQLite = 검색/인덱스**
- **ChatGPT / Claude / Cursor = 동일 MCP 서버 소비자**

다만 2026-03-28 기준으로 아래 항목은 반드시 최신값으로 수정하는 편이 안전하다.

---

## 2. 원본 대비 수정 포인트

### 2.1 Anthropic MCP beta header 수정

원본 문서의 `mcp-client-2025-11-20` 값은 최신 공식 문서 기준과 다르다.

**권장 최신값**
- `anthropic-beta: mcp-client-2025-04-04`

Python SDK를 쓸 때는 아래처럼 `beta.messages.create(..., betas=[...])` 형태로 쓰는 편이 낫다.

```python
import anthropic

client = anthropic.Anthropic()

resp = client.beta.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=800,
    betas=["mcp-client-2025-04-04"],
    messages=[{"role": "user", "content": "최근 의사결정 메모를 찾아줘"}],
    mcp_servers=[
        {
            "type": "url",
            "url": "https://your-public-domain.example.com/mcp",
            "name": "obsidian-memory",
            "authorization_token": "YOUR_TOKEN",
        }
    ],
)
print(resp.content)
```

### 2.2 Anthropic 제한사항 명시 강화

Anthropic Messages API MCP connector는 현재 **tool calls only**다.

즉 이번 MVP는:
- tools 중심 설계
- resources/prompts는 서버 쪽에 두더라도 Claude Messages API 소비 기준으로는 필수 아님
- 문서/설명/프롬프트는 보조 기능으로 취급

### 2.3 OpenAI 문서 표현 최신화

기존 `ChatGPT Apps·deep research·API integration` 방향은 맞다.
다만 최신 공식 문서 기준으로 표현을 아래처럼 정리하는 편이 명확하다.

- **Responses API**에서 `type: "mcp"` 도구로 remote MCP server 사용 가능
- remote MCP server는 **Streamable HTTP 또는 HTTP/SSE** transport 지원 필요
- OpenAI는 자체 문서용 MCP 서버도 공개 운영 중
- ChatGPT 쪽은 **Developer mode beta**에서 full MCP client access를 제공

### 2.4 “공개 HTTP 필요” 범위 구분

이 부분은 헷갈리기 쉬워서 구분해서 써야 한다.

#### public HTTP가 필요한 경우
- OpenAI Responses API
- Anthropic Messages API MCP connector
- ChatGPT Developer mode로 외부 remote MCP를 붙일 때

#### public HTTP가 꼭 필요하지 않은 경우
- Cursor Editor / Cursor CLI
- Claude Code
- 로컬 테스트용 Inspector
- 같은 머신 안에서 붙는 stdio 또는 localhost HTTP

즉,
- **개발 단계**: localhost FastAPI/FastMCP로 충분
- **ChatGPT/Anthropic API 연동 단계**: public HTTPS endpoint 필요

### 2.5 MCP Python SDK 버전 주의

현재 공식 Python SDK 저장소 `main` 브랜치는 v2(pre-alpha) 문맥이 섞여 있다.
운영용은 **v1.x 문서/코드 기준**으로 잡는 편이 안전하다.

실무 권장:
- 초기 MVP: `mcp[cli]` + FastMCP v1.x 스타일
- v2 정식 안정화 후 업그레이드 검토

### 2.6 Streamable HTTP 기본값 정리

기존 가이드 방향은 맞다. 다만 운영 기준 문구를 아래처럼 더 명확히 쓰는 편이 좋다.

- 운영 기본 transport: **Streamable HTTP**
- SSE는 호환용으로 이해
- 신규 배포는 가능하면 Streamable HTTP 기준으로 맞춘다

### 2.7 Cursor 최신 규칙 체계 반영

Cursor 쪽은 예전 `.cursorrules`만 쓰는 방식보다 아래가 더 최신이다.

우선순위:
1. `.cursor/rules/*.mdc`
2. `AGENTS.md`
3. `.cursorrules`는 레거시

즉 Obsidian 메모리 워크플로를 Cursor에 녹일 때는
- 프로젝트 규칙은 `.cursor/rules/`
- 보편 지침은 `AGENTS.md`
조합이 더 적합하다.

### 2.8 Obsidian 자동화 범위 확장

원본은 Obsidian URI 중심인데, 최신 기준으로는 **Obsidian CLI**도 같이 고려할 가치가 있다.

가능한 자동화 선택지:
- 파일 직접 쓰기: 가장 단순하고 안정적
- `obsidian://new`, `obsidian://daily`, `append`
- `obsidian` CLI의 `daily:append`, `read`, `search`

실무 우선순위는 아래를 권장한다.

1. **파일 직접 쓰기**
2. URI/CLI는 보조 자동화
3. 플러그인 의존성은 최소화

---

## 3. 권장 최종 아키텍처

```text
Obsidian Vault (Markdown SSOT)
├─ 10_Daily/
├─ 20_AI_Memory/
└─ 90_System/

FastAPI + FastMCP
├─ /healthz
├─ /mcp
├─ bearer auth
└─ logging

SQLite
├─ metadata index
└─ text search

Clients
├─ Cursor (local or remote MCP)
├─ Claude Code (local or remote MCP)
├─ OpenAI Responses API (public remote MCP)
└─ Anthropic Messages API MCP connector (public remote MCP)
```

---

## 4. 권장 툴 목록

### 핵심 툴
- `search_memory`
- `save_memory`
- `get_memory`
- `list_recent_memories`
- `update_memory`

### 호환용 래퍼
- `search`
- `fetch`

---

## 5. 보안 권장

- 외부 배포 시 **HTTPS 필수**
- 최소한 **Bearer token** 보호
- 로그에 note body 전체를 남기지 말 것
- 민감 메모는 `sensitivity: p2_masked` 이상으로 구분
- `search/fetch`는 read-only로 운용
- `save/update`는 별도 승인 흐름 또는 Conversation 단위 승인 권장

---

## 6. 구현 방향

이 패치본 기준으로 바로 구현 가능한 MVP는 다음과 같다.

- FastAPI 앱
- FastMCP 서버 mount
- Markdown front matter 저장
- SQLite 인덱스
- Cursor/Claude/OpenAI/Anthropic 예제 클라이언트
- Windows PowerShell 실행 스크립트
- `~/.cursor/mcp.json` 예시 포함

---

## 7. 추천 다음 단계

1. 로컬에서 FastAPI/FastMCP MVP 실행
2. Cursor에서 로컬 MCP 연결
3. Obsidian Vault에 실제 메모 쓰기/검색 검증
4. public HTTPS 노출
5. OpenAI / Anthropic API와 연결
6. 승인 정책 및 masking 추가
