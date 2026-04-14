# Operations runbook (index)

> **Generated**: 2026-03-28 (`/update-docs`)  
> **SSOT for env templates**: `.env.example` — production overlays: `docs/PRODUCTION_RAILWAY_RUNBOOK.md`

This file is a **hub** for operators. Detailed procedures stay in topic-specific runbooks to avoid duplication and drift.

---

## Deployment procedures

| Environment | Primary doc |
|-------------|-------------|
| Railway production | `docs/PRODUCTION_RAILWAY_RUNBOOK.md` |
| Railway preview | `docs/RAILWAY_PREVIEW_RUNBOOK.md` |
| VPS / self-managed | `docs/PRODUCTION_VPS_RUNBOOK.md`, `docs/VPS_EXECUTION_CHECKLIST.md`, `docs/VPS_COMMAND_SHEET.md` |
| Remote options matrix | `docs/REMOTE_DEPLOYMENT_MATRIX.md` |

**Typical shape (Railway)**: Docker image, volume for `/data`, env vars aligned with `.env.example` + host allowlist/HMAC as in production runbook.

---

## Monitoring and alerts

| Check | Endpoint / signal | Notes |
|-------|-------------------|--------|
| Process up | `GET /healthz` | Public health; separate from `/mcp` auth (`AGENTS.md`) |
| MCP | `POST /mcp` (with valid token) | Validate after deploy |
| Storage | Vault path + SQLite path | Must be persistent in production |

Formal metrics/alerting are not centralized in this repo doc-set; use your platform (Railway logs, uptime probe on `/healthz`, etc.).

---

## Memory / MCP operations (human workflow)

For **manual** long-term memory via Cursor (paste → `save_memory` → later `search`/`fetch`):

- `docs/CURSOR_SAVE_MEMORY_PRACTICAL_GUIDE.md`
- `docs/plans/PLAN_MANUAL_MEMORY_WORKFLOW.md`

---

## Common issues and fixes

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `401` / auth failures on `/mcp` | Wrong or missing `MCP_API_TOKEN` on client vs server | Align token; rotate if leaked (`PRODUCTION_RAILWAY_RUNBOOK` token guidance). |
| Writes not visible in Obsidian | Wrong `VAULT_PATH` or vault not synced | Confirm server env path matches the vault folder you open in Obsidian. |
| Search empty but files exist | Index DB stale or wrong `INDEX_DB_PATH` | Confirm path; rebuild index per plugin/server procedures if documented. |
| DNS rebinding / host errors (FastMCP) | `MCP_ALLOWED_HOSTS` / origins mismatch | Set allowlists per `app/config.py` + runbook env examples. |
| Plugin build fails | Node deps / TypeScript | `cd obsidian-memory-plugin && npm install && npm run check` |

Data handling and redaction: `docs/MASKING_POLICY.md`, `docs/PROBE_DATA_POLICY.md`.

---

## Rollback procedures

| Layer | Approach |
|-------|----------|
| **Deploy** | Re-promote previous Railway deployment / image tag (see `PRODUCTION_RAILWAY_RUNBOOK.md`). |
| **Config** | Revert env vars in hosting UI; restart service. |
| **Data** | Markdown under `VAULT_PATH` is SSOT; SQLite is derivative — restore vault from backup first, then re-index if your process requires it. |
| **Secrets** | Rotate `MCP_API_TOKEN` (and optional HMAC secret) if compromise suspected; update all MCP clients. |

Destructive purge / verification workflows (if applicable to your deployment): `docs/VERIFICATION_PURGE_RUNBOOK.md`.

---

## Quick reference — `.env.example` keys

`VAULT_PATH`, `INDEX_DB_PATH`, `MCP_API_TOKEN`, `TIMEZONE`, `OBS_VAULT_NAME` — see `docs/CONTRIB.md` for meanings.

---

## Related

| Doc | Topic |
|-----|-------|
| `docs/WRITE_TOOL_GATE.md` | Write tool policy |
| `docs/HMAC_PHASE_2.md` | Optional HMAC hardening |
| `docs/MCP_RUNTIME_EVIDENCE.md` | Runtime notes / evidence |
