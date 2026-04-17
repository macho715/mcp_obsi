# Feature Specification: Local Research Assistant Phase 2 Search Quality + Candidate Review UI

Feature ID: local-research-assistant-phase-2-search-quality-candidate-review-ui
Created: 2026-04-17
Status: Draft
Owner: Local Research Assistant
Input: `docs/superpowers/plans/2026-04-17-local-research-assistant-phase-2-search-quality-candidate-review-ui-plan.md`
Last Updated: 2026-04-17
Version: v0.1.0

## Summary

### Problem

Local Research Assistant Phase 1 can answer directly from Everything search results, but users cannot review or correct the candidate file set before Copilot or fallback analysis. This can lower answer quality when Everything returns noisy, vanished, cache, or tool-generated paths.

### Goals

- G1: Improve candidate search quality before document extraction and Copilot packet creation.
- G2: Let the user preview, include, and exclude candidate files in the local web UI.
- G3: Analyze only the selected candidates for `ask` and `find-bundle` selected flows.
- G4: Preserve existing Phase 1 direct `ask` and `find-bundle` APIs.
- G5: Keep all writes out of Obsidian/wiki and under `runtime/research` only when saving is explicitly requested.

### Non-Goals

- NG1: Do not add Obsidian/wiki upload or memory writes.
- NG2: Do not add file delete, move, rename, edit, or download endpoints.
- NG3: Do not expose the local web server beyond loopback.
- NG4: Do not add new feature modes such as `versions`, `inspect-excel`, `brief-folder`, `compare-documents`, or `audit-evidence`.
- NG5: Do not introduce local LLM, Ollama, or full text indexing database dependencies.
- NG6: Do not change MCP tool schemas, auth behavior, or standalone-package internals.

## User Scenarios & Testing

### User Story 1 - Preview Search Candidates Before Analysis (Priority: P1)

The user enters a question or topic and previews candidate files before any Copilot or fallback analysis runs.

Why this priority: candidate quality directly controls answer quality and reduces noisy Copilot packets.

Independent Test: call `POST /api/research/candidates` with a prompt and verify the response contains ranked candidates, metadata, and no saved report paths.

Acceptance Scenarios:

1. Given Everything HTTP is reachable, When the user previews candidates for `Globalmaritime MWS 13차`, Then the system returns a candidate list with `candidate_id`, `path`, `name`, `extension`, `score`, `rank_reason`, and `selected_by_default`.
2. Given the user previews candidates, When the preview completes, Then no files are written under `runtime/research`, `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.
3. Given Everything returns duplicate paths with different case, When preview is requested, Then the candidates list contains only one normalized candidate for that path.

### User Story 2 - Review And Edit Recommended Candidates (Priority: P1)

The user sees recommended candidates pre-selected in the browser and can remove noisy files or add relevant files before analysis.

Why this priority: the selected file set must remain user-controllable while keeping simple use fast.

Independent Test: use the web page or API contract test to confirm candidate rows include checkbox state and selected candidate payloads can be submitted to selected-analysis routes.

Acceptance Scenarios:

1. Given preview candidates are returned, When the UI renders them, Then each visible row includes a checkbox, filename, path, extension, score, rank reason, and status.
2. Given a candidate is low-value because it is in `.cursor`, `.codex`, cache, build, or pytest temp path, When the UI renders candidates, Then the candidate is either not selected by default or is visibly penalized.
3. Given the user unchecks a candidate, When selected analysis is submitted, Then that candidate is not extracted and is not included in the Copilot or fallback evidence packet.

### User Story 3 - Analyze Selected Candidates For Ask (Priority: P1)

The user runs `ask-selected` using only the selected candidates from the preview result.

Why this priority: question answering is the primary workflow, and selected evidence should improve trust and relevance.

Independent Test: submit selected candidates to `POST /api/research/ask-selected` and verify only submitted candidates appear in `sources`.

Acceptance Scenarios:

1. Given two selected candidates and one excluded candidate, When `ask-selected` runs, Then the response `sources` contains only the two selected candidates.
2. Given Copilot proxy is unavailable, When `ask-selected` runs, Then the system returns fallback findings with source paths and a warning rather than a 500 error.
3. Given `save=false`, When `ask-selected` completes, Then no Markdown or JSON report file is written.
4. Given `save=true`, When `ask-selected` completes, Then the report is written only under `runtime/research/answers`.

### User Story 4 - Analyze Selected Candidates For Find Bundle (Priority: P1)

The user runs `find-bundle-selected` using only selected candidates.

Why this priority: file bundle quality depends on excluding duplicate, stale, unrelated, or temporary files.

Independent Test: submit selected candidates to `POST /api/research/find-bundle-selected` and verify `sources`, `core_files`, and fallback grouping are based only on selected candidates.

Acceptance Scenarios:

1. Given selected candidates contain a DOCX and a PDF, When `find-bundle-selected` runs, Then the response returns `mode=find-bundle`, selected `sources`, and bundle group fields.
2. Given selected candidates are empty, When `find-bundle-selected` is submitted, Then the API returns a client error with a clear message.
3. Given a selected file vanishes before extraction, When selected analysis runs, Then the system marks that source as `limited` and continues with remaining selected candidates.

### User Story 5 - Preserve Phase 1 Direct Flows (Priority: P2)

Existing direct `ask` and `find-bundle` endpoints continue to work for users who do not need manual candidate review.

Why this priority: Phase 2 must be additive and must not break existing usage.

Independent Test: run existing service and web tests for `POST /api/research/ask` and `POST /api/research/find-bundle`.

Acceptance Scenarios:

1. Given the Phase 2 changes are present, When the existing `ask` endpoint is called, Then it returns a source-backed answer or fallback response using the original request shape.
2. Given the Phase 2 changes are present, When the existing `find-bundle` endpoint is called, Then it returns a bundle or fallback response using the original request shape.

### Edge Cases

- EC1: Everything returns a path that no longer exists; the system penalizes or marks it without crashing.
- EC2: Everything returns `.cursor`, `.codex`, `.venv`, cache, build, or pytest temp paths; the system penalizes or does not preselect them.
- EC3: Candidate filename or content contains credential-like text; the system skips or blocks it according to existing credential hard-stop rules.
- EC4: Copilot proxy is unavailable; selected analysis returns fallback output and warning.
- EC5: Copilot proxy returns 422 or non-JSON; selected analysis returns fallback output and warning.
- EC6: The user submits no selected candidates; the API returns a client error.
- EC7: `save=false` is set; no report files are written.
- EC8: Browser UI receives a degraded health status; the UI still permits preview and fallback analysis.

## Requirements

### Functional Requirements

- FR-001: The system MUST provide a candidate preview service that returns ranked candidates without running Copilot analysis.
- FR-002: The system MUST expose `POST /api/research/candidates` for candidate preview.
- FR-003: Candidate preview responses MUST include `mode`, `prompt`, `candidates[]`, and `warnings[]`.
- FR-004: Each candidate MUST include `candidate_id`, `path`, `name`, `extension`, `score`, `rank_reason`, `selected_by_default`, and `status`.
- FR-005: Candidate IDs MUST be deterministic for the same normalized path and candidate context within a preview response.
- FR-006: The system MUST improve query generation for mixed Korean/English prompts by preserving meaningful tokens and phrase-like terms.
- FR-007: The system MUST improve ranking using filename match, path match, extension priority, recency metadata, file existence, and low-value path penalties.
- FR-008: The system MUST penalize or avoid default selection for `.cursor`, `.codex`, `.venv`, cache, build, `$Recycle.Bin`, and pytest temporary paths.
- FR-009: The system MUST preserve existing `POST /api/research/ask` behavior.
- FR-010: The system MUST preserve existing `POST /api/research/find-bundle` behavior.
- FR-011: The system MUST expose `POST /api/research/ask-selected`.
- FR-012: The system MUST expose `POST /api/research/find-bundle-selected`.
- FR-013: Selected-analysis requests MUST accept a selected candidate payload rather than requiring server-side candidate session state.
- FR-014: Selected-analysis requests MUST reject empty candidate selections with a client error.
- FR-015: Selected-analysis responses MUST include only selected candidates in `sources`.
- FR-016: Selected analysis MUST extract only selected candidate files.
- FR-017: If selected extraction fails for a candidate, the system MUST mark that candidate as `limited` and continue processing remaining candidates.
- FR-018: If Copilot fails during selected analysis, the system MUST return fallback output with a warning instead of returning a server error.
- FR-019: The browser UI MUST show a candidate review panel with include/exclude controls.
- FR-020: The browser UI MUST show rank score and rank reason for each candidate.
- FR-021: The browser UI MUST allow the user to analyze selected candidates.
- FR-022: With `save=false`, preview and selected analysis MUST write no report files.
- FR-023: With `save=true`, selected `ask` reports MUST be written only under `runtime/research/answers`.
- FR-024: With `save=true`, selected `find-bundle` reports MUST be written only under `runtime/research/bundles`.
- FR-025: The system MUST NOT write to `vault/wiki`, `vault/memory`, or `vault/mcp_raw` in Phase 2.

### Non-Functional Requirements

- NFR-001 (Compatibility): Phase 2 MUST be additive and preserve Phase 1 direct endpoints and request shapes.
- NFR-002 (Security/Locality): The web server MUST remain loopback-only.
- NFR-003 (Security): The system MUST NOT add file download, delete, move, rename, edit, or upload actions.
- NFR-004 (Security): Credential-like content MUST remain a hard skip or block according to the existing guard.
- NFR-005 (Reliability): Vanished, inaccessible, malformed, or unsupported candidate files MUST NOT crash preview or selected analysis.
- NFR-006 (Reliability): Copilot unavailable, 422, or non-JSON response states MUST return fallback output and warnings.
- NFR-007 (Observability): Candidate responses MUST include enough rank/status information for the user to understand why a file is recommended or penalized.
- NFR-008 (Testability): Candidate preview, selected analysis, ranking, save behavior, and no-wiki behavior MUST be covered by focused tests.
- NFR-009 (Maintainability): New APIs SHOULD reuse `scripts/local_research_service.py` service boundaries rather than duplicating search/extract/Copilot logic in the web module.

## Key Entities / Data

- `CandidatePreviewRequest`: prompt, mode, scope, max_candidates.
- `ResearchCandidate`: candidate_id, path, name, extension, size, modified_at, score, rank_reason, selected_by_default, status.
- `SelectedAnalysisRequest`: prompt or topic, mode, selected_candidates[], scope, save.
- `ResearchResult`: existing answer or bundle response with `sources`, `warnings`, and optional saved paths.

Relationships:

- A `CandidatePreviewRequest` produces zero or more `ResearchCandidate` records.
- A `SelectedAnalysisRequest` contains one or more selected `ResearchCandidate` records.
- A selected `ask` request produces an answer result.
- A selected `find-bundle` request produces a bundle result.

## Interfaces & Contracts

### `POST /api/research/candidates`

Purpose: return reviewable candidates without running Copilot analysis and without saving reports.

Request fields:

- `prompt`: string, required.
- `mode`: `ask` or `find-bundle`, required.
- `scope`: string, optional, default `all`.
- `max_candidates`: integer, optional.

Response fields:

- `mode`
- `prompt`
- `candidates[]`
- `warnings[]`

### `POST /api/research/ask-selected`

Purpose: answer a question using only selected candidates.

Request fields:

- `question`: string, required.
- `selected_candidates[]`: required, non-empty.
- `scope`: string, optional.
- `save`: boolean, optional.

Response: same general shape as existing `ask`, with `sources` limited to selected candidates.

### `POST /api/research/find-bundle-selected`

Purpose: build a file bundle using only selected candidates.

Request fields:

- `topic`: string, required.
- `selected_candidates[]`: required, non-empty.
- `scope`: string, optional.
- `save`: boolean, optional.

Response: same general shape as existing `find-bundle`, with `sources` limited to selected candidates.

## Assumptions & Dependencies

### Assumptions

- A1: Phase 2 uses the existing Phase 1 files `scripts/local_research_service.py` and `scripts/local_research_web.py`.
- A2: Selected-analysis APIs receive selected candidate payloads rather than depending on server-side preview sessions.
- A3: Candidate preview should avoid full document extraction unless a lightweight status check is required.
- A4: Candidate IDs are deterministic for a preview response and are not intended as long-term persistent IDs.
- A5: Existing direct `ask` and `find-bundle` flows remain useful and should stay available.

### Dependencies

- D1: Everything HTTP on loopback, currently expected at `http://127.0.0.1:8080`.
- D2: Standalone Copilot proxy on loopback, currently expected at `http://127.0.0.1:3010`, optional for fallback behavior.
- D3: Existing extraction helpers in `scripts/local_wiki_extract.py`.
- D4: Existing credential detection behavior from repo utilities.
- D5: Existing focused test framework using pytest and FastAPI TestClient.

## Success Criteria

### Measurable Outcomes

- SC-001: `POST /api/research/candidates` returns HTTP 200 with at least `candidate_id`, `path`, `score`, and `selected_by_default` for each candidate when Everything provides results.
- SC-002: Candidate preview with `save=false` writes zero files under `runtime/research`, `vault/wiki`, `vault/memory`, and `vault/mcp_raw`.
- SC-003: `ask-selected` with two selected candidates returns HTTP 200 and includes exactly those selected candidate paths in `sources`.
- SC-004: `find-bundle-selected` with selected candidates returns HTTP 200 and includes only selected candidate paths in `sources`.
- SC-005: Empty selected candidates for selected-analysis endpoints return a client error.
- SC-006: Existing `ask` and `find-bundle` focused tests continue to pass.
- SC-007: Vanished candidate path test passes without a server error.
- SC-008: Copilot unavailable selected-analysis smoke returns fallback output with a warning and no server error.
- SC-009: Focused service/web tests pass with `.\.venv\Scripts\python.exe -m pytest tests\test_local_research_service.py tests\test_local_research_web.py -q`.
- SC-010: Local-wiki regression and local-research tests pass together with the documented focused regression command.
- SC-011: Focused ruff check passes for touched service, web, and test files.
- SC-012: Focused ruff format check passes for touched service, web, and test files.

## Open Questions & Clarifications

### Open Questions

- Q1: Should the UI keep the direct one-click `Run` path visible after candidate review is added, or should review-first become the default screen? Current plan recommends auto-selected candidates with manual edits.
- Q2: Should candidate preview perform any lightweight existence/status checks, or should it stay metadata-only until selected analysis? Current spec assumes preview may include status but should avoid full extraction.

### Clarifications Log

- 2026-04-17 Session:
  - Q: Which Phase 2 UX option is preferred?
  - A: Plan recommends Option 3, auto-select recommended candidates while allowing manual changes.
  - Q: Should Phase 2 write to Obsidian/wiki?
  - A: No. `vault/wiki`, `vault/memory`, and `vault/mcp_raw` writes are out of scope.

## Risks & Mitigations

- R1: Ranking changes may reorder results unexpectedly. Mitigation: add deterministic ranking tests and preserve direct endpoint compatibility.
- R2: Candidate IDs may be treated as persistent IDs. Mitigation: document them as deterministic preview identifiers, not long-term IDs.
- R3: Candidate preview and selected analysis may drift if server-side sessions are used. Mitigation: selected requests carry candidate payloads.
- R4: UI may become confusing if direct run and review run compete. Mitigation: default to recommended candidate review and keep direct run secondary if retained.
- R5: Everything may return vanished paths. Mitigation: penalize or mark them and continue.
- R6: Copilot may be unavailable or return 422. Mitigation: keep fallback output and warnings.
- R7: Local path display may expose sensitive path information on screen. Mitigation: keep server loopback-only and avoid public exposure.

## Traceability

| Item | Links to |
|---|---|
| User Story 1 | FR-001, FR-002, FR-003, FR-004, FR-006, FR-007, SC-001, SC-002 |
| User Story 2 | FR-008, FR-019, FR-020, FR-021, NFR-007 |
| User Story 3 | FR-011, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-022, FR-023, SC-003, SC-005, SC-008 |
| User Story 4 | FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-022, FR-024, SC-004, SC-005, SC-008 |
| User Story 5 | FR-009, FR-010, NFR-001, SC-006 |
| No-wiki boundary | FR-025, SC-002 |
| Reliability boundary | NFR-005, NFR-006, SC-007, SC-008 |

## Reviewer Checklist

- [ ] Every P1 user story has an independent test path.
- [ ] Every selected-analysis route has empty-selection handling.
- [ ] Candidate preview has no persistent write side effects.
- [ ] `save=false` behavior is testable.
- [ ] `vault/wiki`, `vault/memory`, and `vault/mcp_raw` write bans are explicit.
- [ ] Existing direct endpoints are explicitly preserved.
- [ ] Success criteria are measurable.
- [ ] Remaining open questions are not implementation blockers.

## Changelog

- v0.2.0 (2026-04-17): Phase 2 candidate preview, selected-analysis routes, candidate review UI, no-wiki boundary, loopback-client guard, and fallback behavior implemented and verified.
- v0.1.0 (2026-04-17): Initial contract spec from Phase 2 plan.
