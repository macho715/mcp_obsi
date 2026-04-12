판정: **예. 아래는 바로 붙여 넣어 쓸 수 있는 MCP tool spec 초안입니다.**
근거: 현재 결정은 **UX 통합, 내부 계약 분리**이며, 이는 Guide의 `Prompt/Conversation/Response/Item` 분리, 승인형 툴 실행, 1도구=1행동 원칙과 정합적입니다. 
다음행동: 아래 스키마대로 `search_memory / fetch_memory / search_wiki / fetch_wiki / unified_search` 5개를 정의하고, UI는 `unified_search`만 직접 호출하게 두면 됩니다.

## Exec

* **채택안:** Option 3
* **원칙:** 사용자에게는 검색 1개, 내부는 `memory`와 `wiki`를 별도 corpus/tool로 유지
* **권장:** `unified_search`는 orchestration route, `fetch`는 corpus별 분기 유지

## EN Sources ≤3

1. PROJECT_UIUX_FULL_GUIDE_v2026.01 — 툴은 1도구=1행동, 승인형 실행, Items 기반 추적, UI는 Agentic UX 계약을 따라야 함. 
2. Vercel Agent Skills 운영 가이드 — 에이전트 스킬/가이드라인은 내부 규칙을 모듈화하고, UI/코드 리뷰/도구 사용을 분리된 surface로 다루는 구조가 안정적임. 

## MCP Tool Spec 초안

### 1) `search_memory`

기존 계약 유지용 canonical search입니다.

```json
{
  "$id": "tool.search_memory.v1",
  "title": "search_memory",
  "description": "Search canonical memory corpus only. Do not include wiki results.",
  "type": "object",
  "additionalProperties": false,
  "required": ["query"],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1,
      "description": "Natural language query for memory corpus."
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20,
      "default": 8
    },
    "project": {
      "type": ["string", "null"],
      "default": null,
      "description": "Optional project filter."
    },
    "types": {
      "type": "array",
      "description": "Optional memory type filter.",
      "items": {
        "type": "string",
        "enum": ["decision", "project_fact", "preference", "todo", "summary", "note"]
      },
      "default": []
    },
    "include_snippets": {
      "type": "boolean",
      "default": true
    }
  }
}
```

### 2) `fetch_memory`

기존 memory fetch 의미를 절대 바꾸지 않는 route입니다.

```json
{
  "$id": "tool.fetch_memory.v1",
  "title": "fetch_memory",
  "description": "Fetch full canonical memory note by memory id.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id"],
  "properties": {
    "id": {
      "type": "string",
      "minLength": 1,
      "description": "Canonical memory id, e.g. MEM-20260407-142504-3FB5C8"
    },
    "include_related": {
      "type": "boolean",
      "default": false,
      "description": "Whether to include related links or pointers."
    }
  }
}
```

### 3) `search_wiki`

`wiki/analyses` 포함 일반 wiki corpus 검색용입니다.

```json
{
  "$id": "tool.search_wiki.v1",
  "title": "search_wiki",
  "description": "Search wiki corpus only. Intended for compiled notes such as wiki/analyses.",
  "type": "object",
  "additionalProperties": false,
  "required": ["query"],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20,
      "default": 8
    },
    "path_prefix": {
      "type": "string",
      "default": "wiki/",
      "description": "Restrict wiki search to a path prefix."
    },
    "categories": {
      "type": "array",
      "description": "Optional wiki category filter.",
      "items": {
        "type": "string",
        "enum": ["analyses", "playbooks", "incidents", "ops", "reference", "drafts"]
      },
      "default": []
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "default": []
    },
    "include_snippets": {
      "type": "boolean",
      "default": true
    }
  }
}
```

### 4) `fetch_wiki`

pointer 없어도 직접 열 수 있어야 합니다.

```json
{
  "$id": "tool.fetch_wiki.v1",
  "title": "fetch_wiki",
  "description": "Fetch full wiki note by wiki id, slug, or path.",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id": {
      "type": ["string", "null"],
      "default": null,
      "description": "Internal wiki note id if available."
    },
    "slug": {
      "type": ["string", "null"],
      "default": null
    },
    "path": {
      "type": ["string", "null"],
      "default": null,
      "description": "Example: wiki/analyses/logistics_issue_shu_2025-11-26_3"
    },
    "include_frontmatter": {
      "type": "boolean",
      "default": true
    },
    "include_body": {
      "type": "boolean",
      "default": true
    }
  },
  "anyOf": [
    { "required": ["id"] },
    { "required": ["slug"] },
    { "required": ["path"] }
  ]
}
```

### 5) `unified_search`

UI가 직접 쓰는 통합 검색 route입니다. 내부에서는 memory와 wiki를 fan-out 호출합니다.

```json
{
  "$id": "tool.unified_search.v1",
  "title": "unified_search",
  "description": "Search across memory and wiki corpora, preserving source labels and fetch routes.",
  "type": "object",
  "additionalProperties": false,
  "required": ["query"],
  "properties": {
    "query": {
      "type": "string",
      "minLength": 1
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20,
      "default": 10
    },
    "sources": {
      "type": "array",
      "description": "Corpus selection. Default searches both.",
      "items": {
        "type": "string",
        "enum": ["memory", "wiki"]
      },
      "default": ["memory", "wiki"]
    },
    "wiki_path_prefix": {
      "type": "string",
      "default": "wiki/"
    },
    "project": {
      "type": ["string", "null"],
      "default": null
    },
    "memory_types": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["decision", "project_fact", "preference", "todo", "summary", "note"]
      },
      "default": []
    },
    "wiki_categories": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["analyses", "playbooks", "incidents", "ops", "reference", "drafts"]
      },
      "default": []
    },
    "dedupe_strategy": {
      "type": "string",
      "enum": ["none", "title_similarity", "pointer_linked"],
      "default": "pointer_linked"
    },
    "prefer_canonical_memory": {
      "type": "boolean",
      "default": true
    },
    "include_snippets": {
      "type": "boolean",
      "default": true
    }
  }
}
```

## Response Schema 초안

### A) `search_memory` / `search_wiki` 공통 hit 형식

```json
{
  "$id": "schema.search_hit.v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "source",
    "id",
    "title",
    "score",
    "fetch_route"
  ],
  "properties": {
    "source": {
      "type": "string",
      "enum": ["memory", "wiki"]
    },
    "id": {
      "type": "string"
    },
    "title": {
      "type": "string"
    },
    "slug": {
      "type": ["string", "null"]
    },
    "path": {
      "type": ["string", "null"]
    },
    "category": {
      "type": ["string", "null"]
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "snippet": {
      "type": ["string", "null"]
    },
    "score": {
      "type": "number",
      "minimum": 0
    },
    "fetch_route": {
      "type": "string",
      "enum": ["fetch_memory", "fetch_wiki"]
    },
    "related_memory_id": {
      "type": ["string", "null"]
    },
    "related_wiki_path": {
      "type": ["string", "null"]
    },
    "created_at": {
      "type": ["string", "null"],
      "description": "ISO 8601"
    },
    "updated_at": {
      "type": ["string", "null"],
      "description": "ISO 8601"
    }
  }
}
```

### B) `unified_search` 응답 형식

```json
{
  "$id": "schema.unified_search_response.v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["query", "results", "meta"],
  "properties": {
    "query": {
      "type": "string"
    },
    "results": {
      "type": "array",
      "items": { "$ref": "schema.search_hit.v1" }
    },
    "meta": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "sources_searched",
        "memory_result_count",
        "wiki_result_count",
        "merge_strategy"
      ],
      "properties": {
        "sources_searched": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["memory", "wiki"]
          }
        },
        "memory_result_count": {
          "type": "integer",
          "minimum": 0
        },
        "wiki_result_count": {
          "type": "integer",
          "minimum": 0
        },
        "merge_strategy": {
          "type": "string",
          "enum": ["score_merge", "memory_priority", "source_grouped"]
        },
        "warnings": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    }
  }
}
```

## Fetch Response Schema 초안

### `fetch_memory` 응답

```json
{
  "$id": "schema.fetch_memory_response.v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["source", "id", "title", "body"],
  "properties": {
    "source": {
      "type": "string",
      "enum": ["memory"]
    },
    "id": {
      "type": "string"
    },
    "title": {
      "type": "string"
    },
    "type": {
      "type": ["string", "null"]
    },
    "project": {
      "type": ["string", "null"]
    },
    "body": {
      "type": "string"
    },
    "related_wiki_paths": {
      "type": "array",
      "items": { "type": "string" }
    },
    "created_at": {
      "type": ["string", "null"]
    },
    "updated_at": {
      "type": ["string", "null"]
    }
  }
}
```

### `fetch_wiki` 응답

```json
{
  "$id": "schema.fetch_wiki_response.v1",
  "type": "object",
  "additionalProperties": false,
  "required": ["source", "title", "path", "body"],
  "properties": {
    "source": {
      "type": "string",
      "enum": ["wiki"]
    },
    "id": {
      "type": ["string", "null"]
    },
    "title": {
      "type": "string"
    },
    "slug": {
      "type": ["string", "null"]
    },
    "path": {
      "type": "string"
    },
    "category": {
      "type": ["string", "null"]
    },
    "frontmatter": {
      "type": ["object", "null"]
    },
    "body": {
      "type": "string"
    },
    "related_memory_id": {
      "type": ["string", "null"]
    },
    "created_at": {
      "type": ["string", "null"]
    },
    "updated_at": {
      "type": ["string", "null"]
    }
  }
}
```

## 권장 동작 규칙

| No | Item             | Value            | Risk | Evidence              |
| -- | ---------------- | ---------------- | ---- | --------------------- |
| 1  | SSOT             | memory           | 낮음   | Guide의 분리/추적 원칙과 부합   |
| 2  | Overlay          | wiki             | 낮음   | compiled/분석 문서 용도와 부합 |
| 3  | Search UX        | 통합 가능            | 낮음   | UI 레이어 fan-out        |
| 4  | Fetch semantics  | source별 분기 유지    | 낮음   | 계약 안정성 확보             |
| 5  | Approval/logging | write 계열만 승인형 필수 | 낮음   | Agentic UX 원칙         |

## Orchestration 규칙

`unified_search` 내부 로직은 아래처럼 두면 됩니다.

```json
{
  "algorithm": [
    "fan_out_to_search_memory",
    "fan_out_to_search_wiki",
    "normalize_scores_per_source",
    "dedupe_by_pointer_or_title_similarity",
    "prefer_memory_if_canonical_duplicate_exists",
    "return_source_labeled_results"
  ]
}
```

## Options A/B/C

| Option | Value                                                | Risk |  Time |
| ------ | ---------------------------------------------------- | ---: | ----: |
| A      | `search_wiki/fetch_wiki`만 추가, UI는 분리 유지              |   낮음 | 0.50d |
| B      | A + `unified_search` 추가                              |   중간 | 1.00d |
| C      | B + pointer backfill + dedupe tuning + related links |   중간 | 2.00d |

**권장:** B 시작, 이후 C

## Steps

1. `search_memory/fetch_memory` 스키마 freeze
2. `search_wiki/fetch_wiki` 구현
3. `wiki/analyses`만 우선 인덱싱
4. `unified_search` fan-out + merge 추가
5. UI에서 source badge와 fetch route 분기 노출
6. pointer backfill은 2차 작업으로 분리

## cmd3

```text
1) Freeze existing memory contract
2) Add wiki-specific read surface
3) Merge only at orchestration/UI layer
```

## ZERO log

* ZERO 아님
* 사유: 현재 요청은 설계/스키마 초안이며 P2/통관/규정 리스크 없음
* 가정: wiki corpus에 최소 `path/title/body/category/tags` 메타를 제공할 수 있음

원하시면 다음 단계로 **TypeScript 타입 + MCP server handler pseudo-code**까지 이어서 정리하겠습니다.
