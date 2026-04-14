# Spec: local-rag + standalone-package Doc Upgrade

## Context

The local-rag and standalone-package documentation has accumulated gaps and misplacements that reduce onboarding effectiveness and cause operational confusion. This upgrade addresses the two highest-impact issues without over-engineering cleanup of unrelated content.

## Upgrade Scope (Option B)

### 1. New: `docs/LOCAL_RAG_STANDALONE_GUIDE.md`

A single-page runbook for the complete local stack. Targets new users and daily operators.

**Content:**
- Stack overview: what each component does (Ollama / local-rag / mcp_obsidian / standalone-package)
- Port map table (11434 / 8010 / 8000 / 3010)
- Prerequisites checklist
- Step-by-step startup (3 approaches):
  - Click-to-run: `Start MStack.lnk` (newly created shortcut)
  - PowerShell one-liner: `.\start-all.ps1`
  - Manual step-by-step (each service)
- Health verification commands
- Browser access: `http://127.0.0.1:3010/`
- Quick sanity queries (copy-paste ready)
- Common symptoms table (CORS error, 401, 503, connection refused)
- Shutdown procedure (`.\stop-all.ps1` or `Stop MStack.lnk`)

**Style:** Markdown, Korean-language headers and UI labels (consistent with existing Korean docs in this repo), English code/command blocks.

### 2. Update: `local-rag/README.md`

**a. Readiness probe documentation**
- Document the `GET /api/internal/ai/chat-local/ready` endpoint (currently used in `standalone-package/src/local-rag.ts` but absent from README)
- Clarify relationship: `GET /health` = liveness, `GET /ready` = readiness for traffic

**b. Shared-secret header mapping**
- Add explicit section: `LOCAL_RAG_SHARED_SECRET` (local-rag env) ↔ `MYAGENT_LOCAL_RAG_TOKEN` (standalone env) ↔ `x-local-rag-token` (HTTP header)
- Show precedence: standalone uses `MYAGENT_LOCAL_RAG_TOKEN` if set, falls back to `LOCAL_RAG_SHARED_SECRET` if set, otherwise empty (open loopback only)

**c. Design spec reference**
- Add link to `docs/superpowers/specs/2026-04-08-local-rag-cache-and-guard-design.md` in a "Next Steps / Related Design" section

### 3. Delete: `standalone-package/docs/` misplacements

Remove 4 files that contain completely unrelated content (photo-to-video prompts):

- `standalone-package/docs/CLAUDE.md`
- `standalone-package/docs/GEMINI.md`
- `standalone-package/docs/QA-CHECKLIST.md`
- `standalone-package/docs/docs.md`

These are not referenced by any build step, index, or navigation. Deletion is safe.

### 4. Integrate: add design spec reference to `local-rag/README.md`

Add a "Related Design" section linking to `docs/superpowers/specs/2026-04-08-local-rag-cache-and-guard-design.md` so readers can find the cache/guard design without navigating to `docs/superpowers/specs/` manually.

## Verification Plan

- [ ] `docs/LOCAL_RAG_STANDALONE_GUIDE.md` exists and contains port map, startup commands, health checks
- [ ] `local-rag/README.md` mentions `/ready` endpoint and shared-secret precedence
- [ ] `local-rag/README.md` contains link to design spec
- [ ] 4 misplaced files are deleted from `standalone-package/docs/`
- [ ] `pnpm build` in standalone-package still passes after deletions
- [ ] All health endpoints still reachable on new paths (`C:\Users\jichu\Downloads\mcp_obsidian\local-rag`, etc.)

## Files Changed

| Action | File |
|--------|------|
| CREATE | `docs/LOCAL_RAG_STANDALONE_GUIDE.md` |
| UPDATE | `local-rag/README.md` |
| DELETE | `standalone-package/docs/CLAUDE.md` |
| DELETE | `standalone-package/docs/GEMINI.md` |
| DELETE | `standalone-package/docs/QA-CHECKLIST.md` |
| DELETE | `standalone-package/docs/docs.md` |

## Out of Scope

- Rewriting `INTEGRATION_ARCHITECTURE.md` or `AGENTS.md`
- Creating new `docs/` sub-navigation
- Modifying TypeScript source files
- Addressing `docs/CLAUDE_MCP.md` (root level) truncation
- Moving `start-all.ps1` / `stop-all.ps1` into a scripts/ subdirectory

## Dependencies

- `start-all.ps1`, `stop-all.ps1`, `make-shortcuts.ps1` (already committed in `chore/start-stop-scripts`)
- New shortcuts (`Start MStack.lnk`, `Stop MStack.lnk`) already created on Desktop and repo root

## Rollback

Delete the new file and restore deleted files from git history. The README changes are additive only.
