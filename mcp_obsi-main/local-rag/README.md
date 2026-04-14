# local-rag

`standalone-package`의 local-only route를 위해 만든 로컬 retrieval/generation 서비스다.

## Contract

- port: `8010`
- `GET /health` — liveness probe (서비스 기동 여부)
- `GET /api/internal/ai/chat-local/ready` — readiness probe (트래픽 수락 가능 여부)
- `POST /api/internal/ai/chat-local`

비고: `standalone-package`는 `/ready`를 먼저 호출하여 local-rag가 쿼리 처리 가능한 상태인지 확인한 후 `/chat-local`을 호출합니다.

현재 구현 범위:

- Ollama direct generation
- 문서 폴더 기반 lexical retrieval
- 보수적 retrieval cache
- `sources[]` / `snippet` 포함 응답
- optional shared-secret guard for internal chat route

비포함:

- vector DB
- rerank
- durable storage
- SQLite cache

## Environment

기본값:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
LOCAL_RAG_MODEL=gemma4:e4b
LOCAL_RAG_DOCS_DIR=C:\Users\jichu\Downloads\valut\wiki
LOCAL_RAG_CACHE_PATH=.cache\retrieval-cache.json
LOCAL_RAG_QUERY_CACHE_TTL_SEC=45
LOCAL_RAG_SHARED_SECRET=
LOCAL_RAG_HOST=127.0.0.1
LOCAL_RAG_PORT=8010
```

문서 폴더는 `LOCAL_RAG_DOCS_DIR`로 override 가능하다.
`LOCAL_RAG_SHARED_SECRET`를 설정하면 `POST /api/internal/ai/chat-local`만 보호된다.
`GET /health`는 계속 공개다.
secret가 비어 있으면 direct loopback caller만 허용하는 최소 보호만 적용된다.
reverse proxy, tunnel, public exposure가 있으면 `LOCAL_RAG_SHARED_SECRET`를 반드시 설정해야 한다.

## Shared-Secret Header Mapping

`standalone-package` → `local-rag` 호출 시 인증 헤더 흐름:

```
MYAGENT_LOCAL_RAG_TOKEN (standalone env)
       ↓ (fallback)
LOCAL_RAG_SHARED_SECRET (local-rag env)
       ↓ (HTTP header)
x-local-rag-token
```

| 환경변수 | 적용 범위 | 비고 |
|----------|-----------|------|
| `MYAGENT_LOCAL_RAG_TOKEN` | standalone-package만 | standalone-package 기동 시 |
| `LOCAL_RAG_SHARED_SECRET` | local-rag + standalone-package fallback | shared secret으로 통일 시 사용 |

优先순위: `MYAGENT_LOCAL_RAG_TOKEN` 설정 시 그것이 우선. 미설정 시 `LOCAL_RAG_SHARED_SECRET` fallback. 둘 다 비어 있으면 empty (loopback 호출만 허용).

## Quick Start

```powershell
cd C:\Users\jichu\Downloads\local-rag
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
```

실행:

```powershell
powershell -ExecutionPolicy Bypass -File .\run-local.ps1
```

헬스체크:

```powershell
powershell -ExecutionPolicy Bypass -File .\healthcheck.ps1
```

직접 호출 예시:

```powershell
$body = @{
  messages = @(
    @{ role = "user"; content = "Gemma 4를 한 문장으로 요약하라." }
  )
  scope = @()
  mode = "chat"
  routeHint = "local"
} | ConvertTo-Json -Depth 5

Invoke-WebRequest -UseBasicParsing `
  -Method Post `
  -Uri http://127.0.0.1:8010/api/internal/ai/chat-local `
  -Headers @{
    "Content-Type" = "application/json"
    "x-local-rag-token" = $env:LOCAL_RAG_SHARED_SECRET
  } `
  -Body $body
```

## Cache Notes

- per-file cache는 `mtime`/`size` 기준으로 바뀐 파일만 다시 읽는다.
- sidecar 파일이 깨져도 요청은 계속 처리하고 캐시를 재구성한다.
- query cache는 매우 짧은 TTL만 사용한다.

## Related Design

Cache/guard 설계 사양: `C:\Users\jichu\Downloads\mcp_obsidian\docs\superpowers\specs\2026-04-08-local-rag-cache-and-guard-design.md`
