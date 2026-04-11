# Claude MCP

```mermaid
flowchart LR
    Claude["Claude / Claude Code / Messages API"] --> Read["/claude-mcp"]
    ClaudeAuth["Authenticated Claude client"] --> Write["/claude-mcp-write"]
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

이 문서는 Claude용 specialist MCP 경로 2개를 다룬다.

- public read-only route
- authenticated write-capable sibling route

## Tool Surface

### Read-only route `/claude-mcp`

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

### Write-capable sibling `/claude-mcp-write`

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

## Hosted Route

- read-only:
  - `https://mcp-server-production-90cb.up.railway.app/claude-mcp`
  - auth:
    - `No Bearer Authentication`
    - deployment에 따라 host/origin allowlist는 적용될 수 있음
  - verification:
    - `/claude-healthz` -> `200` (liveness only)
    - direct route/tool probe: `search`, `fetch`
    - no-auth read-only verification passed
- write-capable sibling:
  - `https://mcp-server-production-90cb.up.railway.app/claude-mcp-write`
  - auth:
    - `Authorization: Bearer <CLAUDE_MCP_WRITE_TOKEN or MCP_API_TOKEN>`
  - verification:
    - `/claude-write-healthz` -> `200` (liveness only)
    - unauthenticated route probe -> `401`
    - authenticated direct tool verification passed

## Claude Usage

Anthropic MCP connector docs 기준:

- remote MCP server must be public HTTP(S)
- Streamable HTTP and SSE are supported
- currently only tool calls are supported

So the public route stays read-only and tool-only, while the sibling route carries authenticated writes.

## Registration

- Claude Code add command:
  - `claude mcp add --transport http obsidian-memory-claude https://mcp-server-production-90cb.up.railway.app/claude-mcp`
- one-shot PowerShell registration script:
  - `powershell -ExecutionPolicy Bypass -File .\scripts\register_claude_mcp.ps1`

## Verification Command

```powershell
python scripts\verify_specialist_mcp_write.py --server-url https://mcp-server-production-90cb.up.railway.app/claude-mcp-write/ --token <TOKEN> --profile claude
```

현재 코드 기준으로 위 verifier는 `save_memory/get_memory/update_memory`뿐 아니라 `sync_wiki_index`, `append_wiki_log`, `lint_wiki`까지 함께 점검하도록 확장됐다. live production 결과는 별도 evidence에 기록해야 한다.

OAuth-capable route operator verification:
