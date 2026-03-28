# Obsidian Output Contract

## Canonical storage layout (this repo MCP server)

Paths are relative to `VAULT_PATH` except the search index DB (`INDEX_DB_PATH`).

```text
<vault>/
├─ mcp_raw/
│  └─ <source>/
│     └─ <YYYY-MM-DD>/
│        └─ <mcp_id>.md
├─ 20_AI_Memory/
│  └─ <memory_type>/
│     └─ <YYYY>/
│        └─ <MM>/
│           └─ <MEM-...>.md
└─ 10_Daily/
   └─ <YYYY-MM-DD>.md
```

`MemoryStore` also ensures top-level folders `90_System` and `mcp_raw` exist alongside `10_Daily` and `20_AI_Memory`.

`<memory_type>` MUST be one of: `decision`, `project_fact`, `preference`, `person`, `todo`, `conversation_summary` (see `MemoryType` in `app/models.py`). `<MM>` is zero-padded month (`01`–`12`).

## Manual draft vs MCP-written files

- **Conversion skill / human drafts** often use `note_kind: raw|memory`, `id`, and `raw_ref` in YAML for readability.
- **Files written by this server** use `schema_type` (`raw_conversation` / `memory_item`), `mcp_id` for raw paths, and `memory_id` in memory frontmatter. When you prepare content intended for MCP tools, keep identifiers consistent so `raw_refs` resolve.

## Raw note rules

- One conversation → one raw note (draft) or one `mcp_raw/.../<mcp_id>.md` (server).
- Preserve the conversation faithfully.
- Path shape: `mcp_raw/<source>/<conversation_date ISO>/<mcp_id>.md`.

### Raw draft frontmatter (human / Obsidian-oriented)

```yaml
---
note_kind: raw
mcp_id: RAW-20260328-101200
source: cursor
created_at_utc: 2026-03-28T10:12:00Z
topics:
  - logistics
entities:
  - DSV
projects:
  - HVDC
tags:
  - mcp/raw
  - topic/logistics
---
```

Use the same `mcp_id` value as the filename stem when aligning with `RawArchiveStore`.

## Memory note rules

- One durable fragment → one memory note.
- Use arrays for all semantic facets.
- Path shape: `20_AI_Memory/<memory_type>/<YYYY>/<MM>/<MEMORY_ID>.md`.
- Memory id format: `MEM-YYYYMMDD-HHMMSS-XXXXXX` (six uppercase hex digits).

### Memory draft frontmatter

```yaml
---
note_kind: memory
id: MEM-20260328-102000-A1B2C3
source: cursor
created_at_utc: 2026-03-28T10:20:00Z
roles:
  - decision
topics:
  - shipment
entities:
  - DSV
projects:
  - HVDC
confidence: 0.92
status: active
raw_ref: RAW-20260328-101200
tags:
  - mcp/memory
  - role/decision
  - topic/shipment
---
```

## JSON payload mapping

For API payloads, preserve semantic arrays and map:

- `raw_ref` → `raw_refs: [raw_ref]`

## Retrieval considerations

Rank using a combination of:

- full-text
- roles
- topics
- entities
- projects
- recency

## Prohibitions

- No ad-hoc semantic folder trees outside the layout above.
- No singular `memory_type` as the primary classifier in prose when contradicting the path segment rules in this doc.
- No fabricated metadata.
- No one-conversation-equals-one-memory-note assumption.
