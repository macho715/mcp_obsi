---
name: obsidian-memory-workflow
description: Work safely with the Obsidian-backed memory model. Use when implementing markdown writes, daily note appends, or SQLite synchronization.
---
# Obsidian Memory Workflow

## When to Use
- Use when editing markdown persistence.
- Use when changing daily note behavior.
- Use when validating SQLite index synchronization.

## Steps
1. Preserve vault markdown as SSOT; treat SQLite as an index derived from markdown, not the authoritative store.
2. Preserve the markdown path convention under `20_AI_Memory/<type>/<YYYY>/<MM>/`.
3. Keep relative paths slash-normalized.
4. Ensure writes update markdown first, then SQLite.
5. Add or update tests covering markdown existence and index retrieval.
6. Report any backward-compatibility risk.

## Safety
- Do not widen automatic writes without explicit approval.
- Do not persist sensitive content raw.
