# Local Research Assistant MiniMax M2.7 Provider Spec

## Summary

This specification defines the MiniMax M2.7 provider expansion for the Local Research Assistant.

The system must keep the existing GitHub Copilot standalone package unchanged while adding MiniMax M2.7 as a separate selectable provider. The completed feature must support provider routing, MiniMax long-context analysis, bounded tool use, and specialist document modes for local PC document research.

Fixed product decisions:

- Option C is selected: MiniMax M2.7 provider, long context, tool use, and specialist modes.
- The existing GitHub Copilot standalone package remains unchanged.
- MiniMax is added as a separate provider, not as a replacement for Copilot.
- Results are saved only under `runtime/research` when saving is enabled.
- `vault/wiki`, `vault/memory`, and `vault/mcp_raw` are not written by this feature.
- MiniMax API keys are read only from environment variables.

Primary references:

- Plan: `docs/superpowers/plans/2026-04-17-local-research-assistant-minimax-m27-provider-plan.md`
- Current dashboard service: `scripts/local_research_service.py`
- Current dashboard web app: `scripts/local_research_web.py`
- Existing focused tests: `tests/test_local_research_service.py`, `tests/test_local_research_web.py`

## User Scenarios & Testing

### Scenario 1: MiniMax M2.7 Selected Analysis

Given the dashboard is running locally and the user has selected candidate files,  
When the user chooses `MiniMax M2.7` and runs selected analysis,  
Then the request uses the MiniMax provider and returns a structured answer with source paths.

Test path:

- Mock `MiniMaxProvider`.
- Submit `POST /api/research/ask-selected` with `provider=minimax`.
- Assert the MiniMax mock receives the selected evidence packet.
- Assert the response includes `provider=minimax`, `model=MiniMax-M2.7`, and `sources`.

### Scenario 2: Auto Provider Fallback

Given the user chooses `Auto`,  
When MiniMax is unavailable,  
Then the system tries Copilot standalone before deterministic fallback.

Test path:

- Configure MiniMax mock to fail.
- Configure Copilot mock to pass.
- Submit selected analysis with `provider=auto`.
- Assert call order is MiniMax, then Copilot.
- Assert deterministic fallback is not used.

### Scenario 3: Fallback Only

Given the user chooses `Fallback Only`,  
When selected analysis runs,  
Then no external AI provider is called and the result contains deterministic evidence output.

Test path:

- Submit selected analysis with `provider=fallback`.
- Assert MiniMax and Copilot mocks are not called.
- Assert the response includes source-backed fallback findings.

### Scenario 4: Invoice Audit

Given a selected file such as `TAX_INVOICE_AE70066475.md`,  
When the user chooses `Invoice Audit`,  
Then the system extracts invoice fields with source evidence.

Test path:

- Use a local markdown fixture with invoice-like fields.
- Submit selected analysis with `analysis_mode=invoice-audit`.
- Assert output includes invoice number, issue date, supplier, buyer, amount, VAT, total, currency, and source evidence fields.

### Scenario 5: Find Bundle With Tool Use

Given the user chooses `Find Bundle` and enables tool use,  
When MiniMax requests additional search and extraction,  
Then the server executes only bounded approved tools and returns the final grouped file bundle.

Test path:

- Mock MiniMax to request `everything_search`.
- Mock MiniMax to request `extract_file` for a same-request Everything result.
- Assert final response includes core files, supporting files, duplicates or versions, and missing or gap hints.

### Scenario 6: Unauthorized Tool Path Rejection

Given MiniMax requests a path outside the selected, previewed, or same-request discovered files,  
When the tool executor validates the request,  
Then the read is rejected and no file content is returned.

Test path:

- Submit a tool request for `.git`, `.venv`, `node_modules`, `.codex`, `.cursor`, or a secret-looking path.
- Assert the tool result is a rejection with warning metadata.

### Scenario 7: Save False No-Write Boundary

Given selected analysis is called with `save=false`,  
When any provider is used,  
Then no files are written to `runtime/research`, `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.

Test path:

- Snapshot target directories.
- Run selected analysis with `save=false`.
- Assert snapshots are unchanged.

### Scenario 8: Copilot Standalone Preservation

Given the existing Copilot standalone proxy runs at `127.0.0.1:3010`,  
When MiniMax provider support is added,  
Then the standalone package directory is not modified and `provider=copilot` still uses the existing proxy.

Test path:

- Assert no implementation writes are made under `standalone-package-20260311T084247Z-1-001`.
- Mock or smoke `provider=copilot`.
- Assert Copilot provider endpoint remains the existing loopback endpoint.

## Requirements

### Functional Requirements

- `FR-001`: The system shall support a `provider` request field.
- `FR-002`: Supported provider values shall be `auto`, `minimax`, `minimax-highspeed`, `copilot`, and `fallback`.
- `FR-003`: `provider=minimax` shall use `MiniMax-M2.7`.
- `FR-004`: `provider=minimax-highspeed` shall use `MiniMax-M2.7-highspeed`.
- `FR-005`: `provider=copilot` shall use only the existing Copilot standalone proxy.
- `FR-006`: `provider=fallback` shall make no external AI calls.
- `FR-007`: `provider=auto` shall try MiniMax, then Copilot, then deterministic fallback.
- `FR-008`: The MiniMax API key shall be read only from `MINIMAX_API_KEY`.
- `FR-009`: The health response shall include MiniMax status without including the API key value.
- `FR-010`: Existing `ask`, `find-bundle`, `ask-selected`, and `find-bundle-selected` endpoints shall remain backward compatible.
- `FR-011`: A selected analysis request shall include only selected candidate files in the base evidence packet.
- `FR-012`: Tool-use mode shall execute only bounded local tools.
- `FR-013`: Tool-use extraction shall be limited to selected candidates, preview candidates, and same-request Everything results.
- `FR-014`: Tool-use shall not read `.git`, `.venv`, `node_modules`, `.codex`, `.cursor`, or secret-looking paths.
- `FR-015`: Tool-use loops shall enforce maximum rounds, files, and character limits.
- `FR-016`: The long-context packet builder shall apply provider-specific packet budgets.
- `FR-017`: MiniMax oversized or timeout failures shall trigger packet shrink retry or fallback behavior.
- `FR-018`: MiniMax raw thinking or reasoning content shall not be displayed in the dashboard.
- `FR-019`: The dashboard shall display a provider selector.
- `FR-020`: The dashboard shall display a specialist mode selector.
- `FR-021`: Specialist modes shall include `Extract Fields`, `Invoice Audit`, `Execution Package Audit`, and `Compare Documents`.
- `FR-022`: `Invoice Audit` output shall include invoice number, issue date, supplier, buyer, amount, VAT, total, currency, and source evidence.
- `FR-023`: `Compare Documents` output shall include differences and source-backed evidence.
- `FR-024`: `Execution Package Audit` output shall include core, supporting, and missing file groups.
- `FR-025`: Saved output shall be written only under `runtime/research`.
- `FR-026`: The feature shall not write to `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.
- `FR-027`: The existing standalone package directory shall not be modified.

### Non-Functional Requirements

- `NFR-001`: The dashboard and provider control plane shall remain loopback-only.
- `NFR-002`: API keys, bearer tokens, GitHub tokens, and MiniMax keys shall not be printed in logs, responses, docs, or fixtures.
- `NFR-003`: Mock tests shall pass without a real MiniMax API key.
- `NFR-004`: If MiniMax is unavailable, the system shall degrade through Copilot or deterministic fallback.
- `NFR-005`: AI-generated claims should include `source_path` whenever evidence is available.
- `NFR-006`: Content sent to external AI shall be limited to selected or tool-approved files.
- `NFR-007`: Each provider shall have timeout and packet size limits.
- `NFR-008`: Existing Phase 2 candidate review behavior shall remain available.
- `NFR-009`: Focused ruff check and focused format check shall pass for touched files.

## Assumptions & Dependencies

### Assumptions

- `MiniMax-M2.7` and `MiniMax-M2.7-highspeed` are available through the configured MiniMax account.
- International MiniMax usage defaults to `https://api.minimax.io/anthropic`.
- China-region accounts can switch the base URL by environment variable.
- External AI use is allowed for selected document content.
- MiniMax raw thinking content is useful for tool continuity but is not user-facing output.
- The implementation will proceed in phases and should not attempt all behavior in one patch.

### Dependencies

- Everything HTTP on loopback, currently expected at `http://127.0.0.1:8080`.
- Existing Local Research Assistant web service at `http://127.0.0.1:8090`.
- Existing Copilot standalone proxy at `http://127.0.0.1:3010`.
- Existing extraction helpers in `scripts/local_wiki_extract.py`.
- Existing candidate ranking and selected-analysis behavior in `scripts/local_research_service.py`.
- MiniMax API key provided outside the repository as `MINIMAX_API_KEY`.

## Success Criteria

- `SC-001`: `GET /api/research/health` returns `minimax`, `copilot`, `everything`, and `active_provider`.
- `SC-002`: A `provider=minimax` selected ask mock test calls `MiniMaxProvider`.
- `SC-003`: A `provider=copilot` selected ask mock test calls `CopilotProvider`.
- `SC-004`: A `provider=auto` fallback order test verifies MiniMax, then Copilot, then fallback.
- `SC-005`: A `provider=fallback` test verifies zero external AI calls.
- `SC-006`: An unauthorized tool path test verifies read rejection.
- `SC-007`: A max tool rounds test verifies clean stop and warning behavior.
- `SC-008`: A long packet shrink test verifies the packet stays within provider budget.
- `SC-009`: An invoice audit test returns structured fields for a `TAX_INVOICE_AE70066475.md` style fixture.
- `SC-010`: A `save=false` test verifies no-write behavior.
- `SC-011`: A Copilot standalone unchanged check passes.
- `SC-012`: Focused local research tests pass.
- `SC-013`: Focused local wiki regression tests pass.
- `SC-014`: Focused ruff check passes.
- `SC-015`: Focused ruff format check passes.
- `SC-016`: Real MiniMax smoke is recorded only when `MINIMAX_API_KEY` is available.

## Open Questions

- None blocking. MiniMax real smoke depends on a valid local `MINIMAX_API_KEY`.

## Clarifications Log

- 2026-04-17: User selected Option C: MiniMax provider plus long context, tool use, and specialist modes.
- 2026-04-17: Existing Copilot standalone package must remain unchanged.
- 2026-04-17: MiniMax may be used as an external AI provider for selected document content.
- 2026-04-17: Obsidian/wiki upload remains out of scope for this feature.

## Reviewer Checklist

- [ ] Every `FR-*` requirement has a corresponding test or manual verification path.
- [ ] MiniMax API key is not stored in source, docs, tests, or logs.
- [ ] Existing Copilot standalone package is unchanged.
- [ ] Provider routing preserves backward compatibility for existing endpoints.
- [ ] Tool-use path guard rejects unauthorized paths.
- [ ] `save=false` no-write behavior is tested.
- [ ] Dashboard exposes provider and specialist mode controls.
- [ ] Real MiniMax smoke is clearly marked manual and optional.

## Changelog

- v0.1.0 (2026-04-17): Initial contract spec from MiniMax M2.7 provider plan.
