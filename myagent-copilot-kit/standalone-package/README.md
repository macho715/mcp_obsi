# myagent-copilot-standalone

## 메타
- 문서 목적: `myagent-copilot-standalone` 패키지를 단독으로 설치, 빌드, 로그인, 실행, 배포, 검증하는 전체 절차를 제공합니다.
- 대상 독자: 운영자, 개발자, 배포 담당자, 기존 OpenClaw 경유 구성을 standalone으로 옮기려는 사용자
- 기준 운영안: `myagent-copilot-kit/standalone-package`
- 현재 기준 버전/산출물: `v0.1.0`, `release/myagent-copilot-standalone-v0.1.0.zip`
- 관련 문서:
  - `../README.md`
  - `OPERATIONS.md`
  - `MIGRATION.md`
  - `docs/INTEGRATION_ARCHITECTURE.md`

## 1. 패키지 개요
이 패키지는 GitHub Copilot 기반 AI 프록시를 OpenClaw 제품을 직접 실행하지 않고 독립적으로 띄우기 위한 패키지입니다.

핵심 기능:
- GitHub device login
- GitHub token -> Copilot runtime token 교환
- Copilot usage 조회
- `GET /api/ai/health`, `POST /api/ai/chat` 제공
- `POST /api/hvdc/predict`, `GET /api/hvdc/predict/:jobId`, `GET /api/hvdc/predict/:jobId/download` 제공
- pre-send DLP
- 민감도 라우팅
- CORS
- 프록시 토큰 인증
- Windows `.bat` 실행 파일
- 배포 zip export

기본 원칙:
- `Standalone 우선`
- `OpenClaw 경유는 호환 경로`
- `무차감 관측`과 `정책상 무제한 확정 불가`를 분리 기록

외부 연동 원칙:
- durable knowledge는 `mcp_obsidian`가 소유
- local retrieval/generation은 `local-rag` / `Ollama`가 담당
- `standalone-package`는 app/proxy/orchestrator로 유지

## 2. 설치 전 체크
- Node `22.12.0` 이상
- pnpm 설치
- Python `3.11+` 권장
- GitHub Copilot 로그인 가능한 계정
- 홈 디렉터리 쓰기 권한
- 기본 포트 `3010` 사용 가능 여부

확인 명령:
```bash
node -v
pnpm -v
python --version
```

## 3. 폴더 구조
```text
standalone-package/
├─ .cursor/
│  └─ mcp.json
├─ src/
├─ dist/
├─ release/
├─ package.json
├─ pnpm-lock.yaml
├─ .env.local.example
├─ .env.public.example
├─ build.bat
├─ login.bat
├─ token.bat
├─ usage.bat
├─ health.bat
├─ serve-local.bat
├─ serve-public.bat
├─ export-release.bat
├─ export-release.mjs
├─ OPERATIONS.md
└─ MIGRATION.md
```

## 4. 빠른 시작

### 4.1 설치
```bash
pnpm install
```

### 4.2 빌드
```bash
pnpm build
```

### 4.3 로그인
```bash
pnpm login
```

### 4.4 토큰 확인
```bash
pnpm token
```

### 4.5 사용량 확인
```bash
pnpm usage
```

### 4.6 로컬 서버 실행
```bash
pnpm serve:local
```

### 4.7 퍼블릭 서버 실행
```bash
pnpm serve:public
```

### 4.8 Cursor MCP 연동

`standalone-package/.cursor/mcp.json`는 로컬 `mcp_obsidian` 서버(`http://127.0.0.1:8000/mcp`)에 연결되도록 준비돼 있습니다.

필수 조건:
- `mcp_obsidian` 서버가 실행 중일 것
- `MCP_API_TOKEN` 환경변수가 `mcp_obsidian` 서버의 bearer token과 같을 것

주의:
- Cursor IDE profile은 main `/mcp`를 사용합니다.
- 앱 내부 memory bridge는 별도 env를 통해 기본적으로 read-only `/chatgpt-mcp`를 사용합니다.

연동 구조와 책임 경계는 `docs/INTEGRATION_ARCHITECTURE.md`를 따릅니다.

## 5. scripts 설명

### 5.1 `pnpm install`
- 의존성 설치

### 5.2 `pnpm build`
- 타입스크립트 빌드
- 결과물은 `dist/`에 생성

### 5.3 `pnpm dev`
- 개발용 직접 실행
- 내부적으로 `node --import tsx src/cli.ts serve`

### 5.4 `pnpm login`
- GitHub device flow 수행
- 결과를 `~/.myagent-copilot/auth-profiles.json`에 저장

### 5.5 `pnpm token`
- 현재 GitHub auth source와 runtime token baseUrl, expiresAt 확인

### 5.6 `pnpm usage`
- GitHub Copilot usage windows 조회

### 5.7 `pnpm health`
- 현재 서버 옵션 미리보기

### 5.8 `pnpm export:zip`
- 배포용 zip 생성

### 5.9 built-in docs routes
- `GET /docs`
  - 패키지 내 문서 인덱스 HTML
- `GET /docs/view?file=...`
  - 단일 문서 HTML 렌더링

## 6. `dist/cli.js` 직접 실행
빌드 후에는 `tsx` 없이도 Node만으로 바로 실행할 수 있습니다.

```bash
node dist/cli.js
node dist/cli.js health
node dist/cli.js login
node dist/cli.js token --json
node dist/cli.js usage --json --raw
node dist/cli.js serve --host 127.0.0.1 --port 3010
```

주요 command:
- `serve`
- `login`
- `token`
- `usage`
- `health`

## 7. Windows `.bat` 파일별 역할
- `build.bat`
  - `pnpm build` 래퍼
- `login.bat`
  - `pnpm login` 래퍼
- `token.bat`
  - `pnpm token --json` 래퍼
- `usage.bat`
  - `pnpm usage --json` 래퍼
- `health.bat`
  - `pnpm health` 래퍼
- `serve-local.bat`
  - 로컬 전용 실행
- `serve-public.bat`
  - 퍼블릭 전용 실행
- `export-release.bat`
  - zip export 래퍼

## 8. 상태 디렉터리

### 8.1 기본 위치
- `~/.myagent-copilot`

### 8.2 주요 파일
- auth store:
  - `~/.myagent-copilot/auth-profiles.json`
- runtime token cache:
  - `~/.myagent-copilot/cache/github-copilot.token.json`

### 8.3 fallback auth store
standalone store에 자격 증명이 없으면 아래를 순서대로 확인합니다.
- `~/.openclaw/agents/main/agent/auth-profiles.json`
- `~/.openclaw/auth-profiles.json`

이 fallback은 이관 편의를 위한 호환 경로입니다. 기본 운영 기준은 standalone store입니다.

## 9. 환경변수

| 변수 | 용도 | 기본값 | 비고 |
| --- | --- | --- | --- |
| `MYAGENT_HOME` | 상태 파일 루트 | `~/.myagent-copilot` | 홈 경로 변경 시 사용 |
| `MYAGENT_GITHUB_TOKEN` | GitHub 토큰 직접 주입 | 없음 | device login 대신 가능 |
| `COPILOT_GITHUB_TOKEN` | 호환 토큰 변수 | 없음 | 우선순위 후보 |
| `GH_TOKEN` | GitHub CLI 호환 변수 | 없음 | 우선순위 후보 |
| `GITHUB_TOKEN` | 일반 GitHub 토큰 변수 | 없음 | 우선순위 후보 |
| `MYAGENT_PROXY_HOST` | 바인딩 호스트 | `127.0.0.1` | 퍼블릭은 `0.0.0.0` |
| `MYAGENT_PROXY_PORT` | 포트 | `3010` | 필요 시 변경 |
| `MYAGENT_LOCAL_RAG_BASE_URL` | local-rag base URL | `http://127.0.0.1:8010` | 로컬 retrieval/generation endpoint |
| `MYAGENT_LOCAL_RAG_TIMEOUT_MS` | local-rag 요청 타임아웃 | `120000` | 밀리초 |
| `MYAGENT_LOCAL_RAG_TOKEN` | local-rag shared secret | 없음 | 설정 시 `x-local-rag-token` 헤더로 전달 |
| `MYAGENT_MEMORY_BASE_URL` | `mcp_obsidian` base URL | `http://127.0.0.1:8000` | durable memory health/bridge 대상 |
| `MYAGENT_MEMORY_MCP_PATH` | memory MCP mount path | `/chatgpt-mcp` | read-only MCP client target |
| `MYAGENT_MEMORY_BEARER_TOKEN` | memory MCP bearer token | 없음 | read-only mount가 bearer를 요구할 때만 사용 |
| `MCP_API_TOKEN` | memory bearer fallback | 없음 | `MYAGENT_MEMORY_BEARER_TOKEN`이 비었을 때 fallback |
| `MYAGENT_MEMORY_TIMEOUT_MS` | memory health 타임아웃 | `5000` | 밀리초 |
| `MYAGENT_PROXY_CORS_ORIGINS` | 허용 origin 목록 | 로컬 2개 | 콤마 구분 |
| `MYAGENT_PROXY_AUTH_TOKEN` | 프록시 인증 토큰 | 없음 | 퍼블릭 필수 |
| `MYAGENT_PROXY_ALLOW_SANITIZED_TO_COPILOT` | sanitize payload 외부 전송 허용 | `0` | 기본 권장값 유지 |
| `MYAGENT_PROXY_OPS_LOGS` | 운영 로그 on/off | `1` | `0`이면 콘솔 로그 제한 |
| `MYAGENT_HVDC_PREDICT_ENABLED` | HVDC 예측 API on/off | `1` | `0`이면 predict 비활성화 |
| `MYAGENT_HVDC_PREDICT_DIR` | predict 작업 디렉터리 | repo의 `predict/` | `predict2.py`, `runs/` 기준 |
| `MYAGENT_HVDC_PREDICT_PYTHON` | 예측용 Python 실행 파일 | `python` 또는 `predict/.venv` | 절대경로 권장 |
| `MYAGENT_HVDC_PREDICT_TIMEOUT_MS` | 예측 job 타임아웃 | `900000` | 밀리초 |
| `MYAGENT_HVDC_PREDICT_MAX_UPLOAD_MB` | 업로드 최대 크기 | `25` | `xlsx`만 허용 |
| `MYAGENT_HVDC_PREDICT_SHEET_NAME` | 기본 시트명 | `hvdc all status` | 요청에서 override 가능 |
| `OPENCLAW_STATE_DIR` | OpenClaw fallback state override | 없음 | 호환 경로 |
| `OPENCLAW_AGENT_DIR` | 특정 OpenClaw agent auth dir override | 없음 | 호환 경로 |

## 10. 로컬 실행 예시

### 10.1 PowerShell
```powershell
cd C:\path\to\standalone-package
pnpm install
pnpm build
pnpm login
$env:MYAGENT_HVDC_PREDICT_ENABLED="0"
$env:MYAGENT_LOCAL_RAG_TOKEN=$env:LOCAL_RAG_SHARED_SECRET
pnpm serve:local
```

predict까지 같이 쓰는 경우:

```powershell
$env:MYAGENT_HVDC_PREDICT_PYTHON="python"
pnpm serve:local
```

### 10.2 Bash
```bash
cd standalone-package
pnpm install
pnpm build
pnpm login
export MYAGENT_HVDC_PREDICT_ENABLED=0
export MYAGENT_LOCAL_RAG_TOKEN="$LOCAL_RAG_SHARED_SECRET"
pnpm serve:local
```

헬스체크:
```bash
curl http://127.0.0.1:3010/api/ai/health
```

## 11. 퍼블릭 실행 예시

### 11.1 환경변수 설정
```bash
export MYAGENT_PROXY_HOST=0.0.0.0
export MYAGENT_PROXY_PORT=3010
export MYAGENT_PROXY_AUTH_TOKEN=change-me
export MYAGENT_PROXY_CORS_ORIGINS=https://your-dashboard.vercel.app
export MYAGENT_PROXY_ALLOW_SANITIZED_TO_COPILOT=0
export MYAGENT_LOCAL_RAG_TOKEN=replace-with-local-rag-secret
```

### 11.2 실행
```bash
pnpm build
node dist/cli.js serve --host 0.0.0.0 --port 3010
```

### 11.3 공개 운영 필수 조건
- HTTPS 사용
- `MYAGENT_PROXY_AUTH_TOKEN` 사용
- `MYAGENT_PROXY_CORS_ORIGINS`에 실제 origin만 허용
- 브라우저에 원문 대용량 데이터 미전송

## 12. API 요청/응답 예시

### 12.1 `GET /api/ai/health`
```bash
curl http://127.0.0.1:3010/api/ai/health
```

응답 예시:
```json
{
  "ok": true,
  "chatOk": true,
  "partialChatOk": true,
  "copilotChatOk": true,
  "localOnlyChatOk": true,
  "memoryOk": true,
  "predictOk": true,
  "service": "myagent-copilot-standalone",
  "host": "127.0.0.1",
  "port": 3010,
  "authTokenRequired": false,
  "origins": [
    "http://127.0.0.1:4173",
    "http://127.0.0.1:18789"
  ]
}
```

위 예시는 diagnostics visibility가 허용된 경우의 full payload다. proxy auth가 켜진 공개 환경에서는 unauthenticated caller가 summary payload만 받을 수 있다.

- `ok`: 모든 자동 chat route class와 predict 경로가 함께 준비된 상태
- `chatOk`: Copilot route와 local-only route가 모두 준비된 상태
- `partialChatOk`: 둘 중 하나 이상의 chat route가 준비된 상태
- `copilotChatOk`: Copilot route 준비 상태
- `localOnlyChatOk`: secret/scope/RAG 계열 local-only route 준비 상태
- `memoryOk`: 외부 `mcp_obsidian`의 read-only MCP mount가 실제로 응답 가능한 상태
- `predictOk`: HVDC predict 경로 준비 상태
- proxy auth가 켜져 있으면 unauthenticated caller는 위 요약 필드만 받고, dependency 상세(`copilot`, `localRag`, `memory`, `predict`, `origins` 등)는 proxy token을 준 caller에게만 보인다

### 12.2 `POST /api/ai/chat`
```bash
curl -X POST http://127.0.0.1:3010/api/ai/chat \
  -H "Content-Type: application/json" \
  -H "x-request-id: demo-001" \
  -H "x-ai-sensitivity: internal" \
  -d '{
    "model": "github-copilot/gpt-5-mini",
    "sensitivity": "internal",
    "messages": [
      { "role": "system", "content": "입력 JSON 바깥 사실은 단정하지 말라." },
      { "role": "user", "content": "테스트 응답을 2줄로 반환하라." }
    ]
  }'
```

### 12.3 `GET /api/memory/search`
```bash
curl "http://127.0.0.1:3010/api/memory/search?q=gemma" \
  -H "x-ai-proxy-token: <MYAGENT_PROXY_AUTH_TOKEN>"
```

`standalone-package`가 내부 lightweight MCP client로 `mcp_obsidian`의 read-only `search` tool을 호출합니다.
기본 upstream mount는 `/chatgpt-mcp`이며, 이 read-only mount의 실제 접근 통제는 bearer보다 네트워크/프록시 레이어에 의존합니다.

### 12.4 `GET /api/memory/fetch`
```bash
curl "http://127.0.0.1:3010/api/memory/fetch?id=MEM-20260408-001753-89F237" \
  -H "x-ai-proxy-token: <MYAGENT_PROXY_AUTH_TOKEN>"
```

`mcp_obsidian`의 read-only `fetch` tool을 호출해 단일 memory note를 가져옵니다.

응답 예시:
```json
{
  "id": "MEM-20260408-011453-641FC4",
  "title": "KB: HVDC 물류 도메인 지식 온톨로지 작성 가이드 v2.0",
  "text": "HVDC 물류 프로세스를 Shipment 중심의 구조화된 지식 온톨로지로 정의하는 표준 작성 가이드라인이다.",
  "url": "obsidian://open?vault=...",
  "metadata": {
    "type": "project_fact",
    "project": "hvdc",
    "source": "obsidian-ingest",
    "tags": ["kb", "wiki", "analyses"]
  }
}
```

404 예시:
```json
{
  "id": "MEM-UNKNOWN",
  "title": "Not found",
  "text": "",
  "url": "",
  "metadata": {
    "status": "not_found"
  }
}
```

### 12.5 `GET /api/wiki/search`
```bash
curl "http://127.0.0.1:3010/api/wiki/search?q=hazmat" \
  -H "x-ai-proxy-token: <MYAGENT_PROXY_AUTH_TOKEN>"
```

`standalone-package`가 `mcp_obsidian`의 read-only `search_wiki` tool을 호출해 `wiki/analyses` 범위를 검색합니다.

### 12.6 `GET /api/wiki/fetch`
```bash
curl "http://127.0.0.1:3010/api/wiki/fetch?path=wiki/analyses/logistics_issue_shu_2025-11-26_3" \
  -H "x-ai-proxy-token: <MYAGENT_PROXY_AUTH_TOKEN>"
```

`standalone-package`가 `mcp_obsidian`의 read-only `fetch_wiki` tool을 호출해 wiki note 본문과 frontmatter를 가져옵니다.

### 12.7 `GET /api/search/unified`
```bash
curl "http://127.0.0.1:3010/api/search/unified?q=hazmat" \
  -H "x-ai-proxy-token: <MYAGENT_PROXY_AUTH_TOKEN>"
```

이 route는 public MCP tool이 아닙니다. `standalone-package` orchestration layer가 내부 fan-out으로 `searchMemory()`와 `searchWiki()`를 둘 다 호출하고, 결과를 source badge와 함께 병합해서 반환합니다.

### 12.5 `GET /api/memory/health`
```bash
curl http://127.0.0.1:3010/api/memory/health \
  -H "x-ai-proxy-token: <MYAGENT_PROXY_AUTH_TOKEN>"
```

이 endpoint는 `mcp_obsidian` root `/healthz` liveness와 read-only MCP contract probe(`search`, `fetch` only)를 함께 확인합니다.

### 12.5 `POST /api/hvdc/predict`
```bash
curl -X POST http://127.0.0.1:3010/api/hvdc/predict \
  -F "file=@C:/path/to/hvdc status2.xlsx"
```

응답 예시 (`202 Accepted`):
```json
{
  "jobId": "3aa74c44-c13c-4186-8859-2a8c5e7d7d18",
  "status": "queued",
  "createdAt": "2026-04-08T10:00:00.000Z",
  "startedAt": null,
  "finishedAt": null,
  "outputFile": null,
  "statusUrl": "/api/hvdc/predict/3aa74c44-c13c-4186-8859-2a8c5e7d7d18",
  "downloadUrl": "/api/hvdc/predict/3aa74c44-c13c-4186-8859-2a8c5e7d7d18/download",
  "error": null
}
```

상태 조회:
```bash
curl http://127.0.0.1:3010/api/hvdc/predict/<jobId>
```

취소:
```bash
curl -X POST http://127.0.0.1:3010/api/hvdc/predict/<jobId>/cancel
```

완료 파일 다운로드:
```bash
curl -L http://127.0.0.1:3010/api/hvdc/predict/<jobId>/download -o result.xlsx
```

### 12.6 Windows 배치 실행 메모
- `serve-local.bat`와 `serve-public.bat`는 repo 내 `..\..\predict\predict2.py`가 있으면 `MYAGENT_HVDC_PREDICT_DIR`를 자동으로 잡습니다.
- `predict\.venv\Scripts\python.exe`가 있으면 `MYAGENT_HVDC_PREDICT_PYTHON`도 자동 설정합니다.
- 둘 다 없으면 `python` PATH 실행에 의존하므로 `python --version`이 먼저 동작해야 합니다.

## 13. 로그와 운영 관측
- 로그 스키마: `openclaw.copilot.proxy.log.v1`
- requestId, route, dlpStatus, latency, usage를 중심으로 관측
- 원문 payload 전체를 로그에 남기지 않음

## 14. 배포 zip 사용법

### 14.1 생성
```bash
pnpm export:zip
```
또는
```powershell
.\export-release.bat
```

### 14.2 결과물
- `release/myagent-copilot-standalone-v0.1.0.zip`

### 14.3 사용
1. zip을 새 서버나 새 저장소로 복사
2. 압축 해제
3. `pnpm install --frozen-lockfile`
4. `pnpm build`
5. 환경변수 설정
6. `node dist/cli.js serve ...`

## 15. 비용/사용량 해석
- quota delta가 보이지 않으면 `무차감 관측`
- 이것은 실측 표현일 뿐, GitHub 정책 차원의 영구 무료를 의미하지 않음
- 따라서 문서 표준 표현은 `정책상 무제한 확정 불가`

## 16. 자주 묻는 질문

### 16.1 OpenClaw 없이도 되나
됩니다. 현재 기준 운영안은 standalone package입니다.

### 16.2 OpenClaw auth store를 계속 써도 되나
가능하지만 호환 경로입니다. 장기적으로는 `~/.myagent-copilot`로 수렴하는 것이 맞습니다.

### 16.3 대시보드에서 바로 붙일 수 있나
가능합니다. 다만 payload 최소화, CORS, 토큰 인증, HTTPS를 같이 설계해야 합니다.

## 운영 공통 블록
### 검증 명령
```bash
pnpm build
pnpm health
pnpm token
pnpm usage
pnpm export:zip
```

### 주의사항
- 공개 환경에서 브라우저 직접 호출 구조를 유지한다면 프록시 토큰 노출 위험을 별도로 관리해야 합니다.
- 기본 모델을 바꾸더라도 문서의 기준값은 `github-copilot/gpt-5-mini`로 유지하고, 실제 변경은 별도 운영 문서에서 승인 절차와 함께 기록하는 것이 좋습니다.

### 다음에 읽을 문서
- `OPERATIONS.md`

### 변경 이력/기준일
- 2026-03-10: standalone package 설치 매뉴얼 수준 README로 전면 재작성
