판정: **예 — 이 repo는 `Claude Code용 wiki 컴파일러`로 바꾸는 것보다, `Cursor 전용 MCP control plane + 외부 Obsidian vault`로 변환하는 것이 맞습니다.** Cursor는 Project/User/Team Rules와 `AGENTS.md`, MCP, hooks, ignore file을 공식 지원하고, 이 repo도 이미 `.cursor/rules/*.mdc`, `.cursor/hooks.json`, `.cursorignore`, `.cursor/mcp.sample.json`을 갖고 있습니다. ([Cursor][1])
근거: repo 자체 문서상 Cursor는 `/mcp`를 통해 vault markdown SSOT, `mcp_raw` archive, `10_Daily`, SQLite derived index와 연결되고, `AGENTS.md`는 shared SSOT, `CLAUDE.md`는 Claude-specific delta only입니다. 또 2026-03 기준 Cursor 커뮤니티/직원 포럼에서는 folder-based `RULE.md`보다 `.mdc`가 실제로 더 안정적으로 인식되는 known issue/workaround가 계속 보고되어, 실무상 이 repo처럼 `.cursor/rules/*.mdc`를 유지하는 편이 안전합니다. ([GitHub][2])
다음행동: **`CLAUDE.md + raw/wiki` 패턴은 버리고, 아래 Cursor 전용 최종안대로 `AGENTS.md + .cursor/rules/*.mdc + .cursor/mcp.json + 외부 vault` 구조로 정리하십시오.**

## Cursor 전용 최종안

### 0) 구조를 먼저 바꾸십시오

이 캡처 가이드는 “한 폴더를 vault로 열고, `raw/`를 넣고, LLM이 `wiki/`를 만든다”는 흐름입니다.
하지만 `mcp_obsidian` repo는 그 구조가 아닙니다. 이 repo는 **code/control plane**이고, 실제 지식 저장소는 **외부 Obsidian vault**입니다. README runtime overview도 Cursor가 `/mcp`로 접속하고, backend가 vault markdown SSOT, `mcp_raw`, `10_Daily`, SQLite index를 다루는 구조로 설명합니다. `LAYOUT.md`도 `vault/`는 Markdown SSOT, `data/`는 index/runtime data로 분리합니다. ([GitHub][2])

따라서 최종 구조는 이렇게 잡는 것이 맞습니다.

```text
[Cursor에서 여는 것]
mcp_obsidian/
  AGENTS.md
  .cursor/
    rules/*.mdc
    hooks.json
    mcp.json
  .cursorignore
  app/
  scripts/
  schemas/
  ...

[Obsidian에서 여는 것]
<your-vault>/
  mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md
  memory/<YYYY>/<MM>/<MEMORY_ID>.md
  10_Daily/<YYYY-MM-DD>.md
  90_System/
```

## 1) `CLAUDE.md` 중심이 아니라 `AGENTS.md + .cursor/rules/*.mdc` 중심으로 바꾸십시오

Cursor 공식 docs는 persistent instructions를 Project Rules, Team Rules, User Rules, 그리고 `AGENTS.md`로 운영한다고 설명합니다. 이 repo도 이미 `AGENTS.md`를 shared project contract로 두고, `CLAUDE.md`는 “Claude-specific delta only”라고 명시합니다. 따라서 **Cursor 전용 변환안의 SSOT는 `AGENTS.md`**이고, 세부 강제는 `.cursor/rules/*.mdc`로 쪼개는 것이 맞습니다. ([Cursor][1])

또한 현재 실무상 `.mdc`를 유지하는 것이 안전합니다. 공식 docs는 Rules를 설명하지만, 2025-12~2026-03 포럼에서는 folder-based `RULE.md`/`.md` 인식 이슈가 계속 보고되었고, `.mdc`가 workaround로 안내됐습니다. 이 repo가 이미 `000-core.mdc`, `010-plan-mode.mdc`, `020-mcp-contracts.mdc`, `030-security-privacy.mdc`, `040-python-quality.mdc`, `050-cursor-ops-2026.mdc`를 쓰는 것도 그 방향과 맞습니다. ([Cursor][1])

### 권장 운영 원칙

* `AGENTS.md` = 저장소 공통 SSOT
* `.cursor/rules/*.mdc` = Cursor 전용 강제 규칙
* `CLAUDE.md` = 삭제 또는 deprecate 메모로 축소
* 새 규칙은 `.mdc`로 추가

## 2) `raw/wiki`가 아니라 `mcp_raw/memory`로 변환하십시오

이 repo의 계약은 이미 정해져 있습니다.

* raw archive: `mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md`
* current memory write: `memory/<YYYY>/<MM>/<MEMORY_ID>.md`
* legacy compatibility: `20_AI_Memory/<memory_type>/<YYYY>/<MM>/...`
* daily append: `10_Daily/<YYYY-MM-DD>.md`
* tool names: `search_memory`, `save_memory`, `get_memory`, `list_recent_memories`, `update_memory`, `archive_raw`, `search`, `fetch` ([GitHub][3])

즉, 캡처 가이드의 아래 매핑으로 바꾸면 됩니다.

* `raw/` → `mcp_raw/`
* `wiki/concepts/`, `wiki/topics/` → **없앰**
* `wiki/` 결과물 → `memory/`
* `_index.md` 중심 운영 → `90_System/` + derived index
* “compile a wiki” → “archive raw, then curate durable memory notes”

repo `AGENTS.md`도 raw/memory tree는 **chronological fixed segment**로 유지하고, extra semantic path level을 invent하지 말라고 적고 있습니다. 또 “one conversation = one raw note, zero-to-many memory notes” 원칙을 둡니다. 즉, Cursor는 `wiki`를 만드는 agent가 아니라 **raw를 archive하고 durable memory를 normalize하는 agent**로 써야 합니다. ([GitHub][4])

## 3) MCP 연결은 global 대신 project-local로 내리십시오

README상 **현재 active Cursor MCP 설정은 global config**에 있고, local/production 두 서버를 함께 씁니다. 반면 repo의 `050-cursor-ops-2026.mdc`는 **project-local `.cursor/mcp.json` 선호**, `.cursor/mcp.sample.json` 보존, token flow는 env-driven을 명시합니다. Cursor 공식 MCP docs도 external tools/data를 MCP로 연결하는 방식을 안내합니다. 따라서 Cursor 전용 최종안은 다음입니다. ([GitHub][2])

* repo에는 `.cursor/mcp.sample.json` 유지
* 실제 사용은 로컬 `.cursor/mcp.json`
* token은 env로만 주입
* vault path는 `OBSIDIAN_LOCAL_VAULT_PATH`로 외부 vault를 가리킴

### 붙여넣기용 `.cursor/mcp.json`

아래처럼 두 서버를 두면 됩니다. sample의 구조를 유지하되 production URL만 현재 운영값으로 바꾸십시오.

```json
{
  "mcpServers": {
    "obsidian-memory-local": {
      "url": "http://127.0.0.1:8000/mcp",
      "headers": {
        "Authorization": "Bearer ${env:MCP_API_TOKEN}"
      }
    },
    "obsidian-memory-production": {
      "url": "<YOUR_PUBLIC_MCP_URL>",
      "headers": {
        "Authorization": "Bearer ${env:MCP_PRODUCTION_BEARER_TOKEN}"
      }
    }
  }
}
```

## 4) Cursor 전용 규칙 파일 1개를 추가하면 끝납니다

repo에는 이미 core/plan/security/python/cursor-ops 규칙이 있으므로, 캡처 가이드의 “CLAUDE.md에서 wiki 작성법을 장문으로 설명”하는 부분은 **한 개의 Cursor rule**로 바꾸는 것이 가장 깔끔합니다. 이 접근은 Cursor의 Project Rules 모델과도 맞고, repo 구조와도 맞습니다. ([Cursor][1])

### `.cursor/rules/060-vault-curation.mdc`

```md
---
description: Cursor-only Obsidian vault curation workflow for mcp_obsidian.
alwaysApply: true
---

- Treat `AGENTS.md` as the shared repository SSOT.
- This repo is the control plane; the real Obsidian vault is the data plane.
- Do not create `raw/`, `wiki/`, `wiki/concepts/`, or `wiki/topics/` in this repo.
- Use the existing storage contracts only:
  - raw archive: `mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md`
  - memory: `memory/<YYYY>/<MM>/<MEMORY_ID>.md`
  - daily: `10_Daily/<YYYY-MM-DD>.md`
  - system: `90_System/`
- One conversation becomes one raw note. One conversation may yield zero to many memory notes.
- Use MCP tools first for memory operations: `archive_raw`, `save_memory`, `update_memory`, `search_memory`, `get_memory`, `list_recent_memories`.
- Keep markdown-first persistence authoritative. SQLite is a derived accelerator only.
- Never reintroduce folder-based semantic classification.
- Before reporting completion, list files touched, commands run, verification status, and remaining assumptions or risks.
```

## 5) memory note는 schema 기준으로 쓰십시오

schema상 `memory_item`은 `memory_id`, `memory_type`, `source`, `created_by`, `created_at_utc`, `updated_at_utc`, `title`, `content` 등이 required이고, `memory_type` enum은 `preference`, `project_fact`, `decision`, `person`, `todo`, `conversation_summary`입니다. `status`는 `active`, `superseded`, `archived`를 씁니다. ([GitHub][5])

### 붙여넣기용 memory frontmatter 예시

```yaml
---
schema_type: memory_item
memory_id: MEM-20260408-105100-A1B2C3
memory_type: decision
source: cursor_mcp
created_by: MR.CHA
created_at_utc: 2026-04-08T06:51:00Z
updated_at_utc: 2026-04-08T06:51:00Z
title: Cursor-only vault architecture
project: hvdc
tags:
  - project/hvdc
  - source/cursor
  - type/decision
confidence: 0.85
status: active
sensitivity: internal
---

Cursor-only 운영에서는 repo를 control plane으로 두고,
실제 vault는 external Obsidian vault로 유지한다.
`raw/wiki` 구조는 사용하지 않고 `mcp_raw/memory/10_Daily/90_System`만 사용한다.
```

## 6) `.cursorignore`와 hooks는 그대로 살리되, 더 무겁게 만들지 마십시오

Cursor 공식 docs는 `.cursorignore`와 `.cursorindexingignore`로 Cursor가 접근할 파일을 제어한다고 설명합니다. 이 repo도 이미 `.env`, `data/`, logs, hook state, archive 등을 `.cursorignore`로 제외하고 있습니다. hooks도 공식 기능이고, repo는 `beforeShellExecution`에 `shell_guard.py`, `afterShellExecution`에 `shell_log.py`를 연결해 둔 상태입니다. `050-cursor-ops-2026.mdc` 역시 hooks는 lightweight, shell-focused, Windows-stable로 유지하라고 적습니다. ([Cursor][6])

즉, Cursor-only 변환은 다음 원칙이면 충분합니다.

* `.cursorignore`는 유지
* hooks는 지금처럼 guard/log 수준 유지
* shell automation은 넓히지 않음
* high-risk contract 변경은 plan-first

repo의 `010-plan-mode.mdc`와 `030-security-privacy.mdc`도 auth flow, endpoint shape, tool schema, write 범위 확대는 plan-first / approval-first로 다루라고 명시합니다. ([GitHub][7])

## 7) Cursor용 prompt pack

아래 4개로 캡처 가이드의 Claude prompts를 대체하면 됩니다.
이 prompt들은 repo의 tool surface와 storage contract에 맞춘 Cursor 전용 버전입니다. ([GitHub][8])

### A. Bootstrap

```text
Read AGENTS.md and all .cursor/rules/*.mdc first.
Confirm the current MCP contract, storage layout, and verification rules.
Do not invent raw/wiki/topic folder structures.
Propose only minimal diffs for Cursor-only operation.
```

### B. Raw archive

```text
Use MCP tool archive_raw to persist this conversation as one raw note.
Source=<cursor|chatgpt|meeting|webclip>.
Do not create wiki pages.
After archiving, decide whether this raw note should produce 0..n durable memory notes.
```

### C. Curate durable memory

```text
Read the latest raw note(s) and create only durable memory items.
Use memory_type from the schema enum only:
preference, project_fact, decision, person, todo, conversation_summary.
Write to memory/YYYY/MM with markdown-first authority.
If information is transient or duplicate, do not create a memory note.
```

### D. Incremental update / health check

```text
Search existing memories first.
If a fact changed, update the existing memory or mark old status as superseded.
Check for:
- path contract violations
- missing required frontmatter
- invalid memory_id pattern
- raw notes with no useful durable extraction
Report pass/fail/manual only.
```

## 8) 최종 적용 순서

1. `CLAUDE.md` 의존을 끊고 `AGENTS.md + .cursor/rules/*.mdc`를 SSOT 체계로 고정합니다. `CLAUDE.md`는 삭제하거나 deprecate note로 축소하는 편이 낫습니다. repo 자체도 `CLAUDE.md`를 delta only로 정의합니다. ([GitHub][9])
2. `.cursor/mcp.sample.json`을 기준으로 로컬 `.cursor/mcp.json`을 만들고, `MCP_API_TOKEN`, `MCP_PRODUCTION_BEARER_TOKEN`, `OBSIDIAN_LOCAL_VAULT_PATH`를 env로 연결합니다. README는 현재 active config가 global이며 local/production 두 서버를 확인하는 흐름을 제시합니다. ([GitHub][2])
3. 외부 Obsidian vault는 `mcp_raw/`, `memory/`, `10_Daily/`, `90_System/`만 유지합니다. `raw/wiki/concepts/topics`는 버립니다. ([GitHub][3])
4. Cursor Agent는 MCP tools와 terminal을 사용하되, verification은 repo rule대로 `pass/fail/manual`로 보고합니다. `040-python-quality.mdc`는 `pytest -q`, `ruff check .`, `ruff format --check .`를 기본 check로 제시합니다. Cursor terminal docs도 sandboxed terminal execution을 안내합니다. ([GitHub][10])

**한 줄 결론:**
이 repo의 Cursor 전용 변환은 **`CLAUDE.md + raw/wiki`를 Cursor로 단순 치환하는 작업이 아니라, `AGENTS.md + .cursor/rules/*.mdc + MCP + external vault`로 재배선하는 작업**입니다. 이 방식이 공식 Cursor 기능, 현재 repo 구조, 그리고 실제 운영 계약에 가장 잘 맞습니다. ([Cursor][1])

[1]: https://cursor.com/docs/rules?utm_source=chatgpt.com "Rules | Cursor Docs"
[2]: https://github.com/macho715/mcp_obsidian/blob/main/README.md "mcp_obsidian/README.md at main · macho715/mcp_obsidian · GitHub"
[3]: https://github.com/macho715/mcp_obsidian/blob/main/.cursor/rules/020-mcp-contracts.mdc "mcp_obsidian/.cursor/rules/020-mcp-contracts.mdc at main · macho715/mcp_obsidian · GitHub"
[4]: https://github.com/macho715/mcp_obsidian/blob/main/AGENTS.md "mcp_obsidian/AGENTS.md at main · macho715/mcp_obsidian · GitHub"
[5]: https://github.com/macho715/mcp_obsidian/blob/main/schemas/memory-item.schema.json "mcp_obsidian/schemas/memory-item.schema.json at main · macho715/mcp_obsidian · GitHub"
[6]: https://cursor.com/docs/reference/ignore-file?utm_source=chatgpt.com "Ignore File | Cursor Docs"
[7]: https://github.com/macho715/mcp_obsidian/blob/main/.cursor/rules/010-plan-mode.mdc "mcp_obsidian/.cursor/rules/010-plan-mode.mdc at main · macho715/mcp_obsidian · GitHub"
[8]: https://github.com/macho715/mcp_obsidian/blob/main/SYSTEM_ARCHITECTURE.md "mcp_obsidian/SYSTEM_ARCHITECTURE.md at main · macho715/mcp_obsidian · GitHub"
[9]: https://github.com/macho715/mcp_obsidian/blob/main/CLAUDE.md "mcp_obsidian/CLAUDE.md at main · macho715/mcp_obsidian · GitHub"
[10]: https://github.com/macho715/mcp_obsidian/blob/main/.cursor/rules/040-python-quality.mdc "mcp_obsidian/.cursor/rules/040-python-quality.mdc at main · macho715/mcp_obsidian · GitHub"


판정: **조건부 — `검색/질의 성능`은 새 `Cursor + mcp_obsidian`가 더 좋고, `초기 구축 속도`는 기존 `raw/wiki` 방식이 더 좋습니다. 당신 용도 기준 최종 승자는 새 시스템입니다.** 기존 LLM Wiki는 small scale에서 `_index`만으로도 가능하지만, 규모가 커지면 proper search engine이 필요하다고 직접 말합니다. 반면 `mcp_obsidian`는 처음부터 Markdown SSOT 위에 SQLite JSON1+FTS5, `bm25()`, metadata filter, derived index를 얹습니다. ([Gist][1])
근거: 기존 방식은 `raw sources + wiki + schema`의 3계층으로 단순하고, LLM이 위키를 유지·갱신하는 데 강점이 있습니다. 하지만 새 시스템은 `mcp_raw/<source>/<date>`, `memory/YYYY/MM`, `10_Daily`로 저장 단위를 고정하고, 폴더명이 아니라 frontmatter/index metadata를 주 API로 삼으며, 검색 시 자유 텍스트는 FTS5, 구조 필터는 `json_each(...)`로 처리합니다. 반복 조회·정확 필터·증분 운영에서는 구조적으로 더 유리합니다. ([Gist][1])
다음행동: **논문/자료 10~30개를 빨리 wiki화**하려면 기존 방식, **meeting/decision/project_fact/todo를 장기 누적**하려면 새 시스템으로 가십시오. Cursor도 Rules, `AGENTS.md`, MCP, hooks를 공식 지원하고, 이 repo 역시 Cursor에서 local/production MCP 서버를 확인한 상태입니다. ([Cursor][2])

## 구조 benchmark

⚠️AMBER: **공개된 A/B latency(ms) benchmark는 보이지 않았습니다.** 아래 평가는 공식 문서와 저장소 문서 기반의 **구조 benchmark**입니다. Karpathy 문서는 구현이 아니라 “pattern” 자체를 설명하는 abstract note이고, `mcp_obsidian` 문서는 아키텍처·검증 흐름을 설명합니다. ([Gist][1])

### 1) 초기 구축 속도

**기존 `raw/wiki` 방식 우세**입니다.
이유는 간단합니다. Karpathy 패턴은 `raw sources`, `wiki`, `schema` 3계층만 두고 시작하며, small scale에서는 index file만으로도 충분하다고 설명합니다. 즉, 바로 시작하는 비용이 낮습니다. 반면 `mcp_obsidian`는 FastAPI/FastMCP runtime, Markdown SSOT, SQLite derived index, MCP config, env, local/production route 확인까지 포함하므로 초기 셋업은 더 무겁습니다. ([Gist][1])

### 2) 검색·질의 성능

**새 `Cursor + mcp_obsidian` 우세**입니다.
기존 패턴도 훌륭하지만, 본문에서 직접 “wiki가 커지면 proper search가 필요하다”고 말합니다. 반면 `mcp_obsidian`는 이미 JSON1+FTS5 search layer를 두고, 자유 텍스트는 `FTS5 MATCH + bm25()`, 구조 검색은 `json_each(...) EXISTS`, 텍스트가 없으면 metadata-only SQL path로 분기합니다. 이건 단순 `_index.md`/파일 탐색보다 질의 precision과 recall을 높이기 쉬운 구조입니다. ([Gist][1])

### 3) Context 효율

**새 시스템 우세**입니다.
이 repo는 `One conversation = one raw note`, 그리고 `one conversation may yield zero to many memory notes`를 원칙으로 둡니다. 또 retrieval은 폴더명이 아니라 frontmatter와 index metadata를 기준으로 하라고 명시합니다. 이 구조는 질문 때 raw 대화 전체나 wiki page 덩어리를 읽는 대신, 더 작은 durable fragment를 hit시키기 쉬워서 **context 낭비를 줄이는 방향**이라고 보는 것이 합리적입니다. 이것은 문서 구조에서 도출한 제 판단입니다. ([GitHub][3])

### 4) 증분 업데이트와 운영 안정성

**새 시스템 우세**입니다.
기존 방식도 ingest/query/lint 흐름이 좋고 “compiled wiki”라는 강점이 있습니다. 다만 새 시스템은 path backfill 도구, legacy compatibility, auth/healthz, targeted tests까지 포함해 운영 계약이 더 명시적입니다. `20 passed` 검증, path migration dry-run/apply, production health checks가 문서화되어 있어 장기 운영 관점에서는 더 재현성이 높습니다. ([GitHub][4])

### 5) 유지보수 단순성

**기존 방식 우세**입니다.
Karpathy 패턴은 위키 유지 자체를 LLM에게 맡기고, 사람은 source curate와 질문에 집중하라고 설명합니다. 구현 세부도 intentionally abstract라서 도메인에 맞게 가볍게 시작할 수 있습니다. 반면 새 시스템은 schema, path contract, index, route, MCP auth까지 관리해야 하므로 단순성은 떨어집니다. ([Gist][1])

## 최종 결론

**무엇이 더 빠르냐**를 한 줄로 정리하면:

* **처음 1주**: 기존 `raw/wiki`가 더 빠릅니다.
* **3개월 운영 후 검색/재사용/정확도**: 새 `Cursor + mcp_obsidian`가 더 좋습니다.
* **당신 같은 업무형 vault**: 새 시스템이 맞습니다. `decision`, `project_fact`, `todo`, `person`, `conversation_summary`를 쪼개 저장하고 exact filter로 다시 찾는 구조가 업무 memory에 훨씬 유리하기 때문입니다. ([Gist][1])

원하시면 다음 답변에서 **“기존 시스템 vs 새 시스템” 7개 KPI(검색속도, 정확도, 유지비, 셋업시간, scale, token cost, auditability) 점수표**로 바로 정리해드리겠습니다.

[1]: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f "llm-wiki · GitHub"
[2]: https://cursor.com/docs/rules?utm_source=chatgpt.com "Rules | Cursor Docs"
[3]: https://github.com/macho715/mcp_obsidian/blob/main/AGENTS.md "mcp_obsidian/AGENTS.md at main · macho715/mcp_obsidian · GitHub"
[4]: https://github.com/macho715/mcp_obsidian/blob/main/SYSTEM_ARCHITECTURE.md "mcp_obsidian/SYSTEM_ARCHITECTURE.md at main · macho715/mcp_obsidian · GitHub"
