---
name: paste-conversation-to-obsidian
description: >-
  One-shot pipeline: user pastes a chat or transcript → delegate to metadata scout
  and memory splitter when needed → convert with obsidian-conversation-to-memory
  rules → verify → persist via MCP save_memory and archive_raw (or vault writes)
  → run production→desktop sync when required, merge repo-canonical raw into the app vault when applicable
  → close only after sync/merge outcomes are real (success or stated blocker). Use for paste-and-go vault capture.
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

> ⚠️ **CRITICAL WARNING / 중요 경고** ⚠️
> **모든 작업 및 데이터는 반드시 아래 Vault 경로를 사용해야 합니다:**
> C:\Users\jichu\Downloads\valut


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
- For **desktop app vault** target: `OBSIDIAN_LOCAL_VAULT_PATH` (optional). When present and production MCP wrote, finishing the run usually requires the Railway sync script (needs [`railway`](https://docs.railway.app/develop/cli) CLI linked to the service).

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

After each call, record returned **`id`** and **`path`** for the user summary. **Authoritative on-disk location:** `save_memory` / `archive_raw` response `path` values override draft `suggested_path` from subagents if they differ.

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

**`archive_raw` / raw ids:** Many servers validate `mcp_id` with a `convo-…` pattern. If a call fails pattern validation, rename to a matching `convo-…` id and align `raw_refs` via `update_memory` before retrying.

### 6) Obsidian app: visibility & sync decision

MCP and scripts **only write files under the server’s `VAULT_PATH` (or local repo `vault/`)**. There is **no** built-in push to the Obsidian mobile app or to Obsidian Sync servers.

Treat app visibility as a required finalization step, not an afterthought.

#### 6-A) If using local same-folder desktop

- If the write target is already the same folder that desktop Obsidian opened:
  - stop after persistence
  - report `same-folder desktop = immediate`
  - do **not** run a separate sync script

#### 6-B) If using remote production MCP and a local app vault exists

- If writes landed on remote production and the operator has a local Obsidian app vault:
  - **must run** `scripts/sync_railway_production_to_local_vault.ps1` from the **repo root** before claiming the pipeline complete (unless §6.1 outcome 1 already applies).
  - resolve local target from `OBSIDIAN_LOCAL_VAULT_PATH`, or pass `-LocalVaultPath` explicitly.
  - on **success:** report synced folders (from script JSON) and the memory/raw **relative** paths the user should open.
  - on **failure:** report the error (e.g. `railway` not logged in); do **not** claim `production -> local vault sync executed`—use `manual external sync still required` with the blocker.
- Use this path when the user explicitly wants “붙여넣기 한 번 -> 앱에서 바로 보이기”.
- If `OBSIDIAN_LOCAL_VAULT_PATH` is present, treat sync as the **default completion path** for remote production writes, not as an optional follow-up.

#### 6-C) If mobile / other machine only

- Do not claim immediate app visibility.
- State clearly that user-managed replication is still required:
  - Obsidian Sync
  - cloud drive
  - manual copy/export

### 6.1) Required sync execution rule

After persistence, choose exactly one of:

1. `same-folder desktop` -> no extra sync command
2. `production -> local vault sync` -> run `scripts/sync_railway_production_to_local_vault.ps1`
3. `manual external sync required` -> explain limitation plainly

Do not end the pipeline before one of those three outcomes is stated **and** executed when execution is implied (outcome 2 means the script actually ran or a blocker was recorded).
If the user asked for “옵시디언 앱에 바로 보이게” / “싱크까지”, and `OBSIDIAN_LOCAL_VAULT_PATH` exists, outcome 2 is required unless outcome 1 already applies.

### 6.2) Canonical raw merge (after production sync, when applicable)

When **both** are true:

1. You have an authoritative full raw file under the **workspace / repo** vault at the same relative path returned by `archive_raw` or local `MemoryStore` (e.g. `mcp_raw/cursor/2026-03-28/convo-….md`), **and**
2. You pulled production into `OBSIDIAN_LOCAL_VAULT_PATH` via §6-B (so the app vault may contain an older or stub `archive_raw` body),

then **copy that repo file over** the matching path inside `OBSIDIAN_LOCAL_VAULT_PATH` (create parent dirs if needed). Use PowerShell `Copy-Item -LiteralPath` (or equivalent). Do not invent folder names; reuse the **same relative path** under each vault root.

If there was only a single write target and no fuller repo copy exists, state **N/A** for this step.

### 6.3) Definition of “pipeline complete”

You may call the paste workflow **complete** only when:

- §4 verifier outcome is acceptable, **and**
- §5 persistence succeeded (or documented fallback write), **and**
- §6.1 sync outcome is chosen and—if outcome 2—§6-B actually ran or a blocker is explicitly reported, **and**
- §6.2 is done or explicitly **N/A**.

After successful writes, do **all** of the following in the user-facing summary:

1. **Desktop Obsidian (same PC)**  
   - Tell the user to open **exactly the same folder** as the write target: the MCP host’s `VAULT_PATH`, or the workspace `vault/` when using local `MemoryStore`.  
   - If they already have that folder as a vault, files appear as normal notes; Obsidian watches the filesystem—**no extra sync step**.  
   - If files do not show: wrong vault, or Obsidian needs a restart; suggest **file explorer** navigation to the returned relative `path` under vault root.

2. **Phone / tablet / second PC**  
   - MCP does **not** deliver to those devices. The vault directory must already be replicated by **Obsidian Sync**, **iCloud/Dropbox/Git/etc.**, or manual copy.  
   - State this limitation plainly and mention that **`VAULT_PATH` must be the synced folder** (or users must copy exported paths into that folder).

3. **Remote production MCP**  
   - Writes land on the **server’s** disk. Local Obsidian will **not** see them unless that path is shared (network drive, sync, or deliberate export).  
   - Call out when **local** vs **production** profile was used so the user does not search the wrong vault.

4. **Optional deep link**  
   - If `OBS_VAULT_NAME` (or equivalent) is known: `obsidian://open?vault=<name>&file=<relative path from vault root>`.

### 7) Close the loop

Reply with:

- Count of `save_memory` calls and each returned **`path`** / `id`.
- Raw file path (or explicit manual-save instructions).
- **Which disk vault** the writes used (local `vault/` vs production `VAULT_PATH`—describe as “same folder Obsidian should open”, without inventing private paths).
- **Sync result:** one of
  - `same-folder desktop, no extra sync needed`
  - `production -> local vault sync executed`
  - `manual external sync still required`
- **Completion claim:** only say the pipeline is fully complete when §6.3 is satisfied (sync + optional canonical merge), not merely when MCP calls returned OK.
- Link pattern the server uses for Obsidian: `obsidian://open?vault=…&file=…` when settings are known.
- Any verifier **PASS WITH AMBIGUITIES** items.

## Safety

- **Read-first:** if unsure whether the user wanted a durable write, confirm once before calling `save_memory` or `archive_raw`.
- Do not persist **credentials, tokens, or unredacted PII**; mask or refuse per project privacy rules.
- Respect [`obsidian-memory-workflow`](../obsidian-memory-workflow/SKILL.md): markdown on disk is SSOT; SQLite is derived.

## References

- [`obsidian-conversation-to-memory`](../obsidian-conversation-to-memory/SKILL.md)
- [`../obsidian-conversation-to-memory/references/obsidian-output-contract.md`](../obsidian-conversation-to-memory/references/obsidian-output-contract.md)
