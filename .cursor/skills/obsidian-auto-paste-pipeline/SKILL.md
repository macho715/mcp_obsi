---
name: obsidian-auto-paste-pipeline
description: >-
  Fully automatic paste pipeline: no pre-save confirmation, always run metadata scout
  and memory splitter in parallel → convert → verify → MCP save_memory and archive_raw
  → production→local vault sync and canonical raw merge when applicable → open Obsidian
  via obsidian:// when OBS_VAULT_NAME and paths are known. Use when the user wants
  paste-and-go with zero prompts, full sync to desktop Obsidian, or “완전 자동” vault capture.
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
    - paste-conversation-to-obsidian
---

# Obsidian auto-paste pipeline (autopilot)

Run the same end state as [paste-conversation-to-obsidian](../paste-conversation-to-obsidian/SKILL.md) (**raw archive + atomic memory notes + §6 sync/merge rules**), but with **autopilot policy** below. Normative steps for persistence, Railway sync, canonical raw copy, and completion reporting are defined there (§5, §6, §6.1–§6.3, §7): follow that skill in order after ingest/conversion/verify, unless this file overrides.

## When to use

- User pasted a chat or transcript and asked for **fully automatic** save to Obsidian / vault / memory with **no confirmation** before writes.
- User wants **옵시디언 앱 싱크까지** in one shot when local desktop + env (see Limits) allow.

Prefer [paste-conversation-to-obsidian](../paste-conversation-to-obsidian/SKILL.md) when the user may want to confirm `source`, `project`, or save intent once.

## Limits (state explicitly if applicable)

- **Mobile / other device only:** MCP does not push to Obsidian Sync. Automation stops at “manual replication required.”
- **Production → local:** [sync_railway_production_to_local_vault.ps1](../../../scripts/sync_railway_production_to_local_vault.ps1) needs a working [`railway`](https://docs.railway.app/develop/cli) CLI; on failure report the blocker—do not claim sync ran.
- **Secrets / tokens / unredacted PII:** refuse or mask; autopilot does not bypass privacy rules.

## Autopilot policy (overrides paste skill where they conflict)

1. **No pre-save confirmation**  
   When this skill is in effect, do **not** ask “should I save?” before `save_memory` or `archive_raw`. Proceed after verifier PASS (or after minimal draft fixes and re-verify).  
   Exception: tool/schema errors that cannot be resolved without missing required fields—then report the error, do not invent arguments.

2. **Always parallel specialists**  
   Always launch **`obsidian-metadata-scout`** and **`obsidian-memory-splitter`** in **parallel** with the full pasted text. Do **not** skip them for short or single-topic pastes.

3. **Defaults**  
   - `source`: use environment variable `PASTE_DEFAULT_SOURCE` if set; otherwise `cursor`.  
   - `append_daily`: follow server default (same as paste skill).  
   - `project`, language, extra tags: infer only from the pasted text; omit if absent.

4. **Convert and verify**  
   Apply [obsidian-conversation-to-memory](../obsidian-conversation-to-memory/SKILL.md), then **`obsidian-memory-verifier`** (or equivalent checklist). Same bar as paste skill §3–§4.

5. **Persist, sync, merge, complete**  
   Execute [paste-conversation-to-obsidian](../paste-conversation-to-obsidian/SKILL.md) **§5 Persist**, **§6 / §6.1–§6.3**, and **§7** verbatim regarding MCP mapping, sync outcomes, and completion claims.

## Open Obsidian app (desktop, when possible)

After persistence and—if required—§6-B sync and §6.2 merge succeed:

- If **`OBS_VAULT_NAME`** is set (see [docs/CONTRIB.md](../../../docs/CONTRIB.md)) and you have a **vault-relative file path** from MCP (e.g. newest memory or raw note), **must** attempt to open the note in the desktop app.

On **Windows**, run (adjust `vault` and URL-encode `file` per Obsidian URI rules):

```powershell
Start-Process "obsidian://open?vault=$env:OBS_VAULT_NAME&file=<relative/path/from/vault/root.md>"
```

If `Start-Process` fails, record the error and still include the `obsidian://` URL in the user summary. **Pipeline completion** remains tied to disk writes + §6.3 (sync path), not to whether the URI launch succeeded.

## References

- [paste-conversation-to-obsidian](../paste-conversation-to-obsidian/SKILL.md) — persistence tables, sync script, merge, close-the-loop output
- [obsidian-output-contract.md](../obsidian-conversation-to-memory/references/obsidian-output-contract.md)
- [AGENTS.md](../../../AGENTS.md)
