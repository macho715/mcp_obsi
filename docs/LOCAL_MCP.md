# Local MCP (Cursor + 이 레포)

## 이게 “기능”인가?

Cursor에 **별도의 “Local MCP” 토글이나 내장 서버는 없습니다.**  
이 저장소에서 말하는 **로컬 MCP**는 다음 한 가지 조합입니다.

1. **이 레포의 FastAPI 앱**이 `http://127.0.0.1:8000/mcp` 에서 **Streamable HTTP MCP**를 제공한다.
2. Cursor는 프로젝트의 **`.cursor/mcp.json`** 안 **`obsidian-memory-local`** 항목으로 그 URL에 붙는다.

서버 프로세스(uvicorn)를 띄우지 않으면 Cursor 쪽 `obsidian-memory-local`은 연결 오류가 난다. 이는 “기능 누락”이 아니라 **런타임 미기동**에 가깝다.

## 어디에 이미 적혀 있나 (중복 안내)

| 문서 | 내용 |
|------|------|
| [README.md](../README.md) | `## Cursor MCP`, Quick Start의 uvicorn, `check_cursor_mcp_status.ps1` |
| [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md) | 토큰, 로컬 FastAPI 실행, MCP 점검 |
| [AGENTS.md](../AGENTS.md) | `uvicorn` 명령, 도구 목록, `MCP_API_TOKEN` 계약 |
| [CONTRIB.md](CONTRIB.md) | 로컬 API 실행 절차 |
| [.cursor/mcp.sample.json](../.cursor/mcp.sample.json) | `obsidian-memory-local` URL·헤더 템플릿 |

이 파일은 위 내용을 **한곳에서** 따라가기 쉽게 모은 허브다.

## 절차 (최소)

1. **의존성**  
   `/mcp` 가 실제로 동작하려면 MCP 스택이 필요하다.  
   `pip install -e ".[dev,mcp]"` 또는 `uv sync --extra dev --extra mcp` ( [AGENTS.md](../AGENTS.md) ).  
   없으면 `/mcp` 가 **503** 과 안내 메시지로 응답할 수 있다 ([INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)).

2. **`.env`**  
   `MCP_API_TOKEN`, `VAULT_PATH`, `INDEX_DB_PATH` 등 ([CONTRIB.md](CONTRIB.md)).  
   `scripts/start-mcp-dev.ps1`로 시작하면 `OBSIDIAN_LOCAL_VAULT_PATH`가 있을 때 해당 값이 `VAULT_PATH`보다 우선 적용된다.

3. **Windows 사용자 환경 변수**  
   Cursor가 `${env:MCP_API_TOKEN}` 를 펼치려면 **사용자** 또는 Cursor가 물려 받는 환경에 `MCP_API_TOKEN` 이 있어야 한다 ([INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)).  
   값은 **서버의 effective `MCP_API_TOKEN` (`.env` 또는 환경변수)** 와 동일해야 `/mcp` 가 **401** 이 되지 않는다.

4. **서버 기동**

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\start-mcp-dev.ps1
   ```

   또는:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Cursor**  
   프로젝트를 이 레포 루트로 연 뒤 **Settings → MCP** 에서 `obsidian-memory-local` 상태 확인. 환경 변수 바꿨으면 Cursor **재시작**.

## 빠른 검증

```powershell
# 앱 살아 있음 (Bearer 불필요)
Invoke-WebRequest http://127.0.0.1:8000/healthz -UseBasicParsing

# Cursor 설정·환경·로컬/프로덕션 헬스 한 번에
powershell -ExecutionPolicy Bypass -File .\scripts\check_cursor_mcp_status.ps1
```

## 자주 나는 증상

| 증상 | 흔한 원인 |
|------|-----------|
| Cursor `obsidian-memory-local` 연결 실패 | **8000** 에 uvicorn 미기동, 방화벽/포트 충돌 |
| **401** on `/mcp` | Cursor의 `MCP_API_TOKEN` ≠ 서버의 effective `MCP_API_TOKEN` |
| **503** on `/mcp` | **`[mcp]` extra** 미설치 또는 MCP 앱 마운트 실패 |

## 프로덕션과의 차이

- **로컬**: `http://127.0.0.1:8000/mcp` + `MCP_API_TOKEN`, vault는 로컬 `VAULT_PATH`.
- **프로덕션**: `.cursor/mcp.json` 의 `obsidian-memory-production` + `MCP_PRODUCTION_BEARER_TOKEN` (README `## Cursor MCP`).

비밀값·실경로는 문서나 커밋에 넣지 않는다 ([docs/CLAUDE_COWORK_MCP_OUTSOURCE_BRIEF.md](CLAUDE_COWORK_MCP_OUTSOURCE_BRIEF.md)).
