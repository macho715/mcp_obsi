# MCP Runtime Evidence

```mermaid
flowchart LR
    Endpoint["/healthz + /mcp"] --> Transport["Public MCP transport"]
    Transport --> Tools["Read-only tool calls"]
    Tools --> Result["Normalized hit / raw exclusion"]
    Result --> Evidence["Verification evidence"]
```

Date range: 2026-03-28 -> 2026-04-11

## Scope

read-first live MCP verification for the hybrid redesign.

## 2026-04-11 Current Session Final Status

이 섹션은 **현재 Codex 세션 최종 상태**만 짧게 요약한다.

- production redeploy 이후 read-only specialist routes는 current local과 같은 수준으로 다시 확인됐다.
  - `search`
  - `list_recent_memories`
  - `fetch`
  - `search_wiki`
  - `fetch_wiki`
  - `resources = 5`
  - `prompts = 4`
- production write-capable sibling routes도 current local과 같은 수준으로 다시 확인됐다.
  - 13-tool surface
  - `search_wiki`
  - `fetch_wiki`
  - `sync_wiki_index`
  - `append_wiki_log`
  - `write_wiki_page`
  - `lint_wiki`
  - `reconcile_conflict`
- sample ids:
  - ChatGPT write check → `MEM-20260411-194216-B12AE8`
  - Claude write check → `MEM-20260411-194215-091F41`
- 아래의 earlier 2026-04-11 FAIL 기록은 **같은 세션 안의 pre-redeploy snapshot**이며, 현재 최종 상태를 뜻하지 않는다.

## 2026-04-11 Current Session — Wiki Overlay / Resources / Prompts / Wiki Tools

이 섹션은 **현재 Codex 세션**에서 직접 실행한 검증만 기록한다.

### Current-session local precheck

- local `http://127.0.0.1:8000/healthz`는 처음엔 down이었다.
- current session에서 `.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`를 background로 띄운 뒤 `200` 응답을 확인했다.

### Earlier same-session pre-redeploy specialist write verifier (historical)

실행 명령:

- `.venv\Scripts\python.exe scripts\verify_specialist_mcp_write.py --server-url https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp-write/ --token <redacted> --profile chatgpt`

결과:

- **FAIL**
- 실패 이유: production `/chatgpt-mcp-write`의 live tool set이 아직 `search`, `fetch`, `list_recent_memories`, `save_memory`, `get_memory`, `update_memory`까지만 노출하고 있어서, current code가 기대하는 wiki-native tools(`sync_wiki_index`, `append_wiki_log`, `write_wiki_page`, `lint_wiki`, `reconcile_conflict`)와 불일치했다.
- 즉, 이번 실패는 current local code의 verifier expectation과 current production deployment surface 사이의 **배포 불일치**다.

### Earlier same-session full verification round (historical)

실행 명령:

- `powershell -ExecutionPolicy Bypass -File .\scripts\run_mcp_verification_round.ps1 -Round 1`

결과 요약:

- `local_all_mounts_observe` → **PASS**
  - local `/mcp` tool set: `append_wiki_log`, `archive_raw`, `fetch`, `get_memory`, `lint_wiki`, `list_recent_memories`, `reconcile_conflict`, `save_memory`, `search`, `search_memory`, `sync_wiki_index`, `update_memory`, `write_wiki_page`
  - local read-only wrapper routes(`/chatgpt-mcp`, `/claude-mcp`) on current session exposed:
    - resources `5개`
    - prompts `4개`
  - local `read_path_verified = true`
- `production_all_mounts_observe` → **PASS (observe only)**
  - production `/mcp` live tool set: 기존 8개 tool만 노출
  - production `/chatgpt-mcp`, `/claude-mcp` live resources count = `0`
  - production `/chatgpt-mcp`, `/claude-mcp` live prompts count = `0`
  - 현재 code와 달리 production read-only routes에는 resources/prompts가 아직 배포되지 않았다.
- `verify_main_mcp_readonly` → **PASS**
- `verify_chatgpt_mcp_readonly` → **PASS**
- `verify_claude_mcp_readonly` → **PASS**
- `verify_mcp_write_once` → **PASS**
  - sample id: `MEM-20260411-174139-71BBB9`
  - final rollback state: `status = archived`
- `verify_mcp_secret_paths` → **PASS**
  - sample mixed probe id: `MEM-20260411-174147-6F191B`
  - mixed-secret payload masked readback + archived rollback 확인
- `verify_chatgpt_specialist_write` → **FAIL**
  - 실패 이유: production `/chatgpt-mcp-write` tool set mismatch
  - actual live tools: `search`, `fetch`, `list_recent_memories`, `save_memory`, `get_memory`, `update_memory`
  - expected current-code tools: 위 6개 + `sync_wiki_index`, `append_wiki_log`, `write_wiki_page`, `lint_wiki`, `reconcile_conflict`
- round script는 `verify_chatgpt_specialist_write` 실패 지점에서 중단됐기 때문에 `verify_claude_specialist_write`와 후속 `pytest_mcp_focus` step은 current session 기준으로 실행되지 않았다.

### Earlier same-session interpretation (historical)

- local current code는 `resources + prompts + wiki-native write tools`를 이미 노출한다.
- production current deployment는 아직 기존 specialist write surface에 머물러 있다.
- 따라서 이번 current-session 결과는 **code is ready, production is not yet rolled forward**로 해석해야 한다.
- 위 해석은 redeploy 전 snapshot에만 해당한다. 현재 final state는 아래 PASS 섹션을 기준으로 읽는다.

### Current-session production redeploy + readonly recheck

실행 명령:

- `railway up -d`
- `.venv\Scripts\python.exe scripts\verify_chatgpt_mcp_readonly.py --server-url https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp/`
- `.venv\Scripts\python.exe scripts\verify_claude_mcp_readonly.py --server-url https://mcp-server-production-90cb.up.railway.app/claude-mcp/`
- `.venv\Scripts\python.exe scripts\mcp_local_tool_smoke.py --base-url https://mcp-server-production-90cb.up.railway.app --path /chatgpt-mcp/ --search-query "초기 실행 절차를 CLAUDE.md와 wiki 업데이트 규칙으로 고정한다" --require-read-hit`
- `.venv\Scripts\python.exe scripts\mcp_local_tool_smoke.py --base-url https://mcp-server-production-90cb.up.railway.app --path /claude-mcp/ --search-query "초기 실행 절차를 CLAUDE.md와 wiki 업데이트 규칙으로 고정한다" --require-read-hit`

결과:

- **PASS**
- production `/healthz` → `200`
- production `/chatgpt-healthz` → `200`
- production `/claude-healthz` → `200`
- production `chatgpt-mcp` read-only tool set:
  - `search`
  - `fetch`
  - `list_recent_memories`
  - `search_wiki`
  - `fetch_wiki`
- production `claude-mcp` read-only tool set:
  - `search`
  - `fetch`
  - `list_recent_memories`
  - `search_wiki`
  - `fetch_wiki`
- production read-only resources count = `5`
- production read-only prompts count = `4`
- smoke 기준 read path verification도 통과했다.
  - `chatgpt-mcp` → `read_path_verified = true`
  - `claude-mcp` → `read_path_verified = true`

해석:

- earlier 2026-04-11 failure state는 redeploy 전 production lag였다.
- current session 기준으로는 production read-only surface가 now local과 같은 수준으로 올라왔다.

### Current-session production write-side recheck

실행 명령:

- `.venv\Scripts\python.exe scripts\verify_specialist_mcp_write.py --server-url https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp-write/ --token <redacted> --profile chatgpt`
- `.venv\Scripts\python.exe scripts\verify_specialist_mcp_write.py --server-url https://mcp-server-production-90cb.up.railway.app/claude-mcp-write/ --token <redacted> --profile claude`

결과:

- **PASS**
- production `chatgpt-mcp-write` authenticated tool set:
  - `search`
  - `fetch`
  - `list_recent_memories`
  - `search_wiki`
  - `fetch_wiki`
  - `save_memory`
  - `get_memory`
  - `update_memory`
  - `sync_wiki_index`
  - `append_wiki_log`
  - `write_wiki_page`
  - `lint_wiki`
  - `reconcile_conflict`
- production `claude-mcp-write` authenticated tool set:
  - `search`
  - `fetch`
  - `list_recent_memories`
  - `search_wiki`
  - `fetch_wiki`
  - `save_memory`
  - `get_memory`
  - `update_memory`
  - `sync_wiki_index`
  - `append_wiki_log`
  - `write_wiki_page`
  - `lint_wiki`
  - `reconcile_conflict`
- write verification 흐름도 현재 세션에서 모두 통과했다.
  - save
  - fetch
  - get
  - search
  - wiki index sync
  - wiki log append
  - wiki lint
  - rollback archive
- sample ids:
  - ChatGPT write check → `MEM-20260411-194216-B12AE8`
  - Claude write check → `MEM-20260411-194215-091F41`

해석:

- current session 기준으로 production write-side surface도 now local과 같은 수준으로 올라왔다.
- earlier verifier failure 원인은 production lag + verifier expected tool set mismatch였고, current session에서는 둘 다 해소됐다.

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

- repo-local `.cursor/mcp.json`

current code basis for the profile target `/mcp`:

- `search_memory`
- `save_memory`
- `get_memory`
- `list_recent_memories`
- `update_memory`
- `archive_raw`
- `search`
- `fetch`
- `search_wiki`
- `fetch_wiki`
- `sync_wiki_index`
- `append_wiki_log`
- `write_wiki_page`
- `lint_wiki`
- `reconcile_conflict`

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
- Cursor MCP는 현재 repo-local config 기준으로 local + production 둘 다 connected 상태가 확인됐다.
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

이 섹션은 현재 verification round 기본 셋이라기보다 별도 verifier 기반의 historical/manual evidence로 유지한다.

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
  - current-session final tool set: `search`, `list_recent_memories`, `fetch`, `search_wiki`, `fetch_wiki`
  - current-session final discoverability: `resources = 5`, `prompts = 4`
  - no-auth read-only verification passed after redeploy
- Claude route:
  - `/claude-healthz` -> `200`
  - `https://mcp-server-production-90cb.up.railway.app/claude-mcp`
  - current-session final tool set: `search`, `list_recent_memories`, `fetch`, `search_wiki`, `fetch_wiki`
  - current-session final discoverability: `resources = 5`, `prompts = 4`
  - no-auth read-only verification passed after redeploy

## Specialist Write-Capable Sibling Routes

- ChatGPT sibling route:
  - `/chatgpt-write-healthz` -> `200`
  - `https://mcp-server-production-90cb.up.railway.app/chatgpt-mcp-write`
  - unauthenticated probe -> `401`
  - current-session final authenticated tool set: `search`, `fetch`, `list_recent_memories`, `search_wiki`, `fetch_wiki`, `save_memory`, `get_memory`, `update_memory`, `sync_wiki_index`, `append_wiki_log`, `write_wiki_page`, `lint_wiki`, `reconcile_conflict`
  - save/fetch/get/search + wiki index sync + wiki log append + wiki lint + rollback archive verification passed
  - sample id: `MEM-20260411-194216-B12AE8`
- Claude sibling route:
  - `/claude-write-healthz` -> `200`
  - `https://mcp-server-production-90cb.up.railway.app/claude-mcp-write`
  - unauthenticated probe -> `401`
  - current-session final authenticated tool set: `search`, `fetch`, `list_recent_memories`, `search_wiki`, `fetch_wiki`, `save_memory`, `get_memory`, `update_memory`, `sync_wiki_index`, `append_wiki_log`, `write_wiki_page`, `lint_wiki`, `reconcile_conflict`
  - save/fetch/get/search + wiki index sync + wiki log append + wiki lint + rollback archive verification passed
  - sample id: `MEM-20260411-194215-091F41`

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
  - both returned `RailwayProductionDecision` with wrapper URL containing `file=memory/2026/03/MEM-20260328-120319-2591AB.md`
- specialist write sibling recheck after path migration:
  - ChatGPT sibling route recheck passed
    - sample id: `MEM-20260328-234330-5D6BA3`
  - Claude sibling route recheck passed
    - sample id: `MEM-20260328-234330-2D7741`
- implementation note:
  - hyphenated title search on the write sibling routes required an FTS query escaping fix before the recheck passed
