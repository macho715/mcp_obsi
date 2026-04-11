판정: **조건부 예 — `mcp_obsidian`는 이미 Prototype이 아니라 `Pre-Prod`에 가깝습니다. 다만 2025-11 MCP 최신 기준으로는 `tools 중심 memory server` 성격이 강하므로, `resources + prompts + batch tasks/progress + wiki-native audit layer`를 붙여야 “실제 운영형 LLM Wiki MCP”가 됩니다.** ([GitHub][1])
근거: 레포는 이미 Markdown SSOT, SQLite FTS5 derived index, 8개 MCP tools, read-only / authenticated write sibling route, schema validation, mask/reject 정책, HMAC phase-2, Railway production 재검증까지 문서화했습니다. MCP 최신 규격은 server surface를 `tools`만이 아니라 `resources`와 `prompts`까지 포함하는 구조로 정의하고, 장기 작업에는 `tasks`와 `progress`를 둘 수 있게 확장했습니다. ([GitHub][1])
다음행동: **기존 core는 유지**하고, 아래 4개만 추가하십시오 — `wiki overlay`, `resources`, `prompts`, `batch lint/reindex tasks`. 이 조합이 2026 운영선입니다. ([GitHub][1])

## 정정

이전의 “read-only 위주” 평가는 **과소평가**였습니다. 레포 실확인 결과 현재 서버는 `search_memory`, `save_memory`, `get_memory`, `list_recent_memories`, `update_memory`, `archive_raw`, `search`, `fetch`의 8개 tool과 read-only / write-capable specialist route를 이미 갖고 있습니다. 즉 **검색 MCP**가 아니라 **memory CRUD + search 서버**입니다. ([GitHub][2])

## Exec

핵심 판단은 단순합니다.

* **유지해야 할 것**: `Markdown first + SQLite derived index + read/write 분리 + HMAC + schema validation`
* **추가해야 할 것**: `wiki compiled layer + resources + prompts + batch tasks/progress`
* **삭제하지 말 것**: 기존 `memory/YYYY/MM` 계약, wrapper compatibility, hosted specialist route

이유는 MCP 2025-11이 server control plane을 `Prompts(사용자 제어) / Resources(앱 제어) / Tools(모델 제어)`로 분리하기 때문입니다. 현재 레포는 tools plane은 강하지만 resources/prompts plane이 문서상 드러나지 않아, “발견·탐색·운영 룰”이 전부 tool 호출에 쏠릴 위험이 있습니다. ([modelcontextprotocol.io][3])

## EN Sources ≤3

1. `macho715/mcp_obsidian` 레포 README + SYSTEM_ARCHITECTURE ([GitHub][1])
2. MCP Specification 2025-11-25 (`overview / tools / resources / prompts / tasks / progress`) ([modelcontextprotocol.io][3])
3. `cyanheads/obsidian-mcp-server` 벤치마크 레포 ([GitHub][4])

## 벤치마크

| No | Item                       | Value       | Risk | Evidence                                                                                                      |
| -- | -------------------------- | ----------- | ---- | ------------------------------------------------------------------------------------------------------------- |
| 1  | Runtime core               | **PASS**    | 낮음   | FastAPI/FastMCP, Markdown SSOT, SQLite FTS5, Railway 운영 문서화 ([GitHub][1])                                     |
| 2  | Read/Write 분리              | **PASS**    | 낮음   | `/chatgpt-mcp`, `/chatgpt-mcp-write`, `/claude-mcp`, `/claude-mcp-write` 구조와 bearer/HMAC 검증 문서화 ([GitHub][1]) |
| 3  | Tool surface               | **GOOD**    | 중간   | 8개 tool 노출, wrapper compatibility 유지 ([GitHub][2])                                                            |
| 4  | Search plane               | **GOOD**    | 낮음   | SearchPlan DSL, JSON1 + FTS5, path migration/backfill 존재 ([GitHub][2])                                        |
| 5  | Schema/Safety              | **GOOD**    | 중간   | schema validation, mask/reject, signed write, auth gate 존재 ([GitHub][1])                                      |
| 6  | Resources capability       | **AMBER**   | 중간   | 최신 MCP는 resources를 앱 제어 primitive로 정의하나, 현재 문서상 tools 위주 surface만 명시 ([modelcontextprotocol.io][3])           |
| 7  | Prompts capability         | **AMBER**   | 중간   | 최신 MCP는 prompts를 사용자 제어 primitive로 정의하나, 현재 문서상 prompt surface 미노출 ([modelcontextprotocol.io][3])             |
| 8  | Batch ops                  | **GAP**     | 중간   | backfill/reindex/lint 계열은 tasks/progress가 더 적합하나 현재 문서상 task surface 미노출 ([modelcontextprotocol.io][5])       |
| 9  | Wiki-native compiled layer | **GAP**     | 높음   | 현재는 memory server가 강하고, `index/log/conflict/lint` 중심의 wiki overlay는 별도 운영 계층으로 분리되지 않음 ([GitHub][1])          |
| 10 | Obsidian full-KM parity    | **PARTIAL** | 중간   | 벤치마크 레포는 read/write/search/list/frontmatter/tags/delete까지 제공. 현재 레포는 memory-centric CRUD가 강점 ([GitHub][4])    |

## 실제 운영형 설계

### 1) 저장 계층은 교체하지 말고 “overlay”를 얹으십시오

현재 구조의 강점은 이미 확보됐습니다.

```text
mcp_raw/           # raw archive
memory/YYYY/MM/    # normalized memory SSOT
SQLite index       # derived accelerator
```

여기에 아래만 추가하면 됩니다.

```text
wiki/
  index.md
  log.md
  topics/
  entities/
  conflicts/
  reports/
```

즉:

* `memory/` = **event store**
* `wiki/` = **compiled knowledge layer**

이렇게 나눠야 현재 계약을 깨지 않고, LLM Wiki 패턴을 실제 운영에 붙일 수 있습니다. ([GitHub][1])

### 2) `resources`를 먼저 추가하십시오

MCP 최신 구조에서 resources는 **앱 제어 컨텍스트**입니다. 따라서 모델이 매번 tool로 index를 뒤지는 대신, 아래 항목을 resources로 고정하면 운영 품질이 올라갑니다. ([modelcontextprotocol.io][6])

권장 resource surface:

```text
resource://wiki/index
resource://wiki/log/recent
resource://wiki/topic/{slug}
resource://schema/memory
resource://ops/verification/latest
resource://ops/routes/profile-matrix
```

효과:

* index/log를 안정적으로 주입
* schema와 운영 상태를 표준 URI로 노출
* read-only client에서 discoverability 향상

### 3) `prompts`를 추가하십시오

prompts는 **사용자 제어 워크플로**입니다. 현재처럼 모든 행동을 tool 자동호출로 몰아넣지 말고, 반복 운영은 prompt template로 승격해야 합니다. MCP는 `prompts/list`, `prompts/get`을 표준화하고 있습니다. ([modelcontextprotocol.io][7])

권장 prompt 4개:

* `ingest_memory_to_wiki`
* `reconcile_conflict`
* `weekly_lint_report`
* `summarize_recent_project_state`

이유:

* 운영자 승인형 흐름에 적합
* ChatGPT/Claude UI에서 slash-like workflow로 쓰기 쉬움
* human-in-the-loop를 유지하면서 표준화 가능

### 4) wiki-native tool을 5개만 추가하십시오

현재 CRUD는 memory 기준입니다. LLM Wiki 운영에는 **compiled artifact 전용 tool**이 더 필요합니다. tools는 모델 제어이므로, write route에만 두는 것이 맞습니다. MCP tools 문서도 human denial UI를 권장합니다. ([modelcontextprotocol.io][8])

권장 tool:

```text
sync_wiki_index
append_wiki_log
write_wiki_page
lint_wiki
reconcile_conflict
```

역할:

* `sync_wiki_index`: `wiki/index.md` materialize
* `append_wiki_log`: append-only 감사 로그
* `write_wiki_page`: topic/entity/conflict page patch
* `lint_wiki`: orphan/stale/missing-link/source-gap 탐지
* `reconcile_conflict`: 상충 claim 병기

### 5) batch 작업은 `tasks + progress`로 분리하십시오

`backfill`, `reindex`, `full lint`, `rebuild wiki`는 길어질 수 있습니다. MCP 2025-11은 장기 작업용 `tasks`와 진행 알림용 `progress`를 제공합니다. 이 부분은 현재 레포에 가장 값비싼 보강입니다. ([modelcontextprotocol.io][5])

권장 task:

* `task_reindex_memory`
* `task_build_wiki_overlay`
* `task_lint_full_vault`
* `task_backfill_paths`

효과:

* timeout 감소
* 장기 작업 재개 가능성 확보
* UI 진행률 노출 가능

## 권장 라우트 계약

현재 specialist route는 유지하고 capability만 확장하십시오. ([GitHub][2])

```text
/chatgpt-mcp
  - tools: search, fetch
  - resources: wiki/index, recent log, schema
  - prompts: summarize_recent_project_state, weekly_lint_report

/chatgpt-mcp-write
  - above +
  - save_memory, update_memory, get_memory
  - write_wiki_page, sync_wiki_index, append_wiki_log, reconcile_conflict, lint_wiki

/claude-mcp
  - same read profile

/claude-mcp-write
  - same write profile
```

핵심:

* read profile은 **discoverability 강화**
* write profile은 **mutation 최소화 + 승인형**
* 기존 bearer/HMAC를 그대로 재사용

## 파일/모듈 설계

```text
app/
  resources_server.py
  prompts_server.py
  wiki_tools.py
  task_server.py

app/services/
  wiki_store.py
  wiki_index_service.py
  wiki_log_service.py
  conflict_service.py
  lint_service.py
```

역할 분리:

* `wiki_store.py`: `wiki/` 디렉터리 생성/patch
* `wiki_index_service.py`: `index.md` materialization
* `wiki_log_service.py`: append-only log
* `conflict_service.py`: source 충돌 병기
* `lint_service.py`: stale/orphan/source-gap 검사

## 옵션

가정: **1인 Python/FastAPI 운영 기준**입니다. 시간은 구현+smoke 기준 추정이므로 **AMBER**입니다.

| Option                                                       |    $ | Risk                                       |        Time |
| ------------------------------------------------------------ | ---: | ------------------------------------------ | ----------: |
| A. 현행 유지                                                     | 0.00 | 중간 — memory server로는 충분하나 wiki 운영은 누적되지 않음 |  0.50~1.00일 |
| B. **권장** `resources + prompts + wiki 5 tools` 추가            |   중간 | 낮음 — 현재 구조 보존, 운영성 급상승                     |  4.00~7.00일 |
| C. B + `tasks/progress + full lint + frontmatter atomic ops` |   중상 | 매우 낮음 — 장기 운영/팀 운영 적합                      | 8.00~12.00일 |

제 판정은 **B 즉시, C는 2차**입니다.

## 단계별 실행

### Step 1

`wiki/` overlay 디렉터리 추가
`index.md`, `log.md`, `topics/`, `entities/`, `conflicts/`, `reports/`

### Step 2

`resources/list`, `resources/read` capability 추가
최소 5개 resource URI 노출

### Step 3

`prompts/list`, `prompts/get` capability 추가
운영 prompt 4개 고정

### Step 4

write route 전용 `wiki-native tools` 5개 추가
기존 `save_memory/update_memory`는 유지

### Step 5

`lint_wiki` 결과를 `wiki/reports/`에 저장
append-only audit 유지

### Step 6

`tasks/progress`는 batch job에만 적용
`reindex`, `build overlay`, `full lint`부터 시작

## cmd3

```bash
mkdir -p vault/wiki/{topics,entities,conflicts,reports}
touch vault/wiki/{index.md,log.md}
touch app/{resources_server.py,prompts_server.py,wiki_tools.py,task_server.py}
touch app/services/{wiki_store.py,wiki_index_service.py,wiki_log_service.py,conflict_service.py,lint_service.py}
```

## ZERO log

* **정정 완료**: 이 레포는 read-only가 아니라 write-capable sibling route까지 포함한 `Pre-Prod memory MCP`입니다. ([GitHub][2])
* `resources/prompts/tasks` 부재는 **문서/노출 surface 기준** 판정입니다. 코드 전체 AST 탐색은 하지 않았으므로 이 항목은 **AMBER**입니다. ([GitHub][2])
* 일정/공수는 **가정**입니다. 실제 값은 테스트 범위와 CI 포함 여부에 따라 달라집니다.
* 외부 기준은 2025-11 MCP 최신 spec과 2026 시점의 성숙한 Obsidian MCP 구현을 사용했습니다. ([modelcontextprotocol.io][3])

다음 턴에서는 이 기준으로 바로 쓸 수 있는 **`AGENTS.md delta` + `resources/prompts/tool schema` + `wiki overlay 템플릿`**까지 내려가겠습니다.

[1]: https://github.com/macho715/mcp_obsidian/blob/main/README.md "mcp_obsidian/README.md at main · macho715/mcp_obsidian · GitHub"
[2]: https://github.com/macho715/mcp_obsidian/blob/main/SYSTEM_ARCHITECTURE.md "mcp_obsidian/SYSTEM_ARCHITECTURE.md at main · macho715/mcp_obsidian · GitHub"
[3]: https://modelcontextprotocol.io/specification/2025-11-25/server/index?utm_source=chatgpt.com "Overview - Model Context Protocol"
[4]: https://github.com/cyanheads/obsidian-mcp-server?utm_source=chatgpt.com "GitHub - cyanheads/obsidian-mcp-server: Obsidian Knowledge-Management MCP (Model Context Protocol) server that enables AI agents and development tools to interact with an Obsidian vault. It provides a comprehensive suite of tools for reading, writing, searching, and managing notes, tags, and frontmatter, acting as a bridge to the Obsidian Local REST API plugin."
[5]: https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks?utm_source=chatgpt.com "Tasks - Model Context Protocol"
[6]: https://modelcontextprotocol.io/specification/2025-11-25/server/resources?utm_source=chatgpt.com "Resources - Model Context Protocol"
[7]: https://modelcontextprotocol.io/specification/2025-11-25/server/prompts?utm_source=chatgpt.com "Prompts - Model Context Protocol"
[8]: https://modelcontextprotocol.io/specification/2025-11-25/server/tools?utm_source=chatgpt.com "Tools - Model Context Protocol"
