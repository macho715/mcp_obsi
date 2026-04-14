> Status: historical snapshot. This audit is a dated record, not a current canonical operating document. Current repo operation has since moved to global Cursor MCP config and additional hosted specialist routes.

```mermaid
flowchart LR
    Review["Parallel review"] --> Drift["Find drift"]
    Drift --> Sync["Docs sync"]
    Sync --> Gate["Stage gate update"]
```

# Stage Recheck Audit

Date: 2026-03-28  
Root: `C:\Users\jichu\Downloads\mcp_obsidian`

## Verdict

`PARTIAL`

현재 저장소는 hybrid redesign의 핵심 scaffold와 Python 검증은 통과했지만, 문서/상태 동기화 누락과 Cursor MCP runtime 증거 부족이 남아 있다.  
즉, **다음 스테이지로 진입 가능은 하되, “문서 정합성 보강 + Cursor MCP runtime 재검증”을 먼저 묶어서 처리하는 것이 안전하다.**

## Parallel Review Lanes

이번 재확인은 아래 병렬 축으로 수행했다.

- Lane A: 루트 문서 재점검
  - `AGENTS.md`
  - `README.md`
  - `changelog.md`
  - `SYSTEM_ARCHITECTURE.md`
  - `LAYOUT.md`
  - `plan.md`
  - `docs/INSTALL_WINDOWS.md`
- Lane B: 구현 파일 재점검
  - `app/main.py`
  - `app/mcp_server.py`
  - `app/models.py`
  - `app/services/*.py`
  - `schemas/*.json`
- Lane C: 검증 자산 재점검
  - `tests/*.py`
  - `pyproject.toml`
  - plugin build 결과물
- Lane D: 산출물/상태 확인
  - `vault/`
  - `data/`
  - Cursor project-local MCP artifact 경로

## Directly Confirmed

### Code and schema

- Python MCP 서버는 루트에 유지된다.
- `schemas/raw-conversation.schema.json` 존재
- `schemas/memory-item.schema.json` 존재
- `app/services/raw_archive_store.py` 존재
- `app/services/schema_validator.py` 존재
- `obsidian-memory-plugin/` scaffold 존재
- plugin build 결과물 `obsidian-memory-plugin/main.js` 존재

### Runtime and storage artifacts

- `.env` 존재
- `vault/20_AI_Memory/.../MEM-20260328-120319-9019D9.md` 존재
- `vault/mcp_raw/chatgpt/2026-03-28/convo-2026-03-28-e2e.md` 존재
- `data/memory_index.sqlite3` 존재

### Automated verification

- `pytest -q` 통과
- `ruff check .` 통과
- `ruff format --check app tests` 통과
- schema/plugin JSON parse 통과
- `SchemaValidator()` 로드 통과
- plugin:
  - `npm run check` 통과
  - `npm run build` 통과

## Missing / Drift / Inconsistency

### 1. `AGENTS.md` drift

가장 큰 불일치는 [AGENTS.md](/c:/Users/jichu/Downloads/mcp_obsidian/AGENTS.md)다.

- 현재 파일은 `# [ASSUMPTION]` 문구를 포함한다.
- 실제 저장소에 없는 경로를 언급한다.
  - `obsidian-mcp-server/`
- “명령이 repo evidence로 확인되지 않았다”는 문구가 남아 있지만, 현재 repo에는 `pyproject.toml`, `tests/`, `ruff` 구성이 실제 존재한다.
- 즉, **현재 `AGENTS.md`는 repo reality와 불일치가 있다.**

이 항목은 다음 스테이지 전에 정리 우선순위가 높다.

### 2. `plan.md` stale sections

[plan.md](/c:/Users/jichu/Downloads/mcp_obsidian/plan.md)에는 이미 stale한 상태가 남아 있다.

- `.env`는 존재한다고 갱신됐지만,
- `Verified current state`에는 여전히 과거 진단 결과가 남아 있다.
  - `8766`
  - `/mcp/` -> `404`
- 현재 최신 in-process 진단 기준 `/mcp/`는 `400 Bad Request: Missing session ID` 쪽이 더 정확하다.

즉, plan은 partially updated 상태다.

### 3. `changelog.md` manual section stale

[changelog.md](/c:/Users/jichu/Downloads/mcp_obsidian/changelog.md)의 hybrid redesign section에는 아직 다음이 manual로 남아 있다.

- `plugin 실제 npm install / npm run build`

하지만 현재는 이미 build 검증 완료 상태다.  
이 항목은 changelog에 반영되지 않았다.

### 4. `docs/INSTALL_WINDOWS.md` stale MCP response examples

[docs/INSTALL_WINDOWS.md](/c:/Users/jichu/Downloads/mcp_obsidian/docs/INSTALL_WINDOWS.md)에는 `/mcp`가 `307`, `503`, `404`일 수 있다고 적혀 있다.  
현재 최신 진단 기준으로는 `/mcp/`가 `400 Missing session ID`까지 갱신된 상태라 이 문서는 stale 가능성이 높다.

### 5. Cursor MCP status evidence incomplete

Cursor project-local MCP artifact 디렉터리는 존재한다.

- `project-0-mcp_obsidian-obsidian-memory-local`

하지만 상태 파일/세부 로그는 현재 대화에서 일관되게 확보되지 않았다.  
즉, **“connected”를 증명하는 직접 증거가 아직 없다.**

## What Is Not Missing

- hybrid storage artifacts
- shared schemas
- raw archive service
- schema validator
- plugin scaffold
- plugin build output
- hybrid storage test coverage

즉, 현재 누락의 중심은 “구현”보다 “상태 동기화와 운영 증거”다.

## Stage Gate

### Can enter next stage?

`예, 조건부로 가능`

### Required before or during next stage

1. `AGENTS.md`를 실제 repo 기준으로 재동기화
2. `plan.md`의 stale runtime lines 수정
3. `changelog.md`의 plugin build manual 항목 수정
4. `docs/INSTALL_WINDOWS.md`의 `/mcp` 응답 설명 최신화
5. Cursor MCP `connected` 증거를 다시 확보

### Recommended next stage

`Docs sync + MCP runtime evidence stage`

이 단계의 목표는 새 기능 추가가 아니라:

- 문서와 실제 상태를 맞추고
- Cursor MCP runtime evidence를 고정하고
- 그 다음 feature/hardening stage로 넘어가는 것이다.

## Commands Actually Rechecked

```powershell
pytest -q
ruff check .
ruff format --check app tests
npm run check
npm run build
```

추가로 직접 확인:

- `SchemaValidator()` load
- schema/plugin JSON parse
- `vault/` generated files
- `data/` runtime/debug artifacts
- Cursor project-local MCP directory

## Final Note

현재 저장소는 “코드가 비어 있거나 누락된 상태”는 아니다.  
오히려 **코드/테스트는 앞서 있고, 문서와 운영 증거가 따라오지 못한 상태**에 가깝다.

## Follow-up Sync Applied

이 audit 이후 아래 정합화가 실제로 반영됐다.

- `AGENTS.md`
  - assumption 문구 제거
  - 실제 repo 구조 기준으로 재작성
- `plan.md`
  - `.env` 존재 반영
  - Cursor project-local tool offerings 반영
  - stale `404` 진단을 최신 runtime 사실로 교체
- `changelog.md`
  - plugin build/check 완료 반영
  - hybrid storage runtime 확인 반영
- `docs/INSTALL_WINDOWS.md`
  - hybrid 구조 항목 추가
  - 최신 `/mcp` / `/mcp/` 응답 현실 반영

남은 핵심 manual은 여전히 하나다.

- Cursor MCP의 최종 `connected` UI 증거 확보

## Final Gate Update

이후 추가 확인으로 아래 gate는 닫혔다.

- Cursor **Settings -> MCP**에서 `obsidian-memory-local = connected` 수동 확인

현재 이 audit 기준의 후속 단계는 더 이상 "Docs sync + MCP runtime evidence"가 아니다.

- docs sync: 완료
- local MCP runtime evidence: 완료
- next stage: preview deployment execution + write-tool hardening
