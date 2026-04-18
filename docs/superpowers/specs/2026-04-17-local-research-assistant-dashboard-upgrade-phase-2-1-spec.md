# Local Research Assistant Dashboard Upgrade Phase 2.1 Spec

## Summary

This spec defines the Phase 2.1 Stability Patch for the Local Research Assistant Dashboard.

The goal is to make the existing synchronous dashboard accurate, predictable, and reliable before adding job queues, WebSockets, full MiniMax tool-use loops, or report-style rendering.

Current baseline:

- Dashboard: `http://127.0.0.1:8091`
- Everything HTTP: `http://127.0.0.1:8080`
- MiniMax provider: configured through `MINIMAX_API_KEY`
- Copilot standalone: optional fallback provider
- Persistent output: `runtime/research`

Hard boundaries:

- Do not write to `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.
- Do not store or print API keys.
- Keep the dashboard loopback-only.
- Keep existing direct endpoints backward compatible.

## User Scenarios & Testing

### Scenario 1: MiniMax Is Ready While Copilot Is Off

Given MiniMax health is ok and Copilot health is unavailable,  
When the user opens the dashboard,  
Then the dashboard shows MiniMax as available and does not present the whole app as blocked.

Testing:

- Mock health where `minimax.status=ok`, `copilot.status=unavailable`.
- Assert route readiness indicates MiniMax can run.
- Assert UI text distinguishes dependency status from active route status.

### Scenario 2: Provider Error Shows Safe Detail

Given MiniMax returns an HTTP error body with a provider error message,  
When the provider request fails,  
Then the warning includes the provider error message without exposing secrets.

Testing:

- Mock MiniMax HTTP error body such as `insufficient balance (1008)`.
- Assert warning contains the safe message.
- Assert API key value is not present in the warning or response.

### Scenario 3: MiniMax Returns Non-Schema JSON

Given MiniMax returns a JSON object that is parseable but does not match the app schema,  
When `provider=minimax` analysis runs,  
Then the system validates the response and performs one repair retry.

Testing:

- Mock first MiniMax response with missing or wrong fields.
- Mock second MiniMax response with valid schema.
- Assert exactly one repair retry occurs.
- Assert final result is schema-normalized.

### Scenario 4: MiniMax Returns Text Around JSON

Given MiniMax returns a text block with extra explanation or code fences around a JSON object,  
When the provider parses the response,  
Then the system extracts the JSON object when safe and validates it.

Testing:

- Mock response text with a fenced JSON object.
- Mock response text with leading/trailing text around one JSON object.
- Assert valid output is produced.

### Scenario 5: Thinking Blocks Are Not User-Facing

Given MiniMax returns `thinking` and `text` content blocks,  
When the provider processes the response,  
Then only text content needed for final JSON is parsed and no thinking content is shown or saved.

Testing:

- Mock content blocks containing `thinking` and `text`.
- Assert result does not contain thinking text.
- Assert saved JSON/Markdown do not contain thinking text.

### Scenario 6: Candidate Ranking Uses Metadata

Given Everything results include path, extension, size, and modified time,  
When candidates are ranked,  
Then supported clean paths, recent useful files, exact filename matches, and scoped paths are ranked above temp/cache/low-value paths.

Testing:

- Create mixed candidate fixtures:
  - clean markdown source
  - wiki analysis
  - temp pytest artifact
  - `.cursor` or `.codex` path
  - duplicate basename version
- Assert ranked order and rank reasons are stable.

### Scenario 7: Save False Writes Nothing

Given the user runs selected analysis with `save=false`,  
When analysis completes or falls back,  
Then no output file is created under `runtime/research`, `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.

Testing:

- Use temp directories with sentinel files.
- Run `ask-selected` and `find-bundle-selected` with `save=false`.
- Assert no new files are created.

### Scenario 8: Backward Compatibility

Given existing clients call `ask`, `find-bundle`, `ask-selected`, or `find-bundle-selected` without the new fields,  
When requests are submitted,  
Then responses preserve the existing top-level shape while adding optional metadata.

Testing:

- Re-run existing local research web/service tests.
- Assert existing required keys remain present.

## Requirements

### Functional Requirements

- `FR-001`: The health response shall separate dependency status from route readiness.
- `FR-002`: The health response shall include `everything`, `minimax`, `copilot`, and `active_provider`.
- `FR-003`: The dashboard shall display MiniMax status independently from Copilot status.
- `FR-004`: The dashboard shall not show the app as blocked when MiniMax is usable and Copilot is unavailable.
- `FR-005`: Provider warnings shall include safe provider error details when available.
- `FR-006`: Provider warnings shall not include API keys, bearer tokens, or request headers.
- `FR-007`: MiniMax `ask` responses shall be validated against an app-level schema.
- `FR-008`: MiniMax `find-bundle` responses shall be validated against an app-level schema.
- `FR-009`: MiniMax malformed or non-schema responses shall trigger at most one repair retry.
- `FR-010`: If repair retry fails, the system shall return a deterministic fallback plus validation warnings.
- `FR-011`: The provider parser shall ignore MiniMax `thinking` blocks for user-facing output.
- `FR-012`: MiniMax `thinking` content shall not be saved in runtime output files.
- `FR-013`: Candidate ranking shall use filename match, path match, extension, modified time, size presence, and path penalties.
- `FR-014`: Candidate ranking shall penalize low-value paths such as `.cursor`, `.codex`, `node_modules`, `.venv`, pytest temp paths, cache, build, and dist.
- `FR-015`: Candidate ranking shall expose human-readable rank reasons.
- `FR-016`: Candidate ranking shall support duplicate/version grouping metadata where basename or version patterns match.
- `FR-017`: `save=false` shall create no files.
- `FR-018`: All saved output shall remain under `runtime/research`.
- `FR-019`: Existing direct endpoints shall remain backward compatible.
- `FR-020`: Existing provider selection values shall remain `auto`, `minimax`, `minimax-highspeed`, `copilot`, and `fallback`.

### Non-Functional Requirements

- `NFR-001`: The dashboard and provider control plane shall remain loopback-only.
- `NFR-002`: The implementation shall not modify the Copilot standalone package.
- `NFR-003`: Mock tests shall pass without a real MiniMax API key.
- `NFR-004`: Real MiniMax smoke tests shall run only when `MINIMAX_API_KEY` is configured.
- `NFR-005`: No API key or token value shall appear in logs, docs, responses, or fixtures.
- `NFR-006`: The stability patch shall not introduce WebSocket or queue dependencies.
- `NFR-007`: The stability patch shall not write to `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.
- `NFR-008`: Focused pytest, focused regression, ruff check, and format check shall pass.
- `NFR-009`: Existing synchronous endpoints shall remain available while future job endpoints are out of scope.

### Out of Scope

- Job registry and progress polling.
- WebSocket streaming.
- Full MiniMax tool-use loop.
- Report-style UI rendering.
- Full specialist schema implementation for invoice, execution package, compare, and extract fields.
- Vector database or background index daemon.
- Obsidian wiki upload or memory writes.

## Assumptions & Dependencies

- Everything HTTP remains loopback-only at `http://127.0.0.1:8080`.
- The dashboard remains loopback-only at `http://127.0.0.1:8091` or equivalent local port.
- MiniMax external API is accessed through `MINIMAX_API_KEY`.
- MiniMax API may return `thinking` blocks in Anthropic-compatible responses.
- MiniMax API may return valid HTTP responses whose text does not match the app schema.
- Copilot standalone is optional for this phase.
- The repository already contains `scripts/local_research_service.py`, `scripts/local_research_web.py`, `scripts/local_research_providers.py`, and `scripts/local_research_tools.py`.
- Pydantic is available through the current Python environment.

## Success Criteria

- `SC-001`: `GET /api/research/health` returns dependency statuses and route readiness without secrets.
- `SC-002`: Dashboard health UI shows MiniMax usable even when Copilot is unavailable.
- `SC-003`: Mocked MiniMax HTTP error body appears as a safe warning detail.
- `SC-004`: Mocked MiniMax non-schema response triggers one repair retry.
- `SC-005`: Failed repair produces deterministic fallback with validation warnings.
- `SC-006`: Mocked MiniMax `thinking` block is excluded from user-facing result and saved output.
- `SC-007`: `ask` result schema validation test passes.
- `SC-008`: `find-bundle` result schema validation test passes.
- `SC-009`: Candidate ranking metadata test passes.
- `SC-010`: Candidate low-value path penalty test passes.
- `SC-011`: Candidate duplicate/version grouping metadata test passes.
- `SC-012`: `save=false` no-write test passes.
- `SC-013`: Existing direct endpoint compatibility tests pass.
- `SC-014`: Focused local research tests pass.
- `SC-015`: Focused local wiki regression tests pass.
- `SC-016`: Focused ruff check passes.
- `SC-017`: Focused ruff format check passes.
- `SC-018`: Manual MiniMax smoke is recorded only when key is configured and without printing the key.

## Open Questions

- [NEEDS CLARIFICATION: Should `auto` skip Copilot by default when MiniMax is healthy, or keep the current MiniMax -> Copilot -> fallback order?]
- [NEEDS CLARIFICATION: Should duplicate/version grouping only annotate candidates, or should grouped duplicates collapse into one visible row?]
- [NEEDS CLARIFICATION: Should `save=false` become the dashboard default, or remain controlled by API/UI request fields?]

## Clarifications Log

- 2026-04-17: User requested dashboard upgrade ideas using external documentation after 2026 references where available.
- 2026-04-17: Plan recommends Phase 2.1 Stability Patch before job, tool-use, and report UI work.
- 2026-04-17: User has previously stated not to upload to Obsidian for this workflow.

## Reviewer Checklist

- [ ] Requirements are measurable.
- [ ] No critical behavior depends on unstated assumptions.
- [ ] No requirement stores or prints secrets.
- [ ] No requirement writes to forbidden vault paths.
- [ ] Backward compatibility is covered.
- [ ] Test strategy covers provider, service, web, ranking, and no-write behavior.
- [ ] Out-of-scope items are explicit.

## Changelog

- v0.1.0 (2026-04-17): Initial Phase 2.1 Stability Patch spec derived from `docs/superpowers/plans/DASHBOARDUPGRADE.MD`.
