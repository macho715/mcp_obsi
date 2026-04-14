---
name: cursor-subagent-authoring
description: >-
  Author Cursor subagents (`.cursor/agents/*.md`) and optional paired skills
  (`.cursor/skills/<skill-name>/SKILL.md`) for this repository. Use when the
  user wants a new agent file, frontmatter help, or a checklist before saving.
---
# Cursor subagent authoring (`mcp_obsidian` repo)

## When to use

- Adding or rewriting a file under `.cursor/agents/`.
- Deciding whether a companion skill under `.cursor/skills/` is needed.
- Matching the conventions already used here (see `planner.md`, `verifier.md`, `obsidian-memory-splitter.md`).

## Agent file location and naming

- Path: `.cursor/agents/<kebab-case-name>.md`
- `name` in frontmatter should match the filename stem (e.g. file `obsidian-memory-splitter.md` → `name: obsidian-memory-splitter`).

## Required YAML frontmatter

Use this shape (adjust values):

```yaml
---
name: <kebab-case-name>
description: >-
  One line: what it does and when to invoke it. Start with role; include
  "Use when …" or "Use proactively when …" so discovery works in Cursor.
model: fast
readonly: true
---
```

| Field | Notes |
|--------|--------|
| `name` | Stable id; lowercase, hyphens. |
| `description` | Shown in picker; include trigger phrases. |
| `model` | Prefer `fast` for planning/read-only roles; `inherit` if it must follow parent model (see `obsidian-memory-splitter.md`). |
| `readonly` | `true` if the agent must not edit files (typical for splitters, verifiers, planners). Omit or `false` only if you explicitly want write access. |

## Body structure (recommended)

1. **Role** — one short paragraph (what the subagent *is*).
2. **When invoked** or **Mission** — numbered steps (what it *does*).
3. **Rules** — hard constraints (paths, no file writes, no silent overwrites, etc.).
4. **Output** — fixed sections the parent agent can parse (see `obsidian-memory-splitter.md`, `obsidian-converter-package.md`).

Keep subagents **narrow**. If the content is long reference material, templates, or contracts, put that in a **skill** and keep the agent as a thin router.

## When to add a paired skill

Add `.cursor/skills/<skill-name>/SKILL.md` when:

- The workflow is reusable without a subagent invocation.
- You need extra files (`assets/`, `references/`) or a long checklist.

Keep the agent **handoff line** explicit, for example:

> For full steps and templates, open `.cursor/skills/obsidian-conversation-to-memory/SKILL.md` in this repo.

## Copy-paste template (agent only)

```markdown
---
name: <kebab-case-name>
description: >-
  <Role>. Use when <trigger>.
model: fast
readonly: true
---
You are <one-sentence role>.

## Mission
1. ...
2. ...

## Rules
- ...

## Output
Return exactly these sections:

### Section A
- ...

### Section B
- ...
```

## Copy-paste template (skill only)

```markdown
---
name: <skill-name>
description: >-
  <What it teaches>. Use when <trigger>.
---
# <Title>

## When to use
- ...

## Steps
1. ...

## Safety
- ...
```

## Verify before commit

- [ ] Frontmatter parses (no stray `---` inside body without closing).
- [ ] `description` mentions when to use the agent/skill.
- [ ] Read-only agents never imply they will edit the repo.
- [ ] Paths reference this repo’s real layout (`AGENTS.md`, `app/`, `.cursor/`).

## Portable bundle note

Subagents under `.cursor/agents/` that ship with the Obsidian converter are listed in `.cursor/skills/cursor-obsidian-converter-package/SKILL.md`. Repo-only helpers (like this authoring skill) should **not** be added there unless you intentionally expand the vendored bundle.
