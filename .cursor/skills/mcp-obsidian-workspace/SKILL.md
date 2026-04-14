---
name: mcp-obsidian-workspace
description: >-
  Orients Cursor agents to the mcp_obsidian repository: which project skill to
  read for memory vault work, MCP server changes, paste-to-vault pipelines, and
  release tasks. Use when the workspace is this repo, when the user mentions
  `.cursor/skills`, Obsidian MCP, memory SSOT, or needs a skill map before
  editing `app/`, vault paths, or Cursor agent/skill files.
---

# mcp_obsidian workspace (project skills hub)

## Read first

1. [AGENTS.md](../../../AGENTS.md) — repo-wide work contract.
2. [README.md — Document Map](../../../README.md) — where install, architecture, and runbooks live.

## Route the task → skill

| Situation | Open |
| --------- | ---- |
| Paste chat / one-shot save to vault, MCP `save_memory` + sync expectations | [paste-conversation-to-obsidian](../paste-conversation-to-obsidian/SKILL.md) |
| Same as above but **fully automatic** (no pre-save prompts; always scout+splitter; optional `obsidian://` open) | [obsidian-auto-paste-pipeline](../obsidian-auto-paste-pipeline/SKILL.md) |
| Convert transcript or dialogue into raw + memory notes (schemas, frontmatter) | [obsidian-conversation-to-memory](../obsidian-conversation-to-memory/SKILL.md) |
| Markdown-first writes, daily notes, SQLite index, desktop vs Railway visibility | [obsidian-memory-workflow](../obsidian-memory-workflow/SKILL.md) |
| Change `/mcp`, tools, auth, memory tool payloads | [mcp-contract-review](../mcp-contract-review/SKILL.md) |
| New machine / venv / `.env` / first `pytest` | [repo-bootstrap](../repo-bootstrap/SKILL.md) |
| Before push / PR / handoff (pytest + ruff + secrets sanity) | [release-check](../release-check/SKILL.md) |
| Copy Obsidian converter bundle to another repo; map `.cursor` files | [cursor-obsidian-converter-package](../cursor-obsidian-converter-package/SKILL.md) |
| Add or edit `.cursor/agents/*.md` | [cursor-subagent-authoring](../cursor-subagent-authoring/SKILL.md) |

`repo-bootstrap` and `release-check` may be marked non-auto-invoke; still follow them when the user asks for setup or pre-release checks.

## Implementation anchors

- Vault layout and paths: align with server code and `AGENTS.md` (e.g. `memory/<YYYY>/<MM>/`, `mcp_raw/`, `10_Daily/`).
- Tests: `pytest -q` from repo root; extend tests when changing persistence or MCP contracts.

## Subagents (paste pipeline)

Paste workflows may reference `.cursor/agents/`: `obsidian-metadata-scout`, `obsidian-memory-splitter`, `obsidian-memory-verifier`, `obsidian-paste-autopilot`, plus planner/verifier patterns — details in [paste-conversation-to-obsidian](../paste-conversation-to-obsidian/SKILL.md) or [obsidian-auto-paste-pipeline](../obsidian-auto-paste-pipeline/SKILL.md).
