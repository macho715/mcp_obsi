---
name: paste-conversation-to-obsidian
description: >-
  One-shot pipeline: user pastes a chat or transcript → delegate to metadata scout
  and memory splitter when needed → convert with obsidian-conversation-to-memory
  rules → verify → persist memories via MCP save_memory and optional raw markdown
  under the vault. Use when the user wants dialogue stored into the Obsidian-backed
  vault with minimal manual steps (paste and go).
compatibility:
  - cursor-editor
metadata:
  depends_on_subagents:
    - obsidian-metadata-scout
    - obsidian-memory-splitter
    - obsidian-memory-verifier
  depends_on_skills:
    - obsidian-conversation-to-memory
    - obsidian-memory-workflow
---

# Paste conversation → Obsidian (agent pipeline)

Orchestrate subagents and MCP writes so a **pasted conversation** becomes **raw archive + durable memory notes** on disk, aligned with this repo’s layout (see [`AGENTS.md`](../../../AGENTS.md), [`obsidian-output-contract.md`](../obsidian-conversation-to-memory/references/obsidian-output-contract.md)).

## When to use

- User pastes chat / transcript / meeting log and asks to **save to Obsidian**, **vault**, **memory**, or **MCP**.
- User wants **scout + split + verify + save** in one flow without naming each step.

Do **not** use for: auth/MCP contract changes, bulk migration, or storing content the user marked as secret/sensitive without redaction.

## Prerequisites

- **Obsidian memory MCP** is available in Cursor (e.g. `obsidian-memory-local` or production profile) with write tools enabled.
- You know or can ask for: `source` label (e.g. `cursor`, `chatgpt`, `manual`), optional `project`, and whether **daily note append** is desired (`append_daily` on `save_memory`; default server behavior is `True`).
- For **raw file** creation: resolve vault root from environment / user (`VAULT_PATH` or equivalent). Do not hard-code paths.

## Pipeline (execute in order)

### 1) Ingest

- Accept the pasted text as the single conversation source.
- If the message is **short and single-topic** (rough guide: under ~2k characters, one obvious thread), you may **skip** parallel scout/splitter and go to step 3.
- If **long, noisy, or multi-topic**, continue to step 2.

### 2) Parallel specialists (Task subagents)

- Launch **`obsidian-metadata-scout`** and **`obsidian-memory-splitter`** in **parallel** with the full pasted conversation (parent context: goal + any user hints for source/project/language).
- Merge their outputs: use splitter drafts as primary structure; use scout for tags/topics/entities/projects refinements.

### 3) Convert (follow conversion skill)

- Apply rules from **`obsidian-conversation-to-memory`** (read that skill if needed): one **raw** artifact, zero-to-many **atomic memory** drafts, array metadata, `mcp_id` + `MEM-…` ids, `raw_ref` / `raw_refs` linkage, no ad-hoc semantic folders.
- Produce final markdown drafts **before** persistence.

### 4) Verify

- Run **`obsidian-memory-verifier`** on the drafts (or self-check using its checklist if subagent unavailable).
- If **FAIL**, fix drafts minimally, then re-verify.

### 5) Persist (deliberate writes)

**A) Memory notes — MCP `save_memory` (one call per atomic memory)**

Map each memory draft to tool arguments (names must match the server tool schema):

| Draft field | `save_memory` argument |
|-------------|-------------------------|
| Title / heading | `title` |
| Body (Summary + Evidence + Notes) | `content` |
| `source` | `source` |
| Primary shape from `roles` | `memory_type` (see mapping below) |
| `roles` | `roles` (string list; omit or pass as server accepts) |
| `topics`, `entities`, `projects`, `tags` | same-name args |
| `raw_ref` | `raw_refs: [raw_ref]` (always a list) |
| `confidence`, `status`, `language`, `notes` | pass through when present |

**`memory_type` from first/l primary role** (align with [`MemoryStore.ROLE_TO_MEMORY_TYPE`](../../../app/services/memory_store.py)):

| Role (draft) | `memory_type` |
|--------------|-----------------|
| `decision` | `decision` |
| `fact` | `project_fact` |
| `preference` | `preference` |
| `todo` | `todo` |
| `summary` | `conversation_summary` |
| `person` / unclear | omit or set after user confirmation; server may infer from `roles` |

After each call, record returned **`id`** and **`path`** for the user summary.

**B) Raw conversation — MCP `archive_raw`**

After drafts are verified, call **`archive_raw`** once with:

| Field | Value |
|-------|--------|
| `mcp_id` | Same stable id used in memory `raw_refs` (safe filename stem) |
| `source` | e.g. `cursor`, `chatgpt`, `manual` |
| `body_markdown` | Full transcript or normalized conversation (markdown) |
| `created_at_utc` | ISO-8601 string if known, else omit for server default |
| `conversation_date` | `YYYY-MM-DD` if distinct from created time, else omit |
| `project`, `tags` | Optional |

Returns `status`, `path` (under `mcp_raw/...`). If MCP is unavailable, fall back to **Write** into the vault at that path or hand the user the markdown.

Use the **same** `mcp_id` everywhere so `raw_refs` in `save_memory` line up with the archived raw file.

### 6) Close the loop

Reply with:

- Count of `save_memory` calls and each returned **`path`** / `id`.
- Raw file path (or explicit manual-save instructions).
- Link pattern the server uses for Obsidian: `obsidian://open?vault=…&file=…` when settings are known.
- Any verifier **PASS WITH AMBIGUITIES** items.

## Safety

- **Read-first:** if unsure whether the user wanted a durable write, confirm once before calling `save_memory` or `archive_raw`.
- Do not persist **credentials, tokens, or unredacted PII**; mask or refuse per project privacy rules.
- Respect [`obsidian-memory-workflow`](../obsidian-memory-workflow/SKILL.md): markdown on disk is SSOT; SQLite is derived.

## References

- [`obsidian-conversation-to-memory`](../obsidian-conversation-to-memory/SKILL.md)
- [`../obsidian-conversation-to-memory/references/obsidian-output-contract.md`](../obsidian-conversation-to-memory/references/obsidian-output-contract.md)
