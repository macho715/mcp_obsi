---
name: obsidian-conversation-to-memory
description: Convert free-form conversation, transcript, chat log, meeting notes, or pasted dialogue into Obsidian-compatible raw notes and atomic memory notes with YAML frontmatter. Use when the user asks to transform general conversation into Obsidian format, memory vault notes, save_memory v2 payloads, or searchable notes with roles, topics, entities, and projects.
compatibility:
  - cursor-editor
  - cursor-cli
metadata:
  output_types:
    - raw-note
    - memory-note
    - save-memory-v2-json
    - search-dsl-ready-metadata
  primary_source: conversation
---

> ⚠️ **CRITICAL WARNING / 중요 경고** ⚠️
> **모든 작업 및 데이터는 반드시 아래 Vault 경로를 사용해야 합니다:**
> C:\Users\jichu\Downloads\valut


# Obsidian Conversation to Memory

Use this skill to turn general conversation into Obsidian-friendly Markdown artifacts without relying on semantic folders.

## When to Use

Use this skill when the input is any of the following:
- pasted conversation
- meeting transcript
- free-form chat log
- AI conversation the user wants stored in Obsidian
- notes that must be converted into `raw` and `memory` records
- requests mentioning frontmatter, YAML, `roles`, `topics`, `entities`, `projects`, or `save_memory`

Do **not** use this skill for:
- direct database migration
- auth or deployment changes
- storage schema changes outside the note output contract
- destructive file operations without explicit approval
- **one-shot paste-and-persist flows** (use `paste-conversation-to-obsidian` which
  orchestrates this skill internally along with scout/split/verify/MCP persistence)

## Inputs

Expected input can be plain text or Markdown and should ideally include:
- conversation body
- optional source label (`cursor`, `chatgpt`, `claude`, `manual`)
- optional timestamp
- optional project name
- optional language preference

If inputs are incomplete:
- keep unknown metadata empty rather than inventing values
- use `[ASSUMPTION]` only in the prose summary, not as fake metadata
- preserve ambiguity through lower confidence instead of fabricated certainty

## Output Contract

Always produce, in this order:
1. **Conversion summary**
   - topic count
   - memory note count
   - assumptions
   - unresolved ambiguities
2. **One raw note**
   - on-disk layout for this repo’s MCP server: `mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md` (under `VAULT_PATH`)
3. **Zero to many memory notes**
   - on-disk layout for **MCP writes:** `memory/<YYYY>/<MM>/<MEMORY_ID>.md` (`<MM>` zero-padded). `MemoryType` / `roles` are metadata, not path segments. Legacy vault may still have `20_AI_Memory/<memory_type>/<YYYY>/<MM>/…` for older files.
4. **Optional `save_memory` v2 JSON payloads**
   - only when requested or when the user mentions MCP / API / payload / schema

## Core Rules

### 1) Folder policy
- Do not invent ad-hoc semantic trees (e.g. `topic/foo/`, `project/bar/decisions/`). Use only the server layout below.
- **Raw archive:** `mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md` (see [`RawArchiveStore`](../../../app/services/raw_archive_store.py)).
- **Memory notes:** `memory/<YYYY>/<MM>/<MEMORY_ID>.md` for current server writes (see [`MemoryStore._memory_rel_path`](../../../app/services/memory_store.py)). `20_AI_Memory/…` is legacy/read-compat only unless migrating.
- **Daily append (optional):** `10_Daily/<YYYY-MM-DD>.md`.
- **Search index:** SQLite lives at `INDEX_DB_PATH`, not under a `vault/system/` path for this server. The vault may include `90_System/` for other artifacts; do not confuse it with the DB file.

### 2) Storage unit policy
- One conversation becomes **one raw note**.
- One conversation may yield **zero to many memory notes**.
- Prefer **one durable memory fragment per memory note**.
- Split decisions, facts, preferences, todos, and summaries when doing so improves retrieval quality.

### 3) Metadata policy
For **memory notes**, keep these as arrays even when they contain one item:
- `roles`
- `topics`
- `entities`
- `projects`
- `tags`

For **raw notes**, keep these as arrays when present:
- `topics`
- `entities`
- `projects`
- `tags`

Use `raw_ref` in Markdown frontmatter for note-to-note linking.
If JSON payloads are requested, use `raw_refs` as an array to match the `save_memory` v2 payload contract.

### 4) Confidence policy
- High confidence: explicit user statements, explicit decisions, directly stated facts
- Medium confidence: strong implication with clear local context
- Low confidence: inferred topic/entity mapping without explicit wording
- Never invent dates, project names, entities, or owners

### 5) Tags policy
Prefer nested tag patterns like:
- `mcp/raw`
- `mcp/memory`
- `role/decision`
- `topic/logistics`
- `entity/DSV`
- `project/HVDC`

## Decision Tree

### Short single-topic conversation
If the conversation is short and clearly about one topic:
- do the conversion in one pass
- generate one raw note
- generate only the minimum necessary memory notes
- skip subagents unless validation is requested

### Long or mixed-topic conversation
If the conversation is long, noisy, or multi-topic:
- launch `obsidian-metadata-scout` and `obsidian-memory-splitter` in parallel
- merge the two outputs in the parent agent
- run `obsidian-memory-verifier` before finalizing

### Verification-critical requests
If the user asks for strict validation, schema compliance, or repo-ready output:
- always run `obsidian-memory-verifier`
- include a pass/fail checklist in the final answer

## Procedure

### Step 1 — Preflight
- Identify source type: transcript, chat, meeting, dialogue, or mixed notes.
- Determine language.
- Extract any explicit project, entities, dates, and action items.
- Decide whether the task is single-pass or parallel.

### Step 2 — Build the raw note
Create exactly one raw note.

Required frontmatter fields for raw notes:
- `note_kind: raw`
- `mcp_id` (stable key; matches server raw filename stem and links from memory notes)
- `source`
- `created_at_utc`

Recommended arrays when evidence exists:
- `topics`
- `entities`
- `projects`
- `tags`

The raw note body should preserve the conversation faithfully, with only minimal cleanup for readability.

### Step 3 — Split durable memory notes
Create memory notes only for durable, retrieval-worthy items such as:
- decisions
- facts
- preferences
- todos
- summaries

A memory note should capture one retrievable claim or action unit.
Avoid stuffing unrelated topics into one memory note.

Required frontmatter fields for memory notes:
- `note_kind: memory`
- `id`
- `source`
- `created_at_utc`
- `roles`
- `status`
- `raw_ref`

Recommended fields when supported by evidence:
- `topics`
- `entities`
- `projects`
- `tags`
- `confidence`
- `occurred_at`
- `due_at`

### Step 4 — Normalize titles and IDs
Use stable, human-readable titles.

ID patterns aligned with this repo’s MCP server:
- **Memory note ids:** `MEM-YYYYMMDD-HHMMSS-XXXXXX` (six uppercase hex chars), as produced by [`make_memory_id`](../../../app/utils/ids.py).
- **Raw archive filename key:** `mcp_id` in the payload saved by the server (string; must be safe as a filename). For manual drafts before MCP ingest, you may use a placeholder `mcp_id` or a human `id`; when targeting `archive_raw` / on-disk layout, prefer a single stable `mcp_id` per raw note. Link memory `raw_ref` / `raw_refs` to that same identifier.

If exact timestamps are missing:
- use the best available date context
- mark the ambiguity in the summary
- do not fabricate precision

### Step 5 — Optional JSON payloads
If the user asks for API-ready output, generate `save_memory` v2 JSON objects.
Map fields as follows:
- frontmatter `raw_ref` -> JSON `raw_refs: [raw_ref]`
- frontmatter arrays remain arrays
- `status` defaults to `active`
- `language` defaults to the dominant input language

### Step 6 — Validate before returning
Check all of the following:
- exactly one raw note exists
- memory note count matches extracted durable fragments
- no semantic folder names are introduced
- arrays are used for multi-facet metadata
- `raw_ref` links every memory note to the raw note
- titles are distinct and retrieval-friendly
- confidence values are between `0` and `1`
- empty arrays are acceptable; fabricated values are not

## Subagent Integration

### `obsidian-metadata-scout`
Use proactively for long or multi-topic conversation.
Goal:
- extract `roles`, `topics`, `entities`, `projects`, `tags`, and confidence hints

### `obsidian-memory-splitter`
Use proactively for long or mixed conversation.
Goal:
- split conversation into atomic memory notes and propose titles, IDs, and note boundaries

### `obsidian-memory-verifier`
Use after draft generation or when the user requests high confidence.
Goal:
- independently verify schema, folder policy, output completeness, and note atomicity

## Output Format Example

Return the final output in this shape:

- `## Conversion Summary`
  - raw notes: 1
  - memory notes: N
  - assumptions: ...
  - unresolved: ...
- `## Raw Note`
  - YAML frontmatter block
  - raw body block
- `## Memory Note 1`
  - YAML frontmatter block
  - memory body block

## Safety
- Never delete or overwrite existing vault content unless the user explicitly asks.
- Do not claim a note belongs in a semantic folder.
- Do not change repo-wide schema or MCP tool contracts from inside this skill.
- If a write path is requested, prefer preview output first, then explicit approval, then write.

## References
- `references/obsidian-output-contract.md`
- `assets/raw-note-template.md`
- `assets/memory-note-template.md`
- `assets/save-memory-v2.schema.json`
