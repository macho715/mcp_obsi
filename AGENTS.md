# AGENTS.md

# This file is based on the supplied architecture and patch notes, then aligned (storage layout) with `app/services/memory_store.py`, `raw_archive_store.py`, and `app/utils/ids.py` on the filesystem.

# Verify with: the real filesystem, README, pyproject.toml, lockfiles, CI workflows, scripts, and implemented schemas.

## Scope

- This repository implements a hybrid memory system for coding agents.
- Local layer: an Obsidian plugin curates raw conversations, normalized memory notes, frontmatter, and index rebuilds.
- Remote layer: a FastAPI + FastMCP server exposes shared memory tools over a public HTTPS MCP endpoint.
- Durable storage is human-readable Markdown in the Obsidian vault. SQLite and JSON indexes are rebuildable helpers.

## Confirmed Components From the Design Draft

- Obsidian plugin:
  - `obsidian-memory-plugin/`
  - `src/main.ts`, `src/types.ts`, `src/settings.ts`, `src/services/vault-store.ts`
- MCP server:
  - `obsidian-mcp-server/`
  - `app/main.py`, `app/config.py`, `app/models.py`, `app/mcp_server.py`
  - `app/services/index_store.py`, `app/services/markdown_store.py`, `app/services/memory_store.py`
- Vault layout under `VAULT_PATH` (see `MemoryStore._ensure_structure`):
  - `mcp_raw/` — raw conversation markdown: `mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md`
  - `memory/` — current memory markdown write target: `memory/<YYYY>/<MM>/<MEMORY_ID>.md`
  - `20_AI_Memory/` — legacy memory markdown read/update compatibility path
  - `10_Daily/` — daily note append targets
  - `90_System/` — reserved for vault-local system artifacts (not the SQLite index file path)
- Search index: SQLite at `INDEX_DB_PATH` (see `IndexStore`), not a fixed `vault/system/` file path in code.

## Source of Truth

- Markdown notes in the vault are the source of truth.
- SQLite at `INDEX_DB_PATH` is a rebuildable index derived from markdown, not primary storage.
- MCP tool contracts are defined by the server implementation, not by vault folder names.
- Runtime entrypoint and auth boundary live in `app/main.py`.
- Environment keys described in the draft: `VAULT_PATH`, `INDEX_DB_PATH`, `MCP_API_TOKEN`, `TIMEZONE`.

## Storage Model

- Raw and memory trees are chronological with fixed segment shapes; do not invent extra semantic path levels (e.g. `topic/foo/` under `mcp_raw`).
- Required layout (under `VAULT_PATH`):
  - raw: `mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md`
  - memory: `memory/<YYYY>/<MM>/<MEMORY_ID>.md` for current writes
  - legacy memory: `20_AI_Memory/<memory_type>/<YYYY>/<MM>/<MEMORY_ID>.md` remains readable/updatable when already stored
  - daily: `10_Daily/<YYYY-MM-DD>.md` when daily append is used
- Retrieval logic must not treat folder names as the primary semantic API; use frontmatter and index metadata.

## Frontmatter Contract

- MCP-written documents use `schema_type` (`raw_conversation`, `memory_item`) and fields such as `mcp_id` / `memory_id` as implemented in `MarkdownStore` / `RawArchiveStore`.
- Human- or agent-generated drafts for Obsidian often use `note_kind: raw` and `note_kind: memory` before ingest; keep identifiers aligned with server fields when importing.
- Memory notes support multiple roles via `roles[]`.
- Do not use singular `memory_type` as the primary classifier for memory notes.
- `topics[]`, `entities[]`, `projects[]`, and `tags[]` are arrays.
- `raw_refs[]` links a memory note back to source raw conversation ids.
- Keep tags compatible with Obsidian YAML list format and nested tag patterns.
- Keep metadata normalized as arrays even when a note currently has only one value.

## Storage Unit Rules

- One conversation becomes one raw note.
- One conversation may yield zero to many memory notes.
- Split durable facts, decisions, preferences, todos, and summaries into separate memory notes when that improves retrieval quality.
- Do not force `1 conversation = 1 memory note`.
- Prefer one memory note per durable memory fragment.

## Retrieval Model

- Search and ranking should combine:
  - full-text match
  - `roles[]`
  - `topics[]`
  - `entities[]`
  - `projects[]`
  - recency
- Search clients must not depend on folder names for semantics.
- If compatibility wrappers are exposed, `search` should return relevant result lists and `fetch` should return full note content from the metadata-backed store.

## Confirmed Tool Surface

- `search_memory`
- `get_memory`
- `list_recent_memories`
- `save_memory`
- `update_memory`
- `archive_raw` (full transcript → `mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md`)
- Optional compatibility wrappers only if needed by the client surface:
  - `search`
  - `fetch`

## Commands

Confirmed from supplied content:

- Run MCP server: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

# [ASSUMPTION] Install, lint, format, typecheck, and test commands are not confirmed from repo evidence.

# Verify with: actual `pyproject.toml`, `package.json`, `Makefile`, `justfile`, CI workflows, or scripts.

## Boundaries

- Prefer minimal diffs.
- Ask before changing storage roots, frontmatter schema, auth flow, public endpoint shape, or MCP tool schemas.
- Ask before changing write semantics for `save_memory` or `update_memory`.
- Do not weaken bearer-token checks or broaden write-tool exposure without explicit approval.
- Do not commit live secrets, real machine paths, production URLs, or tokens.
- Do not assume community plugin dependencies unless they are present in the repo.

## Security

- Treat `MCP_API_TOKEN`, auth middleware, and public MCP exposure as security-sensitive.
- Never hard-code secrets.
- Mask or omit credentials in docs, tests, examples, and fixtures.
- Keep persistent write actions manual-by-default for high-risk operations.
- Use hooks, runtime checks, or CI for hard controls; do not rely on prose alone.

## Conventions

- Prefer explicit schema models over loose dict mutation.
- Keep storage, indexing, and transport concerns separated.
- Preserve human readability of vault notes.
- Avoid duplicating free-form classification in both ad-hoc path segments and metadata; current memory writes are chronological and semantics live in metadata/frontmatter.
- Reuse existing repository patterns before adding abstractions.
- Read-first behavior is preferred; write behavior must stay deliberate.

## Verification

- Do not report completion until the relevant checks have run or are explicitly marked manual.
- For storage changes, verify raw notes land under `mcp_raw/<source>/<YYYY-MM-DD>/`, new memory notes under `memory/<YYYY>/<MM>/`, and legacy `20_AI_Memory/...` notes remain readable.
- Verify `note_kind`, `roles[]`, `topics[]`, `entities[]`, `projects[]`, `tags[]`, and `raw_ref` serialize correctly.
- Verify one raw note can link to multiple memory notes without schema drift.
- Verify index rebuild and retrieval logic use metadata filters and full-text search, not folder semantics.
- For auth or transport changes, verify `/healthz` and `/mcp` behavior separately.
- Fix root causes. Do not suppress errors to make smoke checks appear green.

## Output Contract

- Summarize what changed.
- List files touched.
- List commands actually run.
- State pass/fail/manual verification status.
- State remaining assumptions, risks, and unverified areas.

## File Separation Rules

- Keep repo-wide, always-on guidance here.
- Put path-specific or team-specific overrides in nested `AGENTS.md` or `AGENTS.override.md` near the relevant code.
- Put repeated workflows into skills.
- Put deterministic enforcement into hooks or CI.

## Suggested Nested Guidance Later

- `obsidian-memory-plugin/AGENTS.md` for plugin-only TypeScript rules.
- `obsidian-mcp-server/AGENTS.md` for FastAPI/MCP server rules.
- Use `AGENTS.override.md` only when a subtree must override broader defaults.
