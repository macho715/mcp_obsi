---
name: cursor-obsidian-converter-package
description: >-
  Installs or explains the Cursor Obsidian conversation bundle (one conversion
  skill, four subagents, plus this installer skill) from the directory that
  contains `README.md` and `.cursor/`. Use when the user asks to add the
  Obsidian converter package, copy conversation-to-memory tooling into another
  repo, sync `.cursor` agents or skills from this bundle, or needs a map of
  included files before converting chats to vault notes.
---

> ⚠️ **CRITICAL WARNING / 중요 경고** ⚠️
> **모든 작업 및 데이터는 반드시 아래 Vault 경로를 사용해야 합니다:**
> C:\Users\jichu\Downloads\valut


# Cursor Obsidian converter package

## Bundle root

For a **portable copy** of this package, **bundle root** is the directory that contains that copy’s `README.md` and `.cursor/`. All paths below are `bundle-root/.cursor/...`.

In the **`mcp_obsidian` monorepo**, the primary Cursor config lives at the **repository root** (`.cursor/` alongside `AGENTS.md`, `app/`, etc.). The subdirectory [`cursor-obsidian-converter-package/`](../../../cursor-obsidian-converter-package) is the **vendoring slice**: copy from there into other projects. Edit repo-root `.cursor/` when working in this repository; keep the subdirectory in sync when you maintain the export bundle.

## Purpose

This bundle ships a portable `.cursor` slice: conversion skill `obsidian-conversation-to-memory`, four subagents, and this skill for **what to copy where** and **what to read next**. It does not replace the conversion rules inside `obsidian-conversation-to-memory`.

## When to use this skill

- Installing or copying the Obsidian converter / conversation package
- Vendoring `.cursor/skills` or `.cursor/agents` from this bundle
- Questions about raw note templates, `save_memory` shapes, or Obsidian-related subagents
- Reconciling duplicate nested folders under `cursor-obsidian-converter-package/` (see below)

For **actual conversion** of dialogue into raw + memory notes, use `.cursor/skills/obsidian-conversation-to-memory/SKILL.md` in the **target** repo after merge (or in this repo if already present).

## Included paths (under `bundle-root/.cursor/`)

| Path | Role |
|------|------|
| `skills/obsidian-conversation-to-memory/SKILL.md` | Main conversion workflow |
| `skills/obsidian-conversation-to-memory/references/obsidian-output-contract.md` | Output contract (paths aligned with `mcp_obsidian` `AGENTS.md` / `app/services/*_store.py` when present) |
| `skills/obsidian-conversation-to-memory/assets/raw-note-template.md` | Raw note template |
| `skills/obsidian-conversation-to-memory/assets/memory-note-template.md` | Memory note template |
| `skills/obsidian-conversation-to-memory/assets/save-memory-v2.schema.json` | Optional JSON schema |
| `skills/cursor-obsidian-converter-package/SKILL.md` | This installer / map skill |
| `agents/obsidian-metadata-scout.md` | Long or noisy input: metadata candidates |
| `agents/obsidian-memory-splitter.md` | Long input: atomic memory splits |
| `agents/obsidian-memory-verifier.md` | Schema and policy verification (includes sync + canonical-merge checks when paste workflow applies) |
| `agents/obsidian-converter-package.md` | Bundle install: inventories, merge plan, clash detection |

**mcp_obsidian repo root only (not in portable bundle by default):** `skills/paste-conversation-to-obsidian/SKILL.md` — one-shot paste → MCP persist → **Railway sync + optional repo-canonical raw merge** into `OBSIDIAN_LOCAL_VAULT_PATH` before claiming complete. Vendoring: copy that skill and `skills/obsidian-memory-workflow/` together if you need the same close-the-loop rules.

## Nested duplicate folder

If a second tree exists at `bundle-root/cursor-obsidian-converter-package/.cursor/`, treat it as accidental duplication. Prefer `bundle-root/.cursor/` unless the user says otherwise.

## Install into another repository

1. Open the target repo root (where that project’s `.cursor/` should live).
2. **Merge** (do not blindly delete existing entries):
   - Copy `skills/obsidian-conversation-to-memory/` → target `.cursor/skills/obsidian-conversation-to-memory/`
   - Copy `skills/cursor-obsidian-converter-package/` → target `.cursor/skills/cursor-obsidian-converter-package/`
   - Copy `agents/obsidian-*.md` → target `.cursor/agents/`
3. Resolve name clashes before overwriting; ask the user if unsure.
4. For conversions, follow `obsidian-conversation-to-memory` in the **target** repo.

Alternative: copy the whole `bundle-root/.cursor/` over the target `.cursor/` only after reviewing clashes (see agent `obsidian-converter-package`).

## After install

- **Conversion work**: skill `obsidian-conversation-to-memory` only.
- **Package / install questions**: this skill or subagent `obsidian-converter-package`.

## Safety

- Do not change MCP tool contracts, vault roots, or auth from this install flow unless the user explicitly requests it and project rules allow it.
- Show a file list and merge plan before destructive overwrites of `.cursor/` content.

## Quick reference

Human-readable overview: `bundle-root/README.md`.

## Maintenance (duplicate file)

This file is mirrored at `cursor-obsidian-converter-package/.cursor/skills/cursor-obsidian-converter-package/SKILL.md`. Edit both together so install docs and Cursor discovery stay aligned.
