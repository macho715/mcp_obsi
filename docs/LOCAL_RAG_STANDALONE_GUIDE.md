# Local RAG + Standalone Stack 가이드

로컬 AI 스택을起動하고 운용하는 방법을 설명합니다.

---

## 스택 구성 요소

| 서비스 | 역할 | 기본 포트 |
|--------|------|----------|
| **Ollama** | 로컬 LLM 엔진 (Gemma 4) | `11434` |
| **local-rag** | retrieval + generation 서비스 | `8010` |
| **mcp_obsidian** | memory/knowledge base API | `8000` |
| **standalone-package** | 웹 채팅 UI (frontend) | `3010` |

---

## 사전 준비

- [ ] Ollama 설치 및 `gemma4:e4b` 모델 다운로드
- [ ] `C:\Users\jichu\Downloads\mcp_obsidian` 경로에 프로젝트克隆
- [ ] `start-all.ps1`, `stop-all.ps1`, `make-shortcuts.ps1` 스크립트 존재 확인
- [ ] Windows PowerShell 사용 가능

---

## 起動 방법

### 방법 1: 클릭 투 런 (추천)

```
C:\Users\jichu\Downloads\mcp_obsidian\Start MStack.lnk
```

또는 рабочий стол의 `Start MStack.lnk`를 더블클릭.
브라우저가 자동 개방됩니다.

### 방법 2: PowerShell 명령

```powershell
cd C:\Users\jichu\Downloads\mcp_obsidian
.\start-all.ps1
```

### 방법 3: 수동起動 (각 서비스별)

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

---

## Health 검증

모든 서비스가 정상 기동했는지 확인합니다.

```powershell
# 순차 검증
@("http://127.0.0.1:11434/", "http://127.0.0.1:8010/health", "http://127.0.0.1:8000/healthz", "http://127.0.0.1:3010/api/ai/health") | ForEach-Object {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $_ -TimeoutSec 5
    Write-Host "OK  $_ ($($r.StatusCode))"
  } catch {
    Write-Host "FAIL $_"
  }
}
```

정상 응답:| 서비스 | 기대 응답 |
|--------|----------|
| Ollama `11434` | `{"model"...}` 또는 HTML |
| local-rag `8010` | `{"status":"ok"...}` |
| mcp_obsidian `8000` | `{"status":"ok"...}` |
| standalone `3010` | `{"status":"ok"...}` |

---

## 브라우저 접근

```
http://127.0.0.1:3010/
```

채팅 입력창에 질문を入力し、送信 클릭.

---

## 빠른 검증 쿼리 (Copy-Paste Ready)

```powershell
# Q1: local-rag health
Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8010/health

# Q2: local-rag readiness probe
Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8010/api/internal/ai/chat-local/ready

# Q3: standalone health
Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:3010/api/ai/health

# Q4: mcp_obsidian health
Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8000/healthz
```

---

## 공통 증상 및 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| `CORS_ORIGIN_DENIED` | UI 서버 포트가 허용 목록에 없음 | `localhost` arbitrary 포트 자동 허용 (loopback 기동 시) |
| `401 Unauthorized` | shared-secret 불일치 | `LOCAL_RAG_SHARED_SECRET` / `MYAGENT_LOCAL_RAG_TOKEN` 환경변수 확인 |
| `503 Service Unavailable` | local-rag 미기동 또는 Ollama 미기동 | 각 서비스 health endpoint 확인 |
| `Connection refused` | 포트 충돌 또는 서비스 미기동 | `netstat -ano -p tcp \| Select-String ":XXXX\s"`로 포트 점유 확인 |
| 빈 응답 또는 meta 정보 | Ollama 미기동 또는 모델 미다운로드 | `ollama list`로 모델 확인, `ollama run gemma4:e4b`로 다운로드 |

---

## 종료 방법

```powershell
cd C:\Users\jichu\Downloads\mcp_obsidian
.\stop-all.ps1
```

또는 klik `Stop MStack.lnk`.

Ollama가自動 재시작되면, 작업 관리자에서 `ollama app.exe` 및 `ollama.exe` 프로세스를 강제 종료합니다.

---

## 환경변수 참고

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `LOCAL_RAG_SHARED_SECRET` | local-rag 내부 라우트 보호용 시크릿 | (비어 있음 = loopback 허용) |
| `MYAGENT_LOCAL_RAG_TOKEN` | standalone-package → local-rag 인증 헤더 | fallback: `LOCAL_RAG_SHARED_SECRET` |
| `LOCAL_RAG_DOCS_DIR` | retrieval 대상 문서 폴더 | `C:\Users\jichu\Downloads\valut\wiki` |
| `OLLAMA_BASE_URL` | Ollama 엔드포인트 | `http://127.0.0.1:11434` |

---

## 관련 문서

- 설계 사양: `docs/superpowers/specs/2026-04-08-local-rag-cache-and-guard-design.md`
- local-rag 상세: `local-rag/README.md`
- 통합 아키텍처: `myagent-copilot-kit/standalone-package/docs/INTEGRATION_ARCHITECTURE.md`
