# Contributing & local development

> **Generated**: 2026-03-28 (`/update-docs`)  
> **Primary SSOT**: `obsidian-memory-plugin/package.json` (npm scripts), `.env.example` (env template).  
> **Contracts & Python commands**: `AGENTS.md`, `pyproject.toml`

---

## Repository layout (short)

| Area | Role |
|------|------|
| `app/` | FastAPI + MCP server (Python) |
| `tests/` | `pytest` |
| `obsidian-memory-plugin/` | Obsidian plugin (TypeScript, npm scripts) |
| `docs/` | Runbooks, policies, plans |

There is **no** `package.json` at the repository root; npm scripts live under the plugin directory only.

---

## Development workflow

1. **Clone** and create a virtualenv (Python 3.11–3.13).
2. **Install** Python deps: `pip install -e .[dev]` (optional MCP: `pip install -e .[mcp]` per `AGENTS.md`).
3. **Configure** env: copy `.env.example` → `.env` and set paths/token (see below).
4. **Run** API locally: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` (`AGENTS.md`).
5. **Plugin** (optional): `cd obsidian-memory-plugin` → `npm install` → `npm run dev` or `npm run build`.

Long-term memory curation workflow for Cursor is documented in:

- `docs/CURSOR_SAVE_MEMORY_PRACTICAL_GUIDE.md`
- `docs/plans/PLAN_MANUAL_MEMORY_WORKFLOW.md`

---

## npm scripts (`obsidian-memory-plugin/package.json`)

Scripts are defined without per-key comments in `package.json`. Descriptions below follow the `scripts` commands and `description` of the package.

| Script | Command | Description |
|--------|---------|-------------|
| `dev` | `node esbuild.config.mjs` | Plugin dev build / watch via esbuild (`esbuild.config.mjs`). |
| `build` | `node esbuild.config.mjs production` | Production bundle for the Obsidian plugin. |
| `check` | `tsc --noEmit` | Typecheck only (no emit). |

**Package metadata**: `"description": "Obsidian plugin scaffold for hybrid memory curation"` — same `package.json`.

Run from plugin root:

```bash
cd obsidian-memory-plugin
npm install
npm run check
npm run build
```

---

## Environment variables (from `.env.example`)

Values below are **templates only**; never commit real tokens or production vault paths.

| Variable | Purpose | Format / notes |
|----------|---------|----------------|
| `VAULT_PATH` | Filesystem root of the Obsidian vault the server reads/writes | Path (repo default `./vault` in example) |
| `INDEX_DB_PATH` | SQLite index DB file path (derived index; rebuildable) | Path (example `./data/memory_index.sqlite3`) |
| `MCP_API_TOKEN` | Bearer token for `/mcp` (and related writer defaults unless overridden) | Long random string; replace placeholder |
| `TIMEZONE` | Timezone string for date handling | Example: `Asia/Dubai` |
| `OBS_VAULT_NAME` | Vault name segment for `obsidian://` links in MCP responses | Example: `mcp_obsidian_vault` |

**Not listed in `.env.example` but supported** by `app/config.py` for hardened/deploy setups (set via real `.env` or host env): e.g. `MCP_ALLOWED_HOSTS`, `MCP_ALLOWED_ORIGINS`, `MCP_HMAC_SECRET`, `CHATGPT_MCP_WRITE_TOKEN`, `CLAUDE_MCP_WRITE_TOKEN`, Railway-style `RAILWAY_*` URLs. See `app/config.py` and `docs/PRODUCTION_RAILWAY_RUNBOOK.md`.

---

## Testing procedures

### Python

From repo root (after `pip install -e .[dev]`):

| Step | Command |
|------|---------|
| Tests | `pytest -q` |
| Lint | `ruff check .` |
| Format check | `ruff format --check app tests` |

Coverage policy: `pyproject.toml` (`fail_under = 85` for coverage reports).

### Plugin

From `obsidian-memory-plugin/`:

```bash
npm run check
```

Build verification: `npm run build`.

---

## Changing contracts

`AGENTS.md` lists **Ask Before Changing** items (auth, `/mcp`, tool schemas, vault layout, etc.). Plan or review before PRs that touch those surfaces.

---

## Related docs

| Doc | Use |
|-----|-----|
| `AGENTS.md` | Tool names, data paths, commands |
| `docs/RUNBOOK.md` | Deploy, health, rollback (this generation) |
| `docs/INSTALL_WINDOWS.md` | Windows setup |
| `docs/MASKING_POLICY.md` | Sensitive content handling |
