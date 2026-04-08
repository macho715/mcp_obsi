# AGENTS.md

This file is based on the supplied architecture and patch notes, then aligned with the current storage layout assumptions around `app/services/memory_store.py`, `raw_archive_store.py`, and `app/utils/ids.py`.

Verify against the real filesystem, `README`, `pyproject.toml`, lockfiles, CI workflows, scripts, and implemented schemas before changing behavior.

## Scope

This repository implements a hybrid memory system for coding agents.

- **Local layer**: an Obsidian plugin curates raw conversations, normalized memory notes, frontmatter, and index rebuilds.
- **Remote layer**: a FastAPI + FastMCP server exposes shared memory tools over a public HTTPS MCP endpoint.
- **Durable storage**: human-readable Markdown in the Obsidian vault.
- **Indexes**: SQLite and JSON indexes are rebuildable helpers, not the primary source of truth.

## Confirmed Components From the Design Draft

### Obsidian plugin

- `obsidian-memory-plugin/`
- `src/main.ts`, `src/types.ts`, `src/settings.ts`, `src/services/vault-store.ts`

### MCP server

- current runtime lives at repo root `app/` (historical design-draft name: `obsidian-mcp-server/`)
- `app/main.py`, `app/config.py`, `app/models.py`, `app/mcp_server.py`
- `app/services/index_store.py`, `app/services/markdown_store.py`, `app/services/memory_store.py`

### Vault layout under `VAULT_PATH`

As described in the supplied draft and expected `MemoryStore._ensure_structure` behavior:

- `mcp_raw/` — raw conversation markdown: `mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md`
- `memory/` — current memory markdown write target: `memory/<YYYY>/<MM>/<MEMORY_ID>.md`
- `20_AI_Memory/` — legacy memory markdown read/update compatibility path
- `10_Daily/` — daily note append targets
- `90_System/` — reserved for vault-local system artifacts, but **not** the canonical SQLite index path

### Search index

- SQLite lives at `INDEX_DB_PATH` via `IndexStore`
- Do **not** assume a fixed vault-local SQLite path unless code proves it

## Source of Truth

- Markdown notes in the vault are the source of truth.
- SQLite at `INDEX_DB_PATH` is a rebuildable index derived from markdown, not primary storage.
- MCP tool contracts are defined by the server implementation, not by vault folder names.
- Runtime entrypoint and auth boundary live in `app/main.py`.
- Environment keys described in the draft include: `VAULT_PATH`, `INDEX_DB_PATH`, `MCP_API_TOKEN`, `TIMEZONE`.

## Storage Model

Raw and memory trees are chronological with fixed segment shapes.
Do **not** invent extra semantic path levels under the MCP-managed trees.

### Required layout under `VAULT_PATH`

- raw: `mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md`
- memory: `memory/<YYYY>/<MM>/<MEMORY_ID>.md` for current writes
- legacy memory: `20_AI_Memory/<memory_type>/<YYYY>/<MM>/<MEMORY_ID>.md` remains readable/updatable when already stored
- daily: `10_Daily/<YYYY-MM-DD>.md` when daily append is used

Retrieval logic must not treat folder names as the primary semantic API. Use frontmatter and index metadata.

## Frontmatter Contract

- MCP-written documents use `schema_type` (`raw_conversation`, `memory_item`) and fields such as `mcp_id` / `memory_id` as implemented in `MarkdownStore` / `RawArchiveStore`.
- Human- or agent-generated drafts for Obsidian may use `note_kind: raw` and `note_kind: memory` before ingest; keep identifiers aligned with server fields when importing.
- Memory notes support multiple roles via `roles[]`.
- Do **not** use singular `memory_type` as the primary classifier for memory notes.
- `topics[]`, `entities[]`, `projects[]`, and `tags[]` are arrays.
- `raw_refs[]` links a memory note back to source raw conversation ids.
- Keep tags compatible with Obsidian YAML list format and nested tag patterns.
- Keep metadata normalized as arrays even when a note currently has only one value.

## Storage Unit Rules

- One conversation becomes one raw note.
- One conversation may yield zero to many memory notes.
- Split durable facts, decisions, preferences, todos, and summaries into separate memory notes when that improves retrieval quality.
- Do **not** force `1 conversation = 1 memory note`.
- Prefer one memory note per durable memory fragment.

## Retrieval Model

Search and ranking should combine:

- full-text match
- `roles[]`
- `topics[]`
- `entities[]`
- `projects[]`
- recency

Search clients must not depend on folder names for semantics.
If compatibility wrappers are exposed, `search` should return relevant result lists and `fetch` should return full note content from the metadata-backed store.

## Confirmed Tool Surface

- `search_memory`
- `get_memory`
- `list_recent_memories`
- `save_memory`
- `update_memory`
- `archive_raw` — full transcript → `mcp_raw/<source>/<YYYY-MM-DD>/<mcp_id>.md`

Optional compatibility wrappers only if needed by the client surface:

- `search`
- `fetch`

## Commands

Historical repo evidence (2026-04-07 verified run):

- `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- `.venv\Scripts\python.exe -m pytest -q` → 65 passed
- `.venv\Scripts\python.exe -m ruff check .` → All checks passed
- `.venv\Scripts\python.exe -m ruff format --check .` → 22 files already formatted
- `.venv\Scripts\python.exe -c "from app.main import app"` → OK

Current workspace recheck (2026-04-08 doc-sync turn):

- `.venv\Scripts\python.exe -m pytest -q` → 65 passed
- `.venv\Scripts\python.exe -m ruff check .` → fail (`11` existing issues, including tracked `app.py`)
- `.venv\Scripts\python.exe -m ruff format --check .` → fail (`3` files would be reformatted)
- `.venv\Scripts\python.exe -c "from app.main import app; print(app.title)"` → `obsidian-mcp`

Install (dev + mcp extras):

- `pip install -e ".[dev,mcp]"` or `uv sync --extra dev --extra mcp`

## Boundaries

Prefer minimal diffs.

Ask before changing any of the following:

- storage roots
- frontmatter schema
- auth flow
- public endpoint shape
- MCP tool schemas
- write semantics for `save_memory` or `update_memory`
- bearer-token checks or write-tool exposure

Do not commit live secrets, real machine paths, production URLs, or tokens.
Do not assume community plugin dependencies unless they are present in the repo.

## Security

- Treat `MCP_API_TOKEN`, auth middleware, and public MCP exposure as security-sensitive.
- Never hard-code secrets.
- Mask or omit credentials in docs, tests, examples, and fixtures.
- Keep persistent write actions manual-by-default for high-risk operations.
- Use hooks, runtime checks, or CI for hard controls; do not rely on prose alone.
- **Read-only MCP mounts** (`/chatgpt-mcp`, `/claude-mcp`) carry **no bearer auth by design** (see `app/main.py` `_expected_bearer_for_path`). Protect at network/proxy layer when deployed publicly. If a dedicated read token is needed, it requires explicit approval under the auth-change gate.
- If `MCP_API_TOKEN` is empty, bearer enforcement for `/mcp` is skipped. Always set a non-empty token in production; the default `dev-change-me` value must not reach production unchanged.

## Conventions

- Prefer explicit schema models over loose dict mutation.
- Keep storage, indexing, and transport concerns separated.
- Preserve human readability of vault notes.
- Avoid duplicating free-form classification in both ad-hoc path segments and metadata.
- Current memory writes are chronological and semantics live in metadata/frontmatter.
- Reuse existing repository patterns before adding abstractions.
- Read-first behavior is preferred; write behavior must stay deliberate.

## Verification

Do not report completion until the relevant checks have run or are explicitly marked manual.

### Code quality (historical 2026-04-07 snapshot)

- `ruff check .` → All checks passed (app/ + scripts/)
- `ruff format --check .` → 22 files already formatted
- `pytest -q` → 65 passed, 0 failed
- `from app.main import app` → import OK

### Code quality (current 2026-04-08 recheck)

- `pytest -q` → 65 passed, 0 failed
- `ruff check .` → fail (`11` existing issues, including `app.py`)
- `ruff format --check .` → fail (`3` files would be reformatted)
- `from app.main import app; print(app.title)` → `obsidian-mcp`

### Storage verification

- raw notes land under `mcp_raw/<source>/<YYYY-MM-DD>/`
- new memory notes land under `memory/<YYYY>/<MM>/`
- legacy `20_AI_Memory/...` notes remain readable
- `note_kind`, `roles[]`, `topics[]`, `entities[]`, `projects[]`, `tags[]`, and `raw_refs[]` serialize correctly
- one raw note can link to multiple memory notes without schema drift
- index rebuild and retrieval logic use metadata filters and full-text search, not folder semantics

### KB workflow verification (2026-04-07 e2e confirmed)

- `obsidian-ingest` → raw archived, `archive_raw` stored, `save_memory` pointer created
- `obsidian-query` → Ollama search + synthesis answer returned with citations
- `obsidian-lint` → deterministic + semantic checks, patch plan written to `runtime/patches/`, `save_memory` audit pointer created

### KB + companion integration verification (2026-04-08 confirmed)

- `obsidian-ingest` manual run → raw archived, canonical note written to external vault, index/log updated
- MCP `archive_raw` API call → `convo-chatgpt-projects-pipeline-standard-2026-04-08` returned with path `mcp_raw/obsidian-ingest/2026-04-08/...`
- MCP `save_memory` API call → `MEM-20260408-163522-F9FE2A` returned as saved pointer id
- temp `local-rag` against external vault → ingested note returned as retrieval source
- temp `standalone-package` against that `local-rag` + local MCP → `/api/ai/chat`, `/api/memory/search`, `/api/memory/fetch` verified

### Transport/auth verification

- verify `/healthz` and `/mcp` separately when auth or transport changes
- verify `/chatgpt-mcp`, `/claude-mcp` read-only exposure is covered by network-layer restriction when running publicly

Fix root causes. Do not suppress errors to make smoke checks appear green.

## Output Contract

Always report:

- what changed
- files touched
- commands actually run
- pass/fail/manual verification status
- remaining assumptions, risks, and unverified areas

## File Separation Rules

- Keep repo-wide, always-on guidance here.
- Put path-specific or team-specific overrides in nested `AGENTS.md` or `AGENTS.override.md` near the relevant code.
- Put repeated workflows into Skills.
- Put deterministic enforcement into hooks or CI.

## LLM Runtime Policy

- Local LLM provider is fixed to **Ollama**.
- Default endpoint is `http://localhost:11434`. Override with `OLLAMA_BASE_URL`.
- Primary model is `gemma4:e4b`.
- Lightweight tasks may use `gemma4:e2b`.
- Skills should call Ollama through a shared helper such as `scripts/ollama_kb.py::generate()` rather than scattering raw HTTP logic across multiple files.
- Default API style is Ollama native `/api/chat`.
- OpenAI-compatible mode is optional and secondary.
- Timeout is `300s` by default and may be overridden by `OLLAMA_TIMEOUT`.
- Use `keep_alive` consistently if model residency matters.
- sibling `standalone-package` local-only route should default to `gemma4:e4b` when routed local and the caller omits `model`; explicit model override still wins.

## KB Routing Policy

This repository has **three persistence layers** in the external Obsidian vault:

- `vault/raw/` = immutable original source copies (web clips, PDFs, manual notes) — **never modify**
- `vault/mcp_raw/` = raw evidence archived via `archive_raw` MCP tool — immutable after write
- `vault/memory/` = MCP-managed chronological memory store for pointers, summaries, decisions, and durable facts

### vault/raw/ subtrees (immutable source copies)

- `vault/raw/articles/` — web articles and pasted text
- `vault/raw/pdf/` — PDF documents
- `vault/raw/notes/` — manual pre-ingest notes

### Core routing rules

1. `memory/` is **not** the canonical KB — pointers only.
2. `mcp_raw/` is the raw-evidence archive written by `archive_raw`; it is immutable after write and excluded from the SQLite memory index/search surface.
3. `raw/` is the immutable source copy layer — write once, never edit.
4. Do not duplicate full content into `memory/`.
5. Do not dump raw transcripts into memory notes.
6. Persist reusable knowledge in the external vault's wiki/ (if needed), then register a pointer summary in `memory/`.

### Route by artifact type

#### Store in `vault/mcp_raw/` or equivalent raw staging

Use for:

- original transcripts
- OCR output
- imported raw markdown
- pre-ingest extraction JSON
- temporary parsing artifacts
- source bundles awaiting normalization

Keep raw storage immutable whenever feasible.

#### Store in external vault's wiki/ (optional)

If the external vault has a `wiki/` subtree, use it for:

- concept notes
- entity notes
- reusable analyses
- link-rich canonical notes

Canonical wiki writing is optional. The primary KB is the memory pointer system.

#### Store via `save_memory`

Use only for:

- pointer cards to canonical wiki notes
- short approved summaries
- decision records
- recent analysis pointers
- lint run summaries
- next-session retrieval hints

`save_memory` content should contain:

- `type` / `kind`
- title
- short summary
- tags
- `wiki_path` or `wiki_link`
- optional `raw_path`
- status such as `draft`, `review`, or `final`

`save_memory` must **not** contain:

- full canonical wiki note bodies
- raw transcript bodies
- repeated long-form markdown already stored in `wiki/`

## KB Workflow Rules

KB workflows are implemented as **3 independent Cursor Skills**:

- `obsidian-ingest`
- `obsidian-query`
- `obsidian-lint`

### Workflow behavior

- Canonical knowledge is written to the external vault's `wiki/` directory directly (if present), not through existing MCP memory-write tools.
- `save_memory` stores only a pointer plus short summary, never the full canonical note.
- External vault `wiki/index.md` and `wiki/log.md` should be updated after any material KB addition.
- Operational byproducts such as patch plans and audit results belong in `runtime/patches/` and `runtime/audits/` outside `vault/` when possible.
- Shared Ollama request schema, model names, timeout, and error handling must stay identical across skills. Change common behavior in one helper, not ad hoc in each skill.

### Per-workflow routing

#### ingest

1. archive/import raw source
2. analyze and normalize
3. write canonical note(s) to external vault's `wiki/` (if present)
4. update `wiki/index.md` and `wiki/log.md` in external vault if they exist
5. register pointer summary via `save_memory`

#### query

1. search `vault/wiki/` in the external vault first (if present)
2. use `memory/` as recent pointer/history support when helpful
3. if the result is reusable, save it to external vault's `wiki/analyses/` if that subtree exists
4. register a short pointer via `save_memory`

#### lint

1. inspect external vault's `wiki/` for contradiction, stale claim, orphan note, missing cross-reference, and evidence gap (if present)
2. produce patch plan first for risky edits
3. apply safe edits deliberately
4. update `wiki/log.md` in external vault if it exists
5. save only a compact lint summary/pointer via `save_memory`

## Pointer Template Policy

When KB workflows write to `save_memory`, they should store a compact pointer record rather than a duplicate note body.

### Recommended fields

- `type: memory_pointer`
- `kind: source | analysis | concept | entity | lint | decision`
- `status: draft | review | final | superseded`
- `title`
- `summary` as 3-8 concise lines
- `wiki_path`
- `wiki_link`
- optional `raw_path`
- `tags`

### Example shape

```yaml
---
type: memory_pointer
kind: analysis
status: final
title: Example KB Note
wiki_path: "vault/wiki/analyses/example-kb-note.md"
wiki_link: "[[wiki/analyses/example-kb-note]]"
raw_path: "vault/mcp_raw/source/2026-04-07/example.md"
tags:
  - kb
  - pointer
  - analysis
---
```

## Approval Gates

Ask before:

- changing canonical wiki structure
- deleting or merging existing canonical notes
- changing MCP storage roots or schemas
- introducing server-side KB write tools in `app/`
- broadening `save_memory` to store long-form wiki content

## Suggested Nested Guidance Later

- `obsidian-memory-plugin/AGENTS.md` for plugin-only TypeScript rules
- `obsidian-mcp-server/AGENTS.md` for FastAPI/MCP server rules
- use `AGENTS.override.md` only when a subtree must override broader defaults
