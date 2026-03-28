# Windows + Cursor + Obsidian 실전 셋업

## 1. 목표

이 문서는 Windows에서 아래 구성을 바로 띄우는 절차다.

- Obsidian Vault를 기억 저장소로 사용
- FastAPI + FastMCP 서버 실행
- Cursor에서 MCP로 연결
- 필요 시 나중에 OpenAI / Anthropic API까지 확장

---

## 2. 권장 경로

### 2.1 Vault 경로
권장 예시:

```text
C:\Users\jichu\Documents\ObsidianVaults\ai-memory-vault
```

### 2.2 코드 경로
권장 예시:

```text
C:\Users\jichu\Downloads\mcp_obsidian\obsidian-mcp-mvp
```

---

## 3. Obsidian 준비

1. Obsidian 설치
2. `Open folder as vault` 선택
3. 아래 폴더를 vault 루트에 생성

```text
10_Daily
20_AI_Memory
90_System
```

4. Daily Notes 플러그인 활성화
5. 필요 시 아래 옵션 점검
   - Automatically update internal links = ON
   - Default location for new notes = vault root 또는 지정 폴더
   - Hidden `.obsidian` 폴더 백업 권장

---

## 4. Python 환경 준비

PowerShell:

```powershell
cd C:\Users\jichu\Downloads\mcp_obsidian\obsidian-mcp-mvp

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e .
```

`pip install -e .`가 어려우면:

```powershell
pip install fastapi "uvicorn[standard]" "mcp[cli]" pydantic pydantic-settings pyyaml
```

---

## 5. 환경변수 설정

`.env` 파일 생성:

```env
VAULT_PATH=C:\Users\jichu\Documents\ObsidianVaults\ai-memory-vault
INDEX_DB_PATH=data\memory_index.sqlite3
MCP_API_TOKEN=change-this-token
TIMEZONE=Asia/Dubai
HOST=127.0.0.1
PORT=8765
```

---

## 6. 서버 실행

### 6.1 PowerShell 직접 실행

```powershell
cd C:\Users\jichu\Downloads\mcp_obsidian\obsidian-mcp-mvp
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
```

정상 기동 확인:

- Health: `http://127.0.0.1:8765/healthz`
- MCP: `http://127.0.0.1:8765/mcp`

### 6.2 제공 스크립트 사용

```powershell
.\scripts\run_dev.ps1
```

---

## 7. Cursor 연결

## 7.1 전역 MCP 설정 파일

최신 문서 기준 예시는 아래 형식이다.

파일:
```text
%USERPROFILE%\.cursor\mcp.json
```

내용:
```json
{
  "mcpServers": {
    "obsidianMemory": {
      "url": "http://127.0.0.1:8765/mcp",
      "headers": {
        "Authorization": "Bearer change-this-token"
      }
    }
  }
}
```

Cursor 재시작 후 Agent/Composer에서 MCP 도구가 보이는지 확인한다.

## 7.2 프로젝트 규칙 권장

`.cursorrules`만 쓰지 말고 아래를 권장한다.

```text
.cursor/rules/obsidian-memory.mdc
```

예시 규칙:

```mdc
---
description: Use Obsidian memory MCP for project memory lookup and durable note writes.
alwaysApply: false
---

- 먼저 `search_memory`로 관련 결정을 찾는다.
- 새 결정이 생기면 `save_memory`로 남긴다.
- 기존 결정 변경은 `update_memory`를 사용한다.
- 민감 데이터는 저장 전 마스킹한다.
```

---

## 8. Cursor에서 바로 테스트할 프롬프트

```text
search_memory로 최근 decision 메모를 찾아 요약해줘.
```

```text
save_memory를 사용해서 "HVDC UAE 창고 경고 규칙"이라는 decision 메모를 저장해줘.
내용은 "occupancy 85% 초과 시 창고 경고 발송"이다.
```

```text
list_recent_memories로 최근 5개 메모를 보여줘.
```

---

## 9. Obsidian 확인 포인트

서버가 `save_memory`를 성공하면 아래 둘 다 갱신돼야 한다.

1. `20_AI_Memory/<type>/YYYY/MM/*.md`
2. `10_Daily/YYYY-MM-DD.md`

---

## 10. OpenAI / Anthropic API 확장 시 주의

### OpenAI Responses API
- public HTTPS endpoint 필요
- remote MCP server는 Streamable HTTP 또는 HTTP/SSE 지원 필요

### Anthropic Messages API MCP connector
- public HTTPS endpoint 필요
- `betas=["mcp-client-2025-04-04"]`
- 현재 tool calls only

즉, 로컬 Cursor 검증이 끝난 뒤
- Cloudflare Tunnel
- ngrok
- 사내 reverse proxy
중 하나로 public endpoint를 만든 다음 API 연동으로 넘어가면 된다.

---

## 11. 공개 배포 권장

### 11.1 최소 구성
- HTTPS
- Bearer token
- IP 제한 또는 VPN
- access log
- vault 백업

### 11.2 권장 추가
- write tool 승인 분리
- rate limit
- 민감 메모 masking
- SQLite 백업 및 rotate

---

## 12. 트러블슈팅

### 12.1 `/mcp` 접속 시 307 redirect
FastMCP + Starlette 조합에서 trailing slash 이슈가 날 수 있다.
현재 제공 코드에서는 mount path를 `/mcp`로 고정하고 내부 streamable path를 `/`로 맞춰 회피했다.

### 12.2 Cursor에 도구가 안 뜸
- Cursor 재시작
- `mcp.json` 문법 확인
- 서버 기동 여부 확인
- 토큰 헤더 확인
- URL 끝 경로가 `/mcp`인지 확인

### 12.3 Obsidian에 파일이 안 보임
- vault 경로 재확인
- 같은 폴더를 vault로 열었는지 확인
- 파일이 `20_AI_Memory` 하위에 생성됐는지 확인
- Obsidian 창 새로고침

### 12.4 Daily note append 실패
- `10_Daily` 폴더 존재 확인
- 파일 권한 확인
- 날짜 포맷 확인

---

## 13. 추천 운영 순서

1. 로컬 vault 생성
2. 로컬 FastAPI/FastMCP 실행
3. Cursor 연결
4. 저장/검색 테스트
5. 승인 정책 확정
6. public HTTPS 노출
7. OpenAI / Anthropic API 연동
