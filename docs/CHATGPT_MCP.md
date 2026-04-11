# ChatGPT MCP

```mermaid
flowchart LR
    ChatGPT["ChatGPT app / developer mode"] --> Read["/chatgpt-mcp"]
    Operator["Authenticated client"] --> Write["/chatgpt-mcp-write"]
    Read --> Search["search"]
    Read --> Recent["list_recent_memories"]
    Read --> Fetch["fetch"]
    Write --> Recent
    Write --> Save["save_memory"]
    Write --> Get["get_memory"]
    Write --> Update["update_memory"]
    Search --> Vault["Obsidian memory store"]
    Fetch --> Vault
    Save --> Vault
    Get --> Vault
    Update --> Vault
```

## Archetype

`tool-only`

## Purpose

이 문서는 ChatGPT용 specialist MCP 경로 2개를 다룬다.

- public app-facing read-only route
- authenticated write-capable sibling route

## Tool Surface

### Read-only route `/chatgpt-mcp`

- `search`
- `list_recent_memories`
- `fetch`
- resources
  - `resource://wiki/index`
  - `resource://wiki/log/recent`
  - `resource://wiki/topic/{slug}`
  - `resource://schema/memory`
  - `resource://ops/verification/latest`
  - `resource://ops/routes/profile-matrix`
- prompts
  - `ingest_memory_to_wiki`
  - `reconcile_conflict`
  - `weekly_lint_report`
  - `summarize_recent_project_state`

주의:
- 모델이 recent/list 질문에서 실수로 `search`를 먼저 호출해도, date-only memory query나 `최근 메모` 같은 generic recent query는 recent browse 의도로 처리되도록 보정한다.

둘 다 read-only다.

### Write-capable sibling `/chatgpt-mcp-write`

- `search`
- `list_recent_memories`
- `fetch`
- `save_memory`
- `get_memory`
- `update_memory`
- `sync_wiki_index`
- `append_wiki_log`
- `write_wiki_page`
- `lint_wiki`
- `reconcile_conflict`

이 sibling route는 Bearer auth가 필요하다.

## Local Run

통합 runtime 기준:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

endpoint:

- `http://127.0.0.1:8000/chatgpt-mcp`
- `http://127.0.0.1:8000/chatgpt-mcp-write`

specialist-only dev script 기준:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-chatgpt-mcp-dev.ps1
```

endpoint:

- `http://127.0.0.1:8001/mcp`

## Hosted Route

- read-only:
  - `https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp`
  - auth:
    - `No Bearer Authentication`
    - deployment에 따라 host/origin allowlist는 적용될 수 있음
  - verification:
    - `/chatgpt-healthz` -> `200` (liveness only)
    - direct route/tool probe: `search`, `list_recent_memories`, `fetch`
    - no-auth read-only verification passed
- write-capable sibling:
  - `https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp-write`
  - auth:
    - `Authorization: Bearer <CHATGPT_MCP_WRITE_TOKEN or MCP_API_TOKEN>`
  - verification:
    - `/chatgpt-write-healthz` -> `200` (liveness only)
    - unauthenticated route probe -> `401`
    - authenticated direct tool verification passed

## App Creation Fields

- name:
  - `obsidian-memory-chatgpt`
- MCP server URL:
  - `https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp`
- authentication:
  - `No Authentication`
- description:
  - `Obsidian-backed read-only memory search, recent listing, and fetch for ChatGPT`

## Notes

- 기존 full MCP surface를 대체하지 않는다.
- ChatGPT app creation UI에는 현재 read-only route만 바로 연결한다.
- write-capable sibling route는 operator/integration path로 배포했다.
- OpenAI Developer Mode docs 기준 ChatGPT app은 `OAuth`, `No Authentication`, `Mixed Authentication`을 지원한다.
- 현재 repo는 ChatGPT write route를 bearer-gated sibling으로 먼저 구현했다.
- 따라서 ChatGPT app 안에서 실제 write까지 쓰려면 다음 단계에서 mixed-auth 또는 OAuth metadata/runtime을 추가해야 한다.
- standard `search` / `fetch` naming을 유지하고, recent/list 성격 질문은 `list_recent_memories`로 처리한다.

## Verification Command

```powershell
python scripts\verify_specialist_mcp_write.py --server-url https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp-write/ --token <TOKEN> --profile chatgpt
```

현재 코드 기준으로 위 verifier는 `save_memory/get_memory/update_memory`뿐 아니라 `sync_wiki_index`, `append_wiki_log`, `lint_wiki`까지 함께 점검하도록 확장됐다. live production 결과는 별도 evidence에 기록해야 한다.
