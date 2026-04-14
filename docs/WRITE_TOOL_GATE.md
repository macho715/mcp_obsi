# Write Tool Gate

```mermaid
flowchart LR
    ReadGreen["Read-only preview green"] --> Scope["Preview-only write scope"]
    Scope --> Save["save_memory once"]
    Save --> Update["update_memory once"]
    Update --> Readback["get/search/fetch readback"]
    Readback --> Archive["rollback via archived status"]
```

## Purpose

이 문서는 Railway preview에서 `save_memory` / `update_memory`를 실제로 1회 검증할 때의 gate와 rollback 기준을 고정한다.

## Gate Conditions

아래 조건이 모두 참일 때만 live write verification을 실행한다.

- target은 Railway hosted preview만 사용한다.
- read-only MCP verification이 이미 green이다.
- bearer auth와 host/origin allowlist가 이미 정상 동작한다.
- preview 데이터는 isolated preview 전용이어야 한다.
- `append_daily=False`로 실행해 daily note write를 막는다.

## Fixed Write Scope

live write verification은 아래 범위로 고정한다.

- tool: `save_memory`
- tool: `update_memory`
- `memory_type=decision`
- `source=manual`
- `project=preview`
- tags include:
  - `preview`
  - `verification`
  - `write-check`
- title prefix:
  - `Railway Preview Write Check`

## Rollback Rule

이 repo의 public MCP surface에는 delete tool이 없으므로 rollback은 soft rollback으로 정의한다.

- created memory는 마지막 단계에서 `status=archived`로 업데이트한다.
- rollback tags를 추가한다.
  - `preview`
  - `verification`
  - `write-check`
  - `rollback-archived`
- rollback 이후 `get_memory` 또는 `fetch`로 archived 상태를 다시 확인한다.

## Failure Handling

- `save_memory` succeeded, `update_memory` failed
  - saved memory id로 archived update를 다시 시도한다.
- save succeeded but client lost response
  - unique title prefix로 `search_memory` 후 memory id를 찾는다.
  - 찾은 id에 archived update를 수행한다.
- any auth / transport failure
  - write verification을 중단하고 read-only state만 유지한다.

## Success Criteria

- `save_memory` returns `status=saved` and an `id`
- `get_memory` returns the saved content
- `update_memory` returns `status=updated`
- `search_memory` returns the updated title/content
- `fetch` returns the same id/content in wrapper shape
- final archived update succeeds

## Verified Run

- date:
  - `2026-03-28`
- command:
  - `python scripts/verify_mcp_write_once.py --server-url https://mcp-server-production-1454.up.railway.app/mcp/ --token <redacted> --confirm preview-write-once`
- memory id:
  - `MEM-20260328-145016-D57430`
- observed results:
  - save succeeded
  - update succeeded
  - `get_memory`, `search_memory`, `fetch` all matched the updated record
  - rollback archived the record successfully

## Out of Scope

- bulk writes
- non-preview projects
- write approval automation
- delete semantics
- production write verification
