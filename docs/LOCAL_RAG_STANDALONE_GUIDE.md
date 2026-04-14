# Local RAG + Standalone Stack 가이드

한 줄 요약: 이 가이드는 Windows에서 `Ollama`, `local-rag`, `mcp_obsidian`, `standalone-package`를 켜고 브라우저에서 질문까지 보내는 가장 짧은 경로를 설명합니다.

## 이 가이드로 끝나면

- `http://127.0.0.1:3010/` 화면이 열립니다.
- 로컬 AI 스택 4개가 모두 켜집니다.
- 브라우저에서 질문 1개를 보내고 응답을 확인할 수 있습니다.
- 문제가 생기면 어디부터 다시 확인해야 하는지 바로 알 수 있습니다.

## 누가 보면 좋은가

- 처음 세팅하는 사용자
- 매일 로컬 스택을 켜는 운영자
- 브라우저 화면은 열리는데 어느 서비스가 죽었는지 헷갈리는 사람

## 스택 구성 요소

| 서비스 | 역할 | 기본 포트 | 사용자가 체감하는 것 |
|--------|------|----------|----------------------|
| **Ollama** | 로컬 LLM 엔진 (Gemma 4) | `11434` | 답변을 만드는 엔진 |
| **local-rag** | retrieval + generation 서비스 | `8010` | 로컬 문서를 찾아 답변 재료를 모음 |
| **mcp_obsidian** | memory/knowledge base API | `8000` | 메모와 저장된 지식 조회 |
| **standalone-package** | 웹 채팅 UI | `3010` | 사용자가 실제로 보는 화면 |

## 시작 전 확인

- [ ] Ollama가 설치되어 있습니다.
- [ ] `gemma4:e4b` 모델을 다운로드했습니다.
- [ ] 저장소 경로가 `C:\Users\jichu\Downloads\mcp_obsidian` 입니다.
- [ ] `start-all.ps1`, `stop-all.ps1`, `make-shortcuts.ps1` 파일이 있습니다.
- [ ] Windows PowerShell을 사용할 수 있습니다.

Assumption: 저장소 경로가 다르면 아래 명령의 경로를 현재 PC 경로에 맞게 바꿔야 합니다.

## 가장 쉬운 시작 방법

### 방법 1: 바로 실행 바로 확인

1. 아래 바로가기를 실행합니다.

```text
C:\Users\jichu\Downloads\mcp_obsidian\Start MStack.lnk
```

2. 또는 바탕화면의 `Start MStack.lnk`를 더블클릭합니다.
3. 브라우저가 자동으로 열리면 `http://127.0.0.1:3010/` 화면이 보이는지 확인합니다.
4. 입력창에 아래 질문을 넣고 `질문 보내기`를 누릅니다.

```text
HVDC 문서 최근 내용 요약해줘
```

### 방법 2: PowerShell 한 줄 실행

```powershell
cd C:\Users\jichu\Downloads\mcp_obsidian
.\start-all.ps1
```

### 방법 3: 수동 실행

이 방법은 어디서 멈췄는지 직접 확인할 때만 권장합니다.

```powershell
# 1. Ollama
ollama serve

# 2. local-rag (별도 PowerShell 창)
cd C:\Users\jichu\Downloads\mcp_obsidian\local-rag
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010

# 3. mcp_obsidian (별도 PowerShell 창)
cd C:\Users\jichu\Downloads\mcp_obsidian
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 4. standalone-package (별도 PowerShell 창)
cd C:\Users\jichu\Downloads\mcp_obsidian\myagent-copilot-kit\standalone-package
$env:MYAGENT_HVDC_PREDICT_ENABLED="0"
node --import tsx src/cli.ts serve --host 127.0.0.1 --port 3010
```

## 지금 상태를 확인하는 순서

이 순서대로 보면 어디서 멈췄는지 빠르게 찾을 수 있습니다.

### 1. 시작 요청

- `Start MStack.lnk`를 눌렀거나 `.\start-all.ps1`를 실행했는지 확인합니다.

### 2. 서비스 기동 확인

```powershell
@(
  "http://127.0.0.1:11434/",
  "http://127.0.0.1:8010/health",
  "http://127.0.0.1:8000/healthz",
  "http://127.0.0.1:3010/api/ai/health"
) | ForEach-Object {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $_ -TimeoutSec 5
    Write-Host "OK  $_ ($($r.StatusCode))"
  } catch {
    Write-Host "FAIL $_"
  }
}
```

### 3. 정상 화면 확인

- 브라우저에서 `http://127.0.0.1:3010/`를 엽니다.
- 아래 3개가 보이면 1차 통과입니다.
  - `Standalone Chat` 제목
  - 질문 입력창
  - `질문 보내기` 버튼

### 4. 결과 확인

| 서비스 | 어디를 보면 되는가 | 최소 통과 기준 |
|--------|-------------------|----------------|
| Ollama | `11434` 응답 또는 `ollama list` | 응답이 오고 모델이 보임 |
| local-rag | `http://127.0.0.1:8010/health` | `status: ok` |
| mcp_obsidian | `http://127.0.0.1:8000/healthz` | `ok: true` |
| standalone | `http://127.0.0.1:3010/api/ai/health` | HTTP `200` |

## 브라우저에서 어떻게 쓰나

1. `http://127.0.0.1:3010/`를 엽니다.
2. 질문 입력창에 질문을 씁니다.
3. `질문 보내기`를 누릅니다.
4. 아래 `응답` 영역과 `근거 문서` 영역을 확인합니다.

예시 질문:

- `HVDC 문서 최근 내용 요약해줘`
- `Gemma 4 모델 개요를 한 줄로 설명해줘`
- `최근 메모 5건 제목만 보여줘`

## API로 직접 확인할 때

### 빠른 health 확인

```powershell
Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8010/health
Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8010/api/internal/ai/chat-local/ready
Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8000/healthz
Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:3010/api/ai/health
```

### 채팅 API 호출 예시

주의: `POST /api/ai/chat`는 `message` 단일 문자열이 아니라 `messages` 배열을 받아야 합니다.

```powershell
$body = @{
  messages = @(
    @{ role = "user"; content = "최근 메모 1건 제목만" }
  )
  route = "local"
} | ConvertTo-Json -Depth 5

Invoke-WebRequest `
  -UseBasicParsing `
  -Method Post `
  -Uri http://127.0.0.1:3010/api/ai/chat `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

## 자주 생기는 증상과 바로 할 일

| 증상 | 먼저 볼 것 | 바로 할 일 |
|------|------------|------------|
| 브라우저가 안 열림 | `start-all.ps1` 실행 여부 | `http://127.0.0.1:3010/` 수동 접속 |
| `401 Unauthorized` | secret/env 값 | `LOCAL_RAG_SHARED_SECRET`, `MYAGENT_LOCAL_RAG_TOKEN` 확인 |
| `503 Service Unavailable` | local-rag, Ollama | `8010/health`, `11434` 확인 |
| `Connection refused` | 포트 점유 여부 | `netstat -ano -p tcp \| Select-String ":XXXX\s"` |
| 채팅은 열리는데 답이 비거나 이상함 | Ollama 모델 상태 | `ollama list`, `ollama run gemma4:e4b` |
| API가 `INVALID_REQUEST`를 반환 | 요청 형식 | `messages` 배열 사용 여부 확인 |

## 실패했을 때 다시 시작하는 순서

이 문서에서 가장 중요한 복구 순서입니다.

1. 브라우저를 닫습니다.
2. `.\stop-all.ps1`를 실행합니다.
3. 5초 정도 기다립니다.
4. `.\start-all.ps1`를 다시 실행합니다.
5. health 4개를 다시 확인합니다.
6. 그래도 안 되면 수동 실행 방식으로 어느 서비스가 죽는지 확인합니다.

## 종료 방법

```powershell
cd C:\Users\jichu\Downloads\mcp_obsidian
.\stop-all.ps1
```

또는 `Stop MStack.lnk`를 클릭합니다.

Ollama가 자동 재시작되면 작업 관리자에서 `ollama app.exe`, `ollama.exe`를 종료합니다.

## 환경변수 참고

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `LOCAL_RAG_SHARED_SECRET` | local-rag 내부 라우트 보호용 시크릿 | 비어 있으면 loopback 허용 |
| `MYAGENT_LOCAL_RAG_TOKEN` | standalone-package → local-rag 인증 헤더 | `LOCAL_RAG_SHARED_SECRET` fallback |
| `LOCAL_RAG_DOCS_DIR` | retrieval 대상 문서 폴더 | `C:\Users\jichu\Downloads\valut\wiki` |
| `OLLAMA_BASE_URL` | Ollama 엔드포인트 | `http://127.0.0.1:11434` |

## 부록 A — UI 업그레이드 메모

### 포함된 개선

| 항목 | 설명 |
|------|------|
| Chat history | `localStorage`에 최대 50개 메시지 저장 |
| Model selector | `gemma4:e4b` / `gemma4:e2b` 선택 |
| Token persistence | token input을 `localStorage`에 저장 |
| Loading spinner | 전송 중 spinner 표시 |
| Error banner | HTTP 오류 시 붉은 배너 표시 |
| Clear chat button | 채팅 기록 초기화 |

### 확인 방법

```powershell
cd C:\Users\jichu\Downloads\mcp_obsidian\myagent-copilot-kit\standalone-package
pnpm run build
```

브라우저에서 확인:

1. 질문 3개 전송 후 새로고침
2. `gemma4:e2b` 선택 후 전송
3. token 입력 후 새로고침
4. local-rag 중지 후 전송
5. `채팅 지우기` 클릭

## 부록 B — local-rag Retrieval Quality 메모

| 항목 | 설명 |
|------|------|
| Benchmark | 10개 쿼리 기준 lexical retrieval 평가 |
| Cache logging | `app/retrieval.py`에 INFO cache hit/miss 로깅 |
| Vault 경로 | `LOCAL_RAG_DOCS_DIR = C:\Users\jichu\Downloads\valut\wiki` |
| Decision | corpus가 작을 때는 lexical 우선, rerank는 추후 재평가 |

Benchmark 상세: [2026-04-08-local-rag-retrieval-benchmark.md](c:/Users/jichu/Downloads/mcp_obsidian/docs/superpowers/specs/2026-04-08-local-rag-retrieval-benchmark.md)

로그 예시:

```text
[RETRIEVAL] cache=HIT terms="gemma 4 model" results=3
[RETRIEVAL] cache=MISS terms="hvdc logistics"
```

## 부록 C — mcp_obsidian 연동 메모

| 항목 | 설명 |
|------|------|
| Token env 공유 | `start-all.ps1`가 standalone 기동 시 token env 전달 |
| Memory proxy routes | `/api/memory/search`, `/api/memory/fetch`, `/api/memory/save` |
| saveMemory | conversation summary를 memory에 저장 |
| Save to memory | 응답 후 저장 버튼으로 MCP `save_memory` 호출 |

예시:

```bash
curl -X POST http://127.0.0.1:3010/api/memory/save \
  -H "Content-Type: application/json" \
  -H "x-ai-proxy-token: dev-memory-token" \
  -d '{
    "title": "[Chat] HVDC 계획 요약",
    "content": "User: HVDC 계획은...\n\nAI: ...",
    "source": "standalone-chat",
    "topics": ["hvdc", "chat"]
  }'
```

## 관련 문서

- [2026-04-08-local-rag-cache-and-guard-design.md](c:/Users/jichu/Downloads/mcp_obsidian/docs/superpowers/specs/2026-04-08-local-rag-cache-and-guard-design.md)
- [2026-04-08-local-rag-retrieval-benchmark.md](c:/Users/jichu/Downloads/mcp_obsidian/docs/superpowers/specs/2026-04-08-local-rag-retrieval-benchmark.md)
- [README.md](c:/Users/jichu/Downloads/local-rag/README.md)
- [INTEGRATION_ARCHITECTURE.md](c:/Users/jichu/Downloads/myagent-copilot-kit/standalone-package/docs/INTEGRATION_ARCHITECTURE.md)
