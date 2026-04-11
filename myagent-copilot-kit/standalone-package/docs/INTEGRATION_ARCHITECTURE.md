# Integration Architecture

## Purpose

이 문서는 `standalone-package`가 `mcp_obsidian`와 `local-rag`/`Ollama`를 어떻게 외부 의존성으로 연결하는지 설명한다. 이 문서는 런타임 병합 문서가 아니라 **경계와 연결 지점**만 정의한다.

## Responsibility Split

| Component | Owns | Must Not Own |
|---|---|---|
| `standalone-package` | app API, proxy, orchestration, HVDC route handling | durable knowledge source of truth |
| `mcp_obsidian` | memory MCP API, vault writes, search index, archive/raw/wiki | app proxy role |
| `local-rag` | local retrieval, generation, rerank, inference orchestration | long-term authoritative storage |
| `Ollama` | model serving host | durable knowledge source of truth |

## Local Port Map

| Service | Port | Role |
|---|---:|---|
| `standalone-package` | `3010` | app/proxy |
| `mcp_obsidian` | `8000` | MCP memory service |
| `local-rag` | `8010` | local retrieval/generation |
| `Ollama` | `11434` | model host |

## Data Flows

### App Chat

```text
Frontend -> standalone-package -> local-rag or Copilot path -> response
```

현재 local-rag integration은 `GET /health`와 `POST /api/internal/ai/chat-local`을 사용한다.

### Durable Knowledge

```text
Cursor / Claude / ChatGPT -> mcp_obsidian MCP -> vault markdown + SQLite index
```

### Integrated App + KB

```text
App request -> standalone-package -> local-rag
          -> if durable memory needed -> bounded external call to mcp_obsidian read-only MCP mount -> vault + index
```

### Desktop Visibility / Sync

```text
mcp_obsidian write -> vault/wiki or memory
                   -> local vault sync if needed
                   -> Obsidian desktop reads same folder
```

## Cursor Integration

- `standalone-package/.cursor/mcp.json`는 `mcp_obsidian` local endpoint를 project-local MCP profile로 연결한다.
- local endpoint는 `http://127.0.0.1:8000/mcp`를 사용한다.
- bearer token은 `${env:MCP_API_TOKEN}`로 주입한다.
- 이 IDE MCP profile은 Cursor용 main `/mcp` 연결이다.
- in-app memory bridge는 별도 env (`MYAGENT_MEMORY_BASE_URL`, `MYAGENT_MEMORY_MCP_PATH`)를 사용하며, 현재 기본값은 read-only `/chatgpt-mcp` mount다.

## Approved Runtime Decisions

- `standalone-package`는 durable memory가 필요할 때만 `mcp_obsidian`를 외부 client로 호출한다.
- direct vault/SQLite 접근과 Python memory runtime 내장은 허용하지 않는다.
- production은 app / memory / model을 분리 서비스로 유지한다.
- `local-rag`와 `Ollama`는 분리 유지한다.

### Approved Merge Scope

- 현재 실제 포함: `.cursor/mcp.json`
- 승인된 optional bundle: `.cursor/skills/obsidian-conversation-to-memory/`
- 승인된 optional bundle: `.cursor/skills/cursor-obsidian-converter-package/`
- 승인된 conditional bundle: `.cursor/skills/paste-conversation-to-obsidian/`
  - trigger: pasted transcript를 standalone에서 바로 vault memory로 저장해야 할 때
  - approver: app owner
- 승인된 conditional bundle: `.cursor/agents/obsidian-converter-package.md`
- 승인된 conditional bundle: `.cursor/agents/obsidian-metadata-scout.md`
- 승인된 conditional bundle: `.cursor/agents/obsidian-memory-splitter.md`
- 승인된 conditional bundle: `.cursor/agents/obsidian-memory-verifier.md`
  - trigger: converter bundle 전체 워크플로우를 standalone repo에 함께 설치할 때
  - approver: app owner, memory owner
- 제외: `obsidian-memory-workflow`, ingest/query/lint/release-check 등 standalone 운영과 직접 무관하거나 vault-side 책임과 충돌하는 skill

## Current Runtime Notes

- current standalone memory bridge는 read-only `search` / `fetch`만 사용한다.
- `MYAGENT_MEMORY_MCP_PATH` 기본값은 `/chatgpt-mcp`다.
- `/api/ai/health`의 `memoryOk`는 read-only MCP contract probe 결과다.
- `/api/memory/health`는 root `/healthz` liveness와 read-only MCP contract probe를 함께 본다.

## Non-Goals

- `standalone-package` 내부에 Python memory runtime을 임베드하지 않는다.
- app process가 vault markdown이나 SQLite 파일을 직접 읽고 쓰지 않는다.
- auth, MCP tool schema, vault layout 계약은 이 문서에서 변경하지 않는다.
