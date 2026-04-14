# obsidian-mcp-mvp

Obsidian Vault를 정본(SSOT)으로 쓰는 기억용 MCP 서버 예시입니다.

## 기능

- Markdown front matter + body 저장
- SQLite 인덱스
- FastAPI `/healthz`
- FastMCP `/mcp`
- Cursor / Claude Code / OpenAI / Anthropic 연동 예시
- Daily note append

## 툴

- `search_memory`
- `save_memory`
- `get_memory`
- `list_recent_memories`
- `update_memory`
- `search` (호환 래퍼)
- `fetch` (호환 래퍼)

## 구조

```text
obsidian-mcp-mvp/
├─ app/
├─ examples/
├─ scripts/
├─ .env.example
├─ pyproject.toml
└─ README.md
```

## 설치

### PowerShell
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

## 실행

```powershell
copy .env.example .env
# .env 수정
.\scripts\run_dev.ps1
```

또는:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
```

## 엔드포인트

- Health: `http://127.0.0.1:8765/healthz`
- MCP: `http://127.0.0.1:8765/mcp`

## Cursor 연결

`%USERPROFILE%\.cursor\mcp.json`

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

## Vault 권장 구조

```text
<your-vault>/
├─ 10_Daily/
├─ 20_AI_Memory/
└─ 90_System/
```

## public API 연동 시 주의

OpenAI Responses API와 Anthropic Messages API MCP connector는 remote MCP 서버가 public HTTP(S)로 노출돼야 합니다.
로컬 개발 단계에서는 Cursor/Claude Code로 먼저 검증한 뒤 public HTTPS로 확장하는 편이 안전합니다.
