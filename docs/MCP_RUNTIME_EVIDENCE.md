# MCP Runtime Evidence

```mermaid
flowchart LR
    Endpoint["/healthz + /mcp"] --> Transport["Public MCP transport"]
    Transport --> Tools["Read-only tool calls"]
    Tools --> Result["Normalized hit / raw exclusion"]
    Result --> Evidence["Verification evidence"]
```

Date: 2026-03-28

## Scope

read-first live MCP verification for the hybrid redesign.

## Environment

- local server URL: `http://127.0.0.1:8000/mcp/`
- auth: `Authorization: Bearer ${env:MCP_API_TOKEN}`
- transport: streamable HTTP

## Endpoint Checks

- `/healthz` -> `200`
- `/mcp` -> `307`
- `/mcp/` -> `400 Missing session ID`

이 조합은 현재 server path/mount가 살아 있고, session 없는 직접 GET에 대해 protocol-level error를 반환한다는 증거다.

## Cursor MCP Evidence

Current Cursor active config:

- `C:\Users\jichu\.cursor\mcp.json`

tool offerings 확인:

- `search_memory`
- `save_memory`
- `get_memory`
- `list_recent_memories`
- `update_memory`
- `search`
- `fetch`

추가 manual evidence:

- Cursor **Settings -> MCP**에서 `obsidian-memory-local = connected` 확인
- Cursor **Settings -> MCP**에서 `obsidian-memory-production = connected` 확인

## MCP Client Tool Calls

Python MCP client로 실제 호출한 결과:

- `list_recent_memories(limit=5)` -> normalized memory 1건 반환
- `search_memory(query='E2E hybrid decision')` -> normalized memory 1건 반환
- `search_memory(query='raw conversation body only')` -> `results: []`
- `search(query='E2E hybrid decision')` -> wrapper read result 1건 반환
- `get_memory(memory_id='MEM-20260328-120319-9019D9')` -> normalized memory 상세 반환
- `fetch(id='MEM-20260328-120319-9019D9')` -> wrapper fetch 상세 반환

## Conclusions

- raw archive note는 normalized search 대상이 아니다.
- normalized memory note는 live MCP read tool로 검색 가능하다.
- wrapper `search` / `fetch`는 현재도 동작한다.
- Cursor MCP는 현재 global config 기준으로 local + production 둘 다 connected 상태가 확인됐다.
- main `/mcp` write tool과 specialist write-capable sibling route는 이후 섹션에서 별도 검증 결과를 기록한다.

## Railway Preview Evidence

- selected preview URL: `https://mcp-server-production-1454.up.railway.app`
- deployment status: `SUCCESS`
- `/healthz` -> `200`
- `/mcp` -> `307` with `https://.../mcp/` redirect
- `/mcp/` -> `400 Missing session ID`
- isolated preview seed written:
  - raw: `mcp_raw/manual/2026-03-28/convo-railway-preview-seed.md`
  - memory: `20_AI_Memory/decision/2026/03/MEM-20260328-120319-ACEB90.md`
- live MCP read-only verification passed through Railway public HTTPS:
  - `list_recent_memories`
  - `search_memory`
  - `get_memory`
  - `search`
  - `fetch`
  - raw exclusion query returned empty results
- production stance:
  - preview and production are now split into separate Railway projects
  - Railway is the current production path

## Write-Tool Gate

Status: `verified once on Railway preview`

First live write verification result:

- command:
  - `python scripts/verify_mcp_write_once.py --server-url https://mcp-server-production-1454.up.railway.app/mcp/ --token <redacted> --confirm preview-write-once`
- memory created:
  - `MEM-20260328-145016-D57430`
- `save_memory` -> `status=saved`
- `update_memory` -> `status=updated`
- read-back verified through:
  - `get_memory`
  - `search_memory`
  - `fetch`
- rollback result:
  - final `status=archived`
  - final tags: `preview`, `write-check`, `rollback-archived`

Interpretation:

- preview write path is functioning end-to-end
- no unexpected transport/auth failure occurred during write verification
- write rollback currently means archived status, not delete

## Secret-Path Verification

Status: `verified once on Railway preview`

Result summary:

- mixed-secret payload save succeeded
- read-back content masked:
  - `token=[REDACTED]`
  - `Bearer [REDACTED]`
- mixed-secret probe record archived successfully after verification
- secret-only payload save was rejected
- rejected title search returned no results

Verified command:

- `python scripts/verify_mcp_secret_paths.py --server-url https://mcp-server-production-1454.up.railway.app/mcp/ --token <redacted> --confirm preview-secret-paths`

## Railway Production Dry Run

- project:
  - `mcp-obsidian-production`
- service:
  - `mcp-server`
- generated domain:
  - `https://mcp-server-production-90cb.up.railway.app`
- seed:
  - raw: `mcp_raw/manual/2026-03-28/convo-railway-production-seed.md`
  - memory: `20_AI_Memory/decision/2026/03/MEM-20260328-120319-2591AB.md`
- verification passed:
  - `/healthz`
  - read-only MCP verification
  - write-once verification
  - secret-path verification
  - backup/restore drill
    - archive example: `/data/backups/drill-20260328-122306.tar.gz`
    - restored files included production seed note, raw archive note, and SQLite index
- current operating decision:
  - `https://mcp-server-production-90cb.up.railway.app` is the official interim production endpoint
  - custom domain is optional future hardening, not a current release blocker

## Railway Production HMAC Phase 2

- `MCP_HMAC_SECRET` configured on Railway production service
- signed write verification:
  - memory id: `MEM-20260328-165501-4BBDFC`
  - integrity verifier -> `verified=true`
- signed secret-path verification:
  - mixed probe id: `MEM-20260328-165506-A19EBD`
  - integrity verifier -> `verified=true`
- signed raw archive verification:
  - raw path: `mcp_raw/manual/2026-03-28/convo-railway-production-hmac-seed.md`
  - integrity verifier -> `verified=true`
- unsigned legacy note handling:
  - memory id: `MEM-20260328-120319-2591AB`
  - `has_signature=false`
- verifier only accepts it with `--allow-unsigned-legacy`

## Specialist Read-Only Routes

- ChatGPT route:
  - `/chatgpt-healthz` -> `200`
  - `https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp`
  - tool set: `search`, `fetch`
  - no-auth read-only verification passed
- Claude route:
  - `/claude-healthz` -> `200`
  - `https://mcp-server-production-90cb.up.railway.app/claude-mcp`
  - tool set: `search`, `fetch`
  - no-auth read-only verification passed

## Specialist Write-Capable Sibling Routes

- ChatGPT sibling route:
  - `/chatgpt-write-healthz` -> `200`
  - `https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp-write`
  - unauthenticated probe -> `401`
  - authenticated tool set: `search`, `fetch`, `save_memory`, `get_memory`, `update_memory`
  - save/fetch/get/search/archive rollback verification passed
  - sample id: `MEM-20260328-203945-8AD433`
- Claude sibling route:
  - `/claude-write-healthz` -> `200`
  - `https://mcp-server-production-90cb.up.railway.app/claude-mcp-write`
  - unauthenticated probe -> `401`
  - authenticated tool set: `search`, `fetch`, `save_memory`, `get_memory`, `update_memory`
  - save/fetch/get/search/archive rollback verification passed
  - sample id: `MEM-20260328-203945-00EA52`

## Production Path Backfill and Specialist Recheck

- production deploy:
  - `railway up -d`
  - deployment: `7f706b9c-9d3d-429d-abb7-ca8519c225c7`
  - status: `SUCCESS`
- production path backfill:
  - command: `railway ssh python /app/scripts/backfill_memory_paths.py --apply`
  - moved: `18`
  - `updated_index_only`: `0`
  - `conflicts`: `0`
  - `missing`: `0`
- post-apply dry run:
  - command: `railway ssh python /app/scripts/backfill_memory_paths.py`
  - `candidate_count`: `0`
- health:
  - `/healthz` -> `200`
- read-only recheck after path migration:
  - ChatGPT route recheck passed
  - Claude route recheck passed
  - both returned `RailwayProductionDecision` with `url=file=memory/2026/03/MEM-20260328-120319-2591AB.md`
- specialist write sibling recheck after path migration:
  - ChatGPT sibling route recheck passed
    - sample id: `MEM-20260328-234330-5D6BA3`
  - Claude sibling route recheck passed
    - sample id: `MEM-20260328-234330-2D7741`
- implementation note:
  - hyphenated title search on the write sibling routes required an FTS query escaping fix before the recheck passed
