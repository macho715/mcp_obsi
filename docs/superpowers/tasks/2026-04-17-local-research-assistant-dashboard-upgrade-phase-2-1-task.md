# Local Research Assistant Dashboard Upgrade Phase 2.1 Task

## Goal

Implement the Phase 2.1 Stability Patch for the Local Research Assistant Dashboard.

The work must make the current synchronous dashboard more accurate and reliable without adding job queues, WebSockets, full MiniMax tool-use loops, or report-style UI rendering.

## Scope

### In Scope

- Separate dependency health from route readiness.
- Make dashboard health/status text route-aware.
- Keep MiniMax usable even when Copilot is unavailable.
- Add app-level response schemas for `ask` and `find-bundle`.
- Validate MiniMax responses against those schemas.
- Add one MiniMax JSON repair retry when response parsing or schema validation fails.
- Preserve safe provider error details in warnings.
- Exclude MiniMax thinking content from user-facing and saved output.
- Improve candidate ranking with Everything metadata and duplicate/version annotations.
- Preserve `save=false` no-write behavior.
- Preserve existing endpoint compatibility.

### Out of Scope

- Job registry.
- Polling or WebSocket progress stream.
- Full MiniMax tool-use loop.
- Report-style UI rendering.
- Full specialist schemas for invoice, execution package, compare, and extract fields.
- Vector database or background indexing.
- Any Obsidian vault upload or memory writes.

## Inputs & References

- Plan: `docs/superpowers/plans/DASHBOARDUPGRADE.MD`
- Spec: `docs/superpowers/specs/2026-04-17-local-research-assistant-dashboard-upgrade-phase-2-1-spec.md`
- Provider code: `scripts/local_research_providers.py`
- Service code: `scripts/local_research_service.py`
- Web code: `scripts/local_research_web.py`
- Tool guard code: `scripts/local_research_tools.py`
- Existing provider tests: `tests/test_local_research_providers.py`
- Existing service tests: `tests/test_local_research_service.py`
- Existing web tests: `tests/test_local_research_web.py`
- Existing tool tests: `tests/test_local_research_tools.py`
- MiniMax API reference: `https://platform.minimax.io/docs/api-reference/text-anthropic-api`
- Everything HTTP reference: `https://ftp.voidtools.com/en-us/support/everything/http/`
- Pydantic validators: `https://docs.pydantic.dev/latest/concepts/validators/`

## Deliverables

- `scripts/local_research_schemas.py`
- Updated `scripts/local_research_providers.py`
- Updated `scripts/local_research_service.py`
- Updated `scripts/local_research_web.py`
- Updated `tests/test_local_research_providers.py`
- Updated `tests/test_local_research_service.py`
- Updated `tests/test_local_research_web.py`
- Updated task/spec evidence after verification

## Acceptance Criteria

- `AC-1`: Health response separates dependency status from route readiness.
- `AC-2`: Health response includes `everything`, `minimax`, `copilot`, `active_provider`, and route-ready metadata without secrets.
- `AC-3`: Dashboard health/status display shows MiniMax usable when Copilot is unavailable.
- `AC-4`: Provider HTTP error body details appear in warnings when safe.
- `AC-5`: Warnings and responses do not contain API keys, bearer tokens, or request headers.
- `AC-6`: MiniMax `ask` output is validated against an app-level schema.
- `AC-7`: MiniMax `find-bundle` output is validated against an app-level schema.
- `AC-8`: MiniMax malformed JSON or schema-invalid output triggers at most one repair retry.
- `AC-9`: Failed repair returns deterministic fallback with validation warnings.
- `AC-10`: MiniMax `thinking` block content is not exposed in result payloads or saved files.
- `AC-11`: Candidate ranking uses filename match, path match, extension, modified time, size presence, path penalties, and duplicate/version annotations.
- `AC-12`: Low-value paths such as `.cursor`, `.codex`, `.venv`, `node_modules`, pytest temp, cache, build, and dist receive rank penalties.
- `AC-13`: Candidate ranking exposes stable human-readable rank reasons.
- `AC-14`: `save=false` creates no files under `runtime/research`, `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.
- `AC-15`: Existing direct endpoint tests continue to pass.
- `AC-16`: Focused tests, focused regression, ruff check, and format check pass.

## Definition of Done

- All deliverables are implemented within the scoped files or deviations are documented.
- Direct endpoints remain backward compatible.
- No code writes to `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.
- MiniMax key values are not printed, stored, logged, or committed.
- Mock tests pass without a real MiniMax API key.
- Manual MiniMax smoke is optional and only records safe status/result metadata.
- Verification evidence is appended to this task document.

## Task List

- [x] T1: Create `scripts/local_research_schemas.py`.
- [x] T2: Add Pydantic schema for `AskResult`.
- [x] T3: Add Pydantic schema for `FindBundleResult`.
- [x] T4: Add normalization helpers for findings, source-backed objects, gaps, next actions, and warnings.
- [x] T5: Add tests for valid `ask` schema output.
- [x] T6: Add tests for valid `find-bundle` schema output.
- [x] T7: Add tests for schema-invalid MiniMax response.
- [x] T8: Add provider repair prompt test with first response invalid and second response valid.
- [x] T9: Implement one repair retry in `MiniMaxProvider`.
- [x] T10: Ensure repair retry does not print or include secrets.
- [x] T11: Add tests for text around JSON and fenced JSON extraction.
- [x] T12: Update JSON extraction to handle one safe JSON object inside surrounding text.
- [x] T13: Add tests proving MiniMax `thinking` blocks are ignored.
- [x] T14: Verify saved outputs do not include `thinking` content.
- [x] T15: Add route-readiness fields to service health.
- [x] T16: Update dashboard health/status text to distinguish dependencies from active route.
- [x] T17: Add web tests for MiniMax ok plus Copilot unavailable status display.
- [x] T18: Add ranking tests for Everything metadata, low-value path penalties, and duplicate/version annotations.
- [x] T19: Implement ranking v2 metadata and annotations in `local_research_service.py`.
- [x] T20: Preserve existing candidate fields and backward compatibility.
- [x] T21: Re-run `save=false` no-write tests and add coverage if missing.
- [x] T22: Run focused local research tests.
- [x] T23: Run focused local wiki regression tests.
- [x] T24: Run focused ruff check.
- [x] T25: Run focused ruff format check.
- [ ] T26: Optional manual MiniMax smoke with key configured. Health-only smoke was run; selected-file MiniMax calls were not run.
- [x] T27: Append implementation evidence to this task document.

## Dependencies & Risks

### Dependencies

- Python environment has Pydantic available.
- Everything HTTP remains loopback-only and reachable for live smoke.
- MiniMax real smoke requires local `MINIMAX_API_KEY`.
- Existing extraction helpers remain compatible.

### Risks

- MiniMax can return valid text that is semantically weak even if schema-valid.
- Repair retry can increase cost and latency.
- Candidate ranking changes can reorder existing tests unexpectedly.
- Health wording can break UI contract tests if not updated carefully.
- Duplicate/version grouping can become too aggressive if it collapses results.

### Mitigations

- Repair retry is limited to one attempt.
- Duplicate/version grouping is annotation-only for this phase.
- `auto` provider order remains unchanged for this phase unless user clarifies otherwise.
- `save=false` default behavior is not changed in this phase.
- Ranking tests use deterministic fixtures.

## Security & Privacy

- Do not print, log, or save `MINIMAX_API_KEY`.
- Do not store bearer tokens, Copilot tokens, or MiniMax keys in fixtures.
- Do not write to `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.
- Keep dashboard loopback-only.
- External AI content remains limited to selected or already extracted evidence packets.
- MiniMax `thinking` content is not user-facing and not persisted.
- Provider error details must be filtered to safe message text only.

## Evidence

### Required Commands

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py -q
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_extract.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py tests\test_local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py -q
```

```powershell
.\.venv\Scripts\python.exe -m ruff check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py scripts\local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_schemas.py
```

```powershell
.\.venv\Scripts\python.exe -m ruff format --check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py scripts\local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_schemas.py
```

### Optional Manual Smoke

Run only if `MINIMAX_API_KEY` is configured locally. Do not print the key.

```text
GET  /api/research/health
POST /api/research/ask-selected provider=minimax save=false
POST /api/research/find-bundle-selected provider=minimax save=false
```

### Evidence To Record After Implementation

- Focused test pass/fail output.
- Focused regression pass/fail output.
- Ruff check pass/fail output.
- Ruff format check pass/fail output.
- Manual MiniMax smoke status if run.
- Confirmation that no forbidden vault writes occurred.

### Parallel Execution Plan Added During Implementation

- Lead/main rollout: service health routing, candidate ranking annotations, integration verification, task evidence, dashboard restart.
- Worker A: schemas/provider lane for `scripts/local_research_schemas.py`, `scripts/local_research_providers.py`, `tests/test_local_research_schemas.py`, and `tests/test_local_research_providers.py`.
- Worker B: dashboard/web lane for `scripts/local_research_web.py` and `tests/test_local_research_web.py`.
- Validation lane: focused regression, ruff check, and ruff format check were run after integration.

### Implementation Evidence 2026-04-17

- Focused local research tests:
  `.\.venv\Scripts\python.exe -m pytest tests\test_local_research_schemas.py tests\test_local_research_providers.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_tools.py -q`
  - Result: pass, `60 passed`.
- Focused regression:
  `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_extract.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py tests\test_local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py -q`
  - Result: pass.
- Ruff check:
  `.\.venv\Scripts\python.exe -m ruff check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py scripts\local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_schemas.py`
  - Result: pass, `All checks passed!`.
- Ruff format check:
  `.\.venv\Scripts\python.exe -m ruff format --check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py scripts\local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_schemas.py`
  - Result: pass, `10 files already formatted`.
- Manual dashboard health smoke:
  `GET http://127.0.0.1:8091/api/research/health`
  - Result: pass, `Route: ready | Active: minimax | Everything: ok | MiniMax: ok | Copilot: unavailable`.
  - Note: no MiniMax analysis POST smoke was run, to avoid sending document content during this verification pass.
- No forbidden vault writes:
  - The implemented code path keeps persistent output under `runtime/research`; `save=false` coverage verifies no `runtime` write in the selected-analysis no-write test.

### Stabilization Evidence 2026-04-17

- MiniMax environment diagnostics:
  `.\.venv\Scripts\python.exe -m pytest tests\test_local_research_providers.py::test_minimax_health_masks_api_key tests\test_local_research_providers.py::test_minimax_health_reports_registered_key_not_loaded tests\test_local_research_providers.py::test_minimax_health_reports_missing_key -q`
  - Result: pass, `3 passed`.
- Dashboard MiniMax status explanation:
  `.\.venv\Scripts\python.exe -m pytest tests\test_local_research_web.py::test_health_route_adds_route_aware_dashboard_status_for_minimax_ready_copilot_unavailable tests\test_local_research_web.py::test_health_route_explains_minimax_restart_needed tests\test_local_research_web.py::test_health_route_explains_minimax_key_missing -q`
  - Result: pass, `3 passed`.
- Focused local research tests after stabilization:
  `.\.venv\Scripts\python.exe -m pytest tests\test_local_research_providers.py tests\test_local_research_web.py tests\test_local_research_service.py tests\test_local_research_schemas.py tests\test_local_research_tools.py -q`
  - Result: pass, `64 passed`.
- Focused regression after stabilization:
  `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_extract.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py tests\test_local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py -q`
  - Result: pass, `95 passed`.
- Dashboard restart smoke after stabilization:
  - Dashboard opened at `http://127.0.0.1:8091/`.
  - Health result: `Route: ready | Active: minimax | Everything: ok | MiniMax: ok | Copilot: unavailable`.

## Open Questions

- [NEEDS CLARIFICATION: Should `auto` skip Copilot by default when MiniMax is healthy, or keep the current MiniMax -> Copilot -> fallback order? Default for this task: keep current order.]
- [NEEDS CLARIFICATION: Should duplicate/version grouping only annotate candidates, or should grouped duplicates collapse into one visible row? Default for this task: annotate only.]
- [NEEDS CLARIFICATION: Should `save=false` become the dashboard default, or remain controlled by API/UI request fields? Default for this task: do not change default.]

## Change Log

- v0.2.0 (2026-04-17): Implemented Phase 2.1 stability patch, added parallel execution plan, and recorded verification evidence.
- v0.1.0 (2026-04-17): Initial task document from Phase 2.1 dashboard upgrade spec.
