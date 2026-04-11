---
name: obsidian-memory-workflow
description: Work safely with the Obsidian-backed memory model. Use when implementing markdown writes, daily note appends, or SQLite synchronization.
---

> ⚠️ **CRITICAL WARNING / 중요 경고** ⚠️
> **모든 작업 및 데이터는 반드시 아래 Vault 경로를 사용해야 합니다:**
> C:\Users\jichu\Downloads\valut

# Obsidian Memory Workflow

## When to Use
- Use when editing markdown persistence.
- Use when changing daily note behavior.
- Use when validating SQLite index synchronization.

## Steps
1. Preserve vault markdown as SSOT; treat SQLite as an index derived from markdown, not the authoritative store.
2. Preserve path conventions from `AGENTS.md` / server implementation (e.g. `memory/<YYYY>/<MM>/`, `mcp_raw/<source>/<YYYY-MM-DD>/`, `10_Daily/`). `20_AI_Memory/…` may exist for legacy reads only—do not assume it for new writes without checking code.
3. Keep relative paths slash-normalized.
4. Ensure writes update markdown first, then SQLite.
5. Add or update tests covering markdown existence and index retrieval.
6. Report any backward-compatibility risk.

## One-shot desktop sync rule

When the user expectation is “save and immediately see it in Obsidian app”, choose one path explicitly:

1. **Local same-folder write**
   - preferred when `VAULT_PATH` already points at the desktop app vault
   - result: file appears without extra sync
2. **Remote production write + local sync**
   - run `scripts/sync_railway_production_to_local_vault.ps1`
   - local target should come from `OBSIDIAN_LOCAL_VAULT_PATH` or explicit operator input
3. **Manual external sync**
   - only when neither of the above is available

Do not report “Obsidian 업로드 완료” unless one of those paths has been satisfied and named.
If `OBSIDIAN_LOCAL_VAULT_PATH` is available and the write target was remote production, the default expected behavior is to run the sync script in the same flow.

### Completion gate (paste / one-shot)

Do **not** treat the job as finished after MCP `save_memory` / `archive_raw` alone when the user expects the **desktop Obsidian vault** to show the notes. In the same flow:

1. Resolve §6.1 style outcome from [`paste-conversation-to-obsidian`](../paste-conversation-to-obsidian/SKILL.md) (same-folder vs Railway sync vs manual).
2. If Railway sync runs, execute `scripts/sync_railway_production_to_local_vault.ps1` from repo root and record pass/fail.
3. If a fuller `archive_raw` exists under repo `VAULT_PATH` than what production may hold, copy that file onto the **same relative path** under `OBSIDIAN_LOCAL_VAULT_PATH` after sync (canonical merge).

## Obsidian app & multi-device behavior
- **Desktop:** Point Obsidian’s vault at the same directory as `VAULT_PATH` (or repo `vault/`). File writes from MCP/scripts show up like any other file change; there is no separate “sync to app” API call.
- **Desktop one-shot via remote MCP:** if writes land on production instead of the app’s local folder, use `scripts/sync_railway_production_to_local_vault.ps1` to pull the production vault into the desktop app vault before claiming visibility.
- **One-shot default:** when the request says “한 번에”, “바로 앱에서”, or equivalent, prefer local same-folder writes first; otherwise perform production write then local sync in the same run.
- **Mobile / other machines:** MCP does not push there. Use Obsidian Sync or mirror the vault folder with your chosen sync tool; alternatively export/copy markdown into that synced vault.
- **Remote MCP:** Writes occur on the server filesystem unless configured otherwise; local Obsidian only reflects those files if that path is available locally or replicated.

## Safety
- Do not widen automatic writes without explicit approval.
- Do not persist sensitive content raw.
