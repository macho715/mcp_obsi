# Local Research Assistant U1 Job and Report Foundation Spec

## Summary

This spec defines the U1 upgrade for the Local Research Assistant.

U1 adds a local job/progress pipeline and report-first result rendering while preserving all existing direct research endpoints. It does not implement the full MiniMax tool-use loop, WebSockets, prompt caching, vector search, or Obsidian vault writes.

Primary goal:

- Make long-running local research operations observable, cancellable before provider work, and readable as reports rather than raw JSON only.

Approved implementation basis:

- Plan: `docs/superpowers/plans/2026-04-17-local-research-assistant-u1-job-report-foundation-plan.md`
- Review: `docs/superpowers/reviews/2026-04-17-local-research-assistant-system-upgrade-review.md`

## User Scenarios & Testing

### Scenario 1: Start an ask job

Given the dashboard is open on loopback  
And the user enters a question  
And provider is `minimax` or `auto`  
When the user starts a job  
Then the API returns a `job_id` immediately  
And the job status starts as `queued` or `running`  
And the existing direct ask endpoint remains available.

Test coverage:

- Web API test for `POST /api/research/jobs`.
- Job registry lifecycle test.

### Scenario 2: Poll job progress

Given a job has been created  
When the dashboard polls `GET /api/research/jobs/{job_id}`  
Then the response includes `job_id`, `status`, `stage`, `progress`, `message`, `events`, `result`, and `error`  
And progress values are stable integers from `0` to `100`.

Test coverage:

- Web API test for polling response shape.
- Job state serialization test.

### Scenario 3: Successful job completes with report

Given a research job runs successfully  
When the job reaches `done`  
Then the job response includes the raw result payload  
And includes a report object with ordered sections  
And the dashboard renders the report before raw JSON.

Test coverage:

- Report renderer tests for ask, find-bundle, and invoice-audit.
- Web UI HTML/JS smoke assertions for report rendering and debug JSON.

### Scenario 4: Cancel before provider call

Given a job is queued or in a pre-provider stage  
When the user cancels the job  
Then the final job state becomes `cancelled`  
And no provider call is made after cancellation is observed.

Test coverage:

- Job registry cancellation test.
- Service/job runner test using a fake long pre-provider step.

### Scenario 5: Cancel during provider call

Given a job is already in `calling_provider`  
When the user cancels the job  
Then the job records `cancel_requested`  
And the final state is either `done`, `failed`, or `cancelled` depending on whether the provider call returns before cancellation can take effect  
And the UI explains that provider calls are soft-cancelled in U1.

Test coverage:

- Job state transition test for `cancel_requested`.

### Scenario 6: `save=false` job writes nothing

Given a job request has `save=false`  
When the job completes  
Then no files are created under `runtime/research` for that job  
And no files are created or modified under `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.

Test coverage:

- Job no-write test with sentinel directories.

### Scenario 7: Direct endpoints remain compatible

Given existing clients call direct endpoints  
When they call `ask`, `find-bundle`, `ask-selected`, or `find-bundle-selected`  
Then the response shape remains backward compatible  
And existing direct endpoint tests pass.

Test coverage:

- Existing `tests/test_local_research_web.py` and `tests/test_local_research_service.py`.

### Scenario 8: Tool loop checkbox is visible but not active

Given U1 does not implement the full MiniMax tool-use loop  
When the user checks `Use tool loop`  
Then the dashboard displays an explicit inactive/planned notice  
And the request remains a normal job/direct request.

Test coverage:

- Web UI text test for inactive tool-loop notice.

## Requirements

### Functional Requirements

- `FR-001`: The system shall provide `POST /api/research/jobs`.
- `FR-002`: `POST /api/research/jobs` shall accept `mode`, `prompt`, `selected_candidates`, `scope`, `max_candidates`, `save`, `provider`, `analysis_mode`, and `tool_use`.
- `FR-003`: `mode` shall support `ask` and `find-bundle`.
- `FR-004`: A job with non-empty `selected_candidates` shall route to the selected-candidate service flow.
- `FR-005`: A job with empty `selected_candidates` shall route to the search-based direct service flow.
- `FR-006`: Job creation shall return a `job_id` immediately without waiting for provider completion.
- `FR-007`: The system shall provide `GET /api/research/jobs/{job_id}`.
- `FR-008`: Job polling response shall include `job_id`, `status`, `stage`, `progress`, `message`, `events`, `result`, `report`, and `error`.
- `FR-009`: The system shall provide `POST /api/research/jobs/{job_id}/cancel`.
- `FR-010`: Cancellation shall work while a job is `queued`.
- `FR-011`: Cancellation shall work before the job enters `calling_provider`.
- `FR-012`: Cancellation during provider call shall be represented as `cancel_requested` or a safe final state.
- `FR-013`: The job registry shall support `queued`, `running`, `done`, `failed`, `cancel_requested`, and `cancelled`.
- `FR-014`: The job runner shall expose stages `queued`, `searching`, `ranking`, `extracting`, `building_packet`, `calling_provider`, `validating_response`, `saving`, `rendering_report`, `done`, `failed`, and `cancelled`.
- `FR-015`: The job runner shall append progress events with stage, progress, and message.
- `FR-016`: The report renderer shall convert ask results into sections for Answer, Key Findings, Evidence, Gaps, Next Actions, and Sources.
- `FR-017`: The report renderer shall convert find-bundle results into sections for Core Files, Supporting Files, Duplicates / Versions, Missing / Gap Hints, Next Actions, and Sources.
- `FR-018`: The report renderer shall convert invoice-audit results into Invoice Fields and Missing Fields sections when structured invoice data is present.
- `FR-019`: The report renderer shall include AI status based on `provider`, `model`, `ai_applied`, and `provider_status`.
- `FR-020`: The report renderer shall preserve raw result payload as debug data.
- `FR-021`: The dashboard shall display report sections before raw JSON.
- `FR-022`: The dashboard shall keep raw JSON available in a collapsed debug panel.
- `FR-023`: The dashboard shall poll job status until final state.
- `FR-024`: The dashboard shall show cancel control for active jobs.
- `FR-025`: The dashboard shall show that tool loop is planned/inactive in U1 when `tool_use=true`.
- `FR-026`: Direct endpoints shall remain available and backward compatible.
- `FR-027`: Job execution shall respect `save=false`.
- `FR-028`: Job results may be retained in memory for U1; persistent answer/bundle writes shall remain controlled by the existing service `save` behavior.

### Non-Functional Requirements

- `NFR-001`: Dashboard and job endpoints shall remain loopback-only.
- `NFR-002`: Job registry shall be in-process and runtime-only for U1.
- `NFR-003`: Job state mutation shall be protected against simple concurrent access races.
- `NFR-004`: Job IDs shall be opaque and not derived from file paths, prompts, or secret values.
- `NFR-005`: API keys, bearer tokens, Copilot tokens, and MiniMax keys shall not appear in logs, responses, docs, or fixtures.
- `NFR-006`: U1 shall not write to `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.
- `NFR-007`: U1 shall not introduce unbounded worker threads or processes.
- `NFR-008`: U1 shall not require a live MiniMax key for unit tests.
- `NFR-009`: U1 shall not require WebSockets.
- `NFR-010`: U1 shall keep existing direct endpoint tests passing.
- `NFR-011`: Report rendering shall be deterministic for the same input payload.
- `NFR-012`: Raw provider thinking content shall not be displayed or persisted by U1.

## Assumptions & Dependencies

- The current FastAPI dashboard remains the UI/API host.
- Existing `ResearchService` methods remain the source of truth for research execution.
- Existing provider routing remains unchanged for U1.
- Existing `save` behavior remains unchanged for direct and job flows.
- Polling interval defaults to 1000 ms.
- WebSockets are deferred until after polling is stable.
- Full MiniMax tool-use loop is deferred to U3.
- Search planner/ranking v3 is deferred to U2.
- Prompt caching and long-context packet builder are deferred to U4.
- Tests may use fake services/providers; live MiniMax smoke is optional.

## Success Criteria

- `SC-001`: `POST /api/research/jobs` returns `job_id`, `status`, and `created_at`.
- `SC-002`: `GET /api/research/jobs/{job_id}` returns the required job fields.
- `SC-003`: Successful ask job reaches `done` and includes result plus report.
- `SC-004`: Successful find-bundle job reaches `done` and includes result plus report.
- `SC-005`: Failed job reaches `failed` and includes safe error text.
- `SC-006`: Cancelled pre-provider job reaches `cancelled`.
- `SC-007`: Cancel during provider call records `cancel_requested` or a safe final state.
- `SC-008`: Report renderer returns deterministic sections for ask.
- `SC-009`: Report renderer returns deterministic sections for find-bundle.
- `SC-010`: Report renderer returns invoice fields for invoice-audit structured data.
- `SC-011`: Dashboard HTML/JS includes job start, poll, cancel, report rendering, and collapsed debug JSON behavior.
- `SC-012`: Dashboard displays inactive/planned notice when tool loop is checked in U1.
- `SC-013`: Existing direct endpoint tests pass.
- `SC-014`: `save=false` job path creates no files in `runtime/research`.
- `SC-015`: `save=false` job path does not modify `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.
- `SC-016`: Focused U1 tests pass.
- `SC-017`: Focused local research suite passes.
- `SC-018`: Focused regression suite passes.
- `SC-019`: Focused ruff check passes.
- `SC-020`: Focused ruff format check passes.

## Open Questions

- [NEEDS CLARIFICATION: Should completed job results be persisted under `runtime/research/jobs` when `save=true`, or kept memory-only? Default for U1: memory-only job registry; existing service save behavior still controls answer/bundle files.]
- [NEEDS CLARIFICATION: Should the polling interval be configurable? Default for U1: fixed 1000 ms.]
- [NEEDS CLARIFICATION: Should `Run direct` remain visible after job mode is added? Default for U1: yes.]

## Clarifications Log

- 2026-04-17: U1 scope is job/progress pipeline plus report UI only.
- 2026-04-17: Polling is selected before WebSockets.
- 2026-04-17: Full MiniMax tool-use loop is deferred to a later phase.
- 2026-04-17: Direct endpoints remain backward compatible.

## Reviewer Checklist

- [x] Scope excludes full tool-use loop.
- [x] Scope excludes WebSockets.
- [x] Scope excludes prompt caching and search planner v3.
- [x] Job API request and response shapes are explicit.
- [x] Job states and stages are explicit.
- [x] Cancellation semantics are explicit.
- [x] Report sections are explicit.
- [x] `save=false` no-write behavior is explicit.
- [x] Loopback-only boundary is preserved.
- [x] Secret handling is explicit.
- [x] Success criteria are measurable.

## Changelog

- v0.1.0 (2026-04-17): Initial U1 job/report foundation spec from approved plan.
- v0.2.0 (2026-04-17): U1 implemented; focused tests, regression, ruff, format, and dashboard smoke passed.
