# One-Page Architecture

## Purpose

이 문서는 `standalone-package + mcp_obsidian + local-rag/Ollama` 조합의 **운영자용 1페이지 요약**이다.  
**계약 원본과 검증 기준은 `Spec.md`** 를 따른다.

## System Shape

```text
[User / Frontend / Dashboard]
            |
            v
+-----------------------------+
| standalone-package          |
| Node/TS/Express             |
| role: app/proxy/orchestrator|
+-----------------------------+
     |                 |
     | HTTP            | HTTP or MCP client
     v                 v
+----------------+   +---------------------------+
| local-rag      |   | mcp_obsidian              |
| role: retrieval|   | FastAPI + MCP memory svc  |
| / inference    |   | role: durable KB store    |
+----------------+   +---------------------------+
     |
     | model host calls
     v
+----------------+
| Ollama         |
| role: model    |
| serving host   |
+----------------+
                            |
                            v
                 +---------------------------+
                 | Obsidian Vault + SQLite   |
                 | wiki / memory / mcp_raw   |
                 +---------------------------+

[Cursor / Claude / ChatGPT]
            |
            v
      MCP -> mcp_obsidian
```

## Responsibility Split

| Component | Owns | Must Not Own |
|---|---|---|
| `standalone-package` | app API, proxy, HVDC predict orchestration, routing | durable knowledge source of truth |
| `local-rag` | generation, retrieval, rerank, local inference orchestration | long-term authoritative storage |
| `Ollama` | model serving host | durable knowledge source of truth |
| `mcp_obsidian` | memory API, `memory/` writes, `mcp_raw/` archive, search index | user-facing app proxy role |
| Obsidian Vault + SQLite | markdown SSOT + derived search index | app business orchestration |

## Port Map

| Service | Local Port | Note |
|---|---:|---|
| `standalone-package` | `3010` | app/proxy |
| `mcp_obsidian` | `8000` | MCP memory API |
| `local-rag` | `8010` | local retrieval/generation |
| `Ollama` | `11434` | model host |

## Configuration Ownership

| Area | Main Variables / Config |
|---|---|
| `standalone-package` | `MYAGENT_PROXY_*`, `MYAGENT_LOCAL_RAG_*`, `MYAGENT_HVDC_PREDICT_*` |
| `mcp_obsidian` | `VAULT_PATH`, `INDEX_DB_PATH`, `MCP_API_TOKEN`, `OBSIDIAN_LOCAL_VAULT_PATH` (script/sync helper) |
| Cursor MCP client | `.cursor/mcp.json`, `${env:MCP_API_TOKEN}`, `${env:MCP_PRODUCTION_BEARER_TOKEN}` |

상세 값과 예시는 `Spec.md`의 `Environment Baseline`을 따른다.

## Core Flows

### App Chat
```text
Frontend -> standalone-package -> local-rag or Copilot path -> response
```

### Knowledge Write / Retrieval
```text
Cursor / Claude / ChatGPT -> mcp_obsidian MCP -> vault markdown + SQLite index
```

### Integrated App + KB
```text
App request -> standalone-package -> local-rag
          -> if durable memory needed -> bounded external call to mcp_obsidian -> vault + index
```

### Desktop Visibility / Sync
```text
mcp_obsidian MCP write -> vault/memory or mcp_raw
                       -> local vault sync if needed
                       -> Obsidian desktop reads same folder

KB wiki writes are handled by repo/skill-level workflows, not by the FastAPI MCP runtime surface.
```

## Directory Boundary

```text
standalone-package/
  src/
  dist/
  .cursor/   # optional tooling/client config only

mcp_obsidian/
  app/
  scripts/
  vault/
  data/
  .cursor/
```

## Recommended Decision

- `standalone-package`는 앱으로 유지
- `standalone-package/.cursor/`만 additive merge
- `standalone-package`의 durable memory 연계는 `mcp_obsidian` 외부 client 호출로만 허용
- durable KB는 `mcp_obsidian`가 독점
- production은 app / memory / model 분리 서비스로 유지
- `local-rag`와 `Ollama`는 모델 계층으로 분리 유지

## See Also

- 계약/검증 기준: `Spec.md`
- 로컬 MCP 연결: `docs/LOCAL_MCP.md`
- Windows 로컬 설정: `docs/INSTALL_WINDOWS.md`