# Local Research Assistant Current Work Log

Date: 2026-04-17  
Workspace: `C:\Users\SAMSUNG\Downloads\mcp_obsi-main`

## Summary

This document records the Local Research Assistant work completed so far, the parts verified by tests, and the most recent interrupted changes that still need validation.

The current system is a loopback-only local web dashboard that searches local PC documents through Everything HTTP, extracts supported files, sends selected evidence to an AI provider, and renders a readable research report with raw JSON kept in a debug panel.

The main AI provider path is MiniMax M2.7 through the MiniMax Anthropic-compatible HTTPS API. Copilot standalone remains optional and is currently unavailable on `127.0.0.1:3010` in the observed dashboard health output.

## Important Distinction

`MiniMax: ok` in the dashboard originally meant that `MINIMAX_API_KEY` was present in the running process. It did not prove that a live model call had succeeded.

After the latest partial patch, MiniMax health is being split into:

- `key_configured`: local environment/key-load state.
- `live_smoke`: optional real API probe state.

The live smoke probe is designed to be disabled by default and enabled only with `MINIMAX_HEALTH_LIVE_SMOKE=1`, because probing the model on every health call can add latency and cost.

## Verified Work Completed Before The Latest Interruption

### U1 Job And Report Foundation

Implemented:

- In-process job registry.
- Job API:
  - `POST /api/research/jobs`
  - `GET /api/research/jobs/{job_id}`
  - `POST /api/research/jobs/{job_id}/cancel`
- Job states:
  - `queued`
  - `running`
  - `done`
  - `failed`
  - `cancel_requested`
  - `cancelled`
- Job progress stages:
  - `searching`
  - `extracting`
  - `building_packet`
  - `calling_provider`
  - `validating_response`
  - `saving`
  - `rendering_report`
- Report renderer for:
  - normal ask results
  - find-bundle results
  - invoice-audit structured data
- Dashboard controls:
  - `Preview Candidates`
  - `Run direct`
  - `Analyze Selected`
  - `Start job`
  - `Cancel job`
- Dashboard rendering:
  - report sections first
  - raw JSON in collapsed debug panel

Files involved:

- `scripts/local_research_jobs.py`
- `scripts/local_research_reports.py`
- `scripts/local_research_web.py`
- `scripts/local_research_service.py`
- `tests/test_local_research_jobs.py`
- `tests/test_local_research_reports.py`
- `tests/test_local_research_web.py`
- `docs/superpowers/plans/2026-04-17-local-research-assistant-u1-job-report-foundation-plan.md`
- `docs/superpowers/specs/2026-04-17-local-research-assistant-u1-job-report-foundation-spec.md`

Verified commands:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_research_jobs.py tests\test_local_research_reports.py tests\test_local_research_web.py tests\test_local_research_service.py -q
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_jobs.py tests\test_local_research_reports.py -q
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_extract.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py tests\test_local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_jobs.py tests\test_local_research_reports.py -q
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m ruff check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py scripts\local_research_jobs.py scripts\local_research_reports.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_jobs.py tests\test_local_research_reports.py
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m ruff format --check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py scripts\local_research_jobs.py scripts\local_research_reports.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_jobs.py tests\test_local_research_reports.py
```

Result: passed.

### MiniMax Compact Retry

Problem found:

- MiniMax health could be `ok`, but actual analysis could still fall back when MiniMax returned HTTP 500 or an invalid JSON shape.
- The first response sometimes required repair because the model included or omitted fields differently from the local schema.

Implemented:

- If MiniMax returns a provider request error, retry once with a compact packet.
- Compact retry limits the packet to:
  - first 3 sources
  - 1000 chars per `excerpt` or `snippet`
- If compact retry succeeds, the result remains `provider=minimax`.
- If compact retry fails, existing fallback behavior remains available.

Files involved:

- `scripts/local_research_providers.py`
- `tests/test_local_research_providers.py`

Verified commands:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_research_providers.py -q
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_research_providers.py tests\test_local_research_service.py tests\test_local_research_web.py -q
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_jobs.py tests\test_local_research_reports.py -q
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_extract.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py tests\test_local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_jobs.py tests\test_local_research_reports.py -q
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m ruff check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py scripts\local_research_jobs.py scripts\local_research_reports.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_jobs.py tests\test_local_research_reports.py
```

Result: passed.

```powershell
.\.venv\Scripts\python.exe -m ruff format --check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py scripts\local_research_jobs.py scripts\local_research_reports.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_jobs.py tests\test_local_research_reports.py
```

Result: passed.

### Real MiniMax Smoke

Dashboard was restarted at:

```text
http://127.0.0.1:8091/
```

Observed health:

```text
Route: ready | Active: minimax | Everything: ok | MiniMax: ok | Copilot: unavailable
```

Real MiniMax job smoke:

- Prompt: `dsv`
- Provider: `minimax`
- Model: `MiniMax-M2.7`
- `save=false`
- Result: `done`
- `ai_applied=true`
- Report generated.
- No answer file persisted because `save=false`.

Invoice audit smoke from the dashboard:

- Prompt: `TAX_INVOICE_AE70066475 세금계산서에서 공급자, 구매자, 금액, VAT, 총액을 추출`
- Provider: `minimax`
- Model: `MiniMax-M2.7`
- `ai_applied=true`
- Extracted invoice fields:
  - invoice number: `98256434`
  - issue date: `16.04.2026`
  - supplier: `Abu Dhabi Marine Operations And Services Company LLC`
  - buyer: `SAMSUNG C & T CORPORATION-ABU DHABI`
  - amount: `372,000.00`
  - VAT: `0.00`
  - total: `372,000.00`
  - currency: `USD`

This confirmed that MiniMax API analysis can work end-to-end in the dashboard.

## Most Recent Interrupted Work

The latest requested improvement had five parts:

1. Split MiniMax health into `key_configured` and `live_smoke`.
2. Strongly prioritize exact filename/entity matches such as `TAX_INVOICE_AE70066475`.
3. Strip leading PowerShell, `uvx`, and `markitdown` error logs from extracted `.md` text.
4. Clarify that `Start job` uses checked candidates as the selected-only packet when preview candidates exist.
5. Make the `Use tool loop` notice explicit that tool loop is planned/inactive in U1.

Work was interrupted after partial implementation. The following changes appear to have been written to disk, but they have not been fully verified after the interruption.

### Partially Applied Provider Health Changes

File:

- `scripts/local_research_providers.py`

Observed additions:

- `key_configured` object in `MiniMaxProvider.health()`.
- `live_smoke` object in `MiniMaxProvider.health()`.
- `_live_smoke_health()`.
- `MINIMAX_HEALTH_LIVE_SMOKE=1` opt-in behavior.
- `_safe_text()` to avoid returning raw secret-looking text in health errors.

Intended behavior:

- Without API key:
  - `status=unavailable`
  - `key_configured.status=missing`
  - `live_smoke.status=skipped`
- With API key and no live smoke:
  - `status=ok`
  - `key_configured.status=ok`
  - `live_smoke.status=not_run`
- With API key and `MINIMAX_HEALTH_LIVE_SMOKE=1`:
  - run a tiny live MiniMax request
  - return `live_smoke.status=ok` or `failed`
  - never include the API key in the response

Tests added but not fully verified after interruption:

- `test_minimax_health_masks_api_key`
- `test_minimax_health_live_smoke_can_probe_api_without_exposing_key`
- existing missing-key health tests were extended to expect `key_configured` and `live_smoke`.

### Partially Applied Ranking And Extraction Changes

File:

- `scripts/local_research_service.py`

Observed additions:

- `_exact_entity_match_score()`
- `_entity_key()`
- `exact filename/entity match` rank reason
- `_clean_extracted_text()`
- `_is_leading_conversion_noise_line()`

Intended behavior:

- Candidate names like `TAX_INVOICE_AE70066475.md` should outrank generic VAT or unrelated invoice-like files when the prompt includes `TAX_INVOICE_AE70066475`.
- Leading conversion logs like the following should be removed from the evidence packet:
  - `uvx : Installed ...`
  - `markitdown`
  - `NativeCommandError`
  - `CategoryInfo`
  - `FullyQualifiedErrorId`
  - `ps-script`
  - PowerShell location/error prefix lines
- The cleaned text should be what MiniMax receives in `packet.sources[].excerpt`.
- The dashboard source snippet should also start from the actual document content rather than the conversion log.

Tests added but not fully verified after interruption:

- `test_rank_candidates_strongly_prefers_exact_filename_entity_match`
- `test_md_extraction_strips_leading_powershell_uvx_markitdown_noise`

### Partially Applied Dashboard UI Changes

File:

- `scripts/local_research_web.py`

Observed additions:

- UI copy:
  - `Start job uses checked candidates only...`
  - `selected-only packet`
- Dashboard health formatting for MiniMax:
  - `key ok`
  - `live not run`
- Tool-loop notice changed to:
  - `Tool loop is not active in U1; the checkbox records intent only and no local tools are executed.`

Intended behavior:

- The dashboard should make clear that checked candidates are the only candidates sent to the provider when a preview list exists.
- The dashboard should not imply that U1 already performs true MiniMax tool-use loops.
- Health should distinguish key availability from actual live API probe status.

Tests added but not fully verified after interruption:

- `test_create_app_serves_working_interface` now expects selected-only copy and stronger inactive tool-loop copy.
- `test_health_route_adds_route_aware_dashboard_status_for_minimax_ready_copilot_unavailable` now expects `MiniMax: ok (key ok, live not run)`.

## Known Issues And Risks

### Unverified State After Interruption

The latest patch was interrupted by the user. Some edits are present on disk, but the full focused test suite was not run afterward.

Required next verification:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_research_providers.py tests\test_local_research_service.py tests\test_local_research_web.py -q
```

```powershell
.\.venv\Scripts\python.exe -m ruff check scripts\local_research_providers.py scripts\local_research_service.py scripts\local_research_web.py tests\test_local_research_providers.py tests\test_local_research_service.py tests\test_local_research_web.py
```

```powershell
.\.venv\Scripts\python.exe -m ruff format --check scripts\local_research_providers.py scripts\local_research_service.py scripts\local_research_web.py tests\test_local_research_providers.py tests\test_local_research_service.py tests\test_local_research_web.py
```

### Git Status Unavailable

`git status --short` previously failed because the current folder was not recognized as a Git repository:

```text
fatal: not a git repository (or any of the parent directories): .git
```

Therefore, file change tracking must be done through explicit file inspection rather than Git diff in this workspace.

### Copilot Unavailable

Copilot standalone is still unavailable at:

```text
127.0.0.1:3010
```

This does not block MiniMax provider operation, but it means `provider=auto` has fewer fallback options before deterministic fallback.

### Tool Loop Not Implemented

The `Use tool loop` checkbox is still an intent marker in U1. True local tool-use loops remain a later phase. The UI should continue to state this clearly.

### Candidate Ranking Still Needs Verification

Exact filename/entity match logic was partially implemented but not fully verified. The target behavior is:

- `TAX_INVOICE_AE70066475.md` should outrank unrelated VAT spreadsheets and generic invoice summaries when the query includes `TAX_INVOICE_AE70066475`.
- The rank reason should explicitly include `exact filename/entity match`.

### Extraction Cleanup Still Needs Verification

PowerShell and `uvx` conversion logs were observed inside `TAX_INVOICE_AE70066475.md` snippets. Cleanup logic was added, but it must be verified with the focused test and a dashboard smoke run.

## Recommended Next Step

Run the focused tests and ruff checks listed above. If they fail, fix only the focused failures in:

- `scripts/local_research_providers.py`
- `scripts/local_research_service.py`
- `scripts/local_research_web.py`
- related focused tests

After the focused checks pass, run the broader local research and local wiki regression suites:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_jobs.py tests\test_local_research_reports.py -q
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_extract.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py tests\test_local_research_schemas.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py tests\test_local_research_jobs.py tests\test_local_research_reports.py -q
```

Then restart the dashboard on:

```text
http://127.0.0.1:8091/
```

Manual smoke target:

1. Search `TAX_INVOICE_AE70066475`.
2. Confirm `TAX_INVOICE_AE70066475.md` ranks first or near first with exact-match reason.
3. Select only that candidate.
4. Run `Invoice Audit` with `provider=minimax`.
5. Confirm:
   - `AI applied via minimax / MiniMax-M2.7`
   - source snippet no longer starts with `uvx` or PowerShell error lines
   - extracted fields still include supplier, buyer, amount, VAT, total
   - tool-loop copy clearly says inactive/planned in U1

