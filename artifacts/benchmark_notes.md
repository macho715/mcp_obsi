# Benchmark Notes — design-upgrade-loop skill-update run

**Run date:** 2026-04-14
**Target skill:** `design-upgrade-loop`
**Mode:** update (Cursor-only)
**Internet:** allowed
**Destructive:** not allowed

---

## 1. Cursor Skill Format (Official Docs — 2026-04-14)

Source: https://www.cursor.com/docs/context/skills  
Source: https://cursor.com/help/customization/skills

### Required changes identified

| Issue | Severity | Evidence |
|---|---|---|
| Missing YAML frontmatter (`name`, `description`) | **BLOCKER** | Cursor docs: "Frontmatter fields: `name` — Yes (required), `description` — Yes (required)" |
| `name` must match folder name exactly | **BLOCKER** | "Must match the parent folder name" |
| `agents/openai.yaml` is Codex-specific | WARNING | Cursor skill packaging docs list no `agents/` subdirectory; `openai.yaml` is not a Cursor artifact |
| Script invocation uses `python3` (bash style) | WARNING | Windows env uses `python`, not `python3` |
| Browser guidance does not mention `cursor-ide-browser` MCP | INFO | Cursor has native MCP browser tool; should be listed first |
| Description in inventory says "Codex" | WARNING | "Use when you want **Codex** to web-search..." — should say Cursor |

### Cursor skill discovery paths (confirmed)
- `.agents/skills/` (repo-level)
- `.cursor/skills/` (project-level)
- `~/.cursor/skills/` (global user-level)
- `~/.codex/skills/` ← **compatibility alias** — this is where `design-upgrade-loop` currently lives ✅

### Optional frontmatter fields
- `compatibility` — environment requirements (Python version, shell, etc.)
- `metadata` — arbitrary key-value pairs
- `disable-model-invocation: true` — slash-command-only mode
- `license` — license name or reference

---

## 2. Dashboard Design References 2026

Source: https://asappstudio.com/admin-dashboard-designs-2026/  
Source: https://omni.co/articles/best-dashboard-software-2026

### 2026 dashboard design trends
- Card-based KPI layout with drill-down interactivity
- Dark mode via CSS variables (oklch token system)
- Semantic data layer + governed metrics as trust signal
- shadcn/ui + Tailwind CSS as dominant stack for custom builds
- AI-assisted querying as table-stakes feature

### Recommended reference sites to add to `source-routing.md`
- **Tremor** (https://tremor.so) — chart-focused Next.js component library, rapid dashboard prototyping
- **Horizon UI PRO** (https://horizon-ui.com) — modern minimalist SaaS analytics dashboard, React + Tailwind
- **shadcn dashboard** (https://dub.sh/shadcn-dashboard) — copy-paste model, dark mode, data tables

---

## 3. Overlap Detection

From `artifacts/skill_inventory.json`:

| Skill | Overlap | Reuse opportunity |
|---|---|---|
| `uiux-studio` | UX flows and accessibility | Can reference for a11y scoring in scorecard |
| `playwright` | Browser automation scripts | `scripts/playwright_cli.sh` exists, Cursor prefers MCP over CLI |
| `screenshot` | OS-level capture | `scripts/take_screenshot.ps1` available on Windows if MCP unavailable |

No duplicate design-upgrade skill found. `design-upgrade-loop` is the only design benchmark skill.

---

## 4. Summary of required patches

1. Add YAML frontmatter: `name: design-upgrade-loop` + full description  
2. Add `compatibility` field: Python 3.8+, Windows PowerShell  
3. Replace "Codex" with "Cursor" in body text  
4. Fix script invocation: `python3` → `python`  
5. Add `cursor-ide-browser` MCP as first browser option  
6. Add 2026 dashboard references to `references/source-routing.md`  
7. Keep `agents/openai.yaml` but add a comment marking it Codex-only  

**No deletions required. All changes are additive or corrective.**
