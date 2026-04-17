# Local Research Assistant MiniMax M2.7 Provider Task

## Goal

Implement the MiniMax M2.7 provider expansion for Local Research Assistant in controlled phases.

The execution must add provider routing, MiniMax support, long-context packet handling, bounded tool use, and specialist modes without modifying the existing GitHub Copilot standalone package.

## Scope

### In Scope

- Add provider routing for `auto`, `minimax`, `minimax-highspeed`, `copilot`, and `fallback`.
- Add MiniMax health and analysis support.
- Preserve existing Copilot standalone fallback behavior.
- Add provider and specialist controls to the dashboard.
- Add bounded local tool execution.
- Add specialist output schemas and workflows.
- Add mocked tests and manual smoke instructions.
- Record verification evidence after implementation.

### Out of Scope

- Editing `standalone-package-20260311T084247Z-1-001`.
- Writing to `vault/wiki`, `vault/memory`, or `vault/mcp_raw`.
- Storing real API keys in repository files.
- Publicly exposing the dashboard.
- Building a vector database or background index daemon.

## Inputs & References

- Plan: `docs/superpowers/plans/2026-04-17-local-research-assistant-minimax-m27-provider-plan.md`
- Spec: `docs/superpowers/specs/2026-04-17-local-research-assistant-minimax-m27-provider-spec.md`
- Existing service: `scripts/local_research_service.py`
- Existing web UI/API: `scripts/local_research_web.py`
- Existing tests: `tests/test_local_research_service.py`, `tests/test_local_research_web.py`
- Existing extraction helpers: `scripts/local_wiki_extract.py`
- Existing Everything helper: `scripts/local_wiki_everything.py`
- Existing Copilot helper: `scripts/local_wiki_copilot.py`
- MiniMax docs:
  - `https://platform.minimax.io/docs/guides/text-generation`
  - `https://platform.minimax.io/docs/guides/text-m2-function-call`
  - `https://platform.minimax.io/docs/guides/text-ai-coding-tools`

## Deliverables

- `scripts/local_research_providers.py`
- `scripts/local_research_tools.py`
- Updated `scripts/local_research_service.py`
- Updated `scripts/local_research_web.py`
- `tests/test_local_research_providers.py`
- `tests/test_local_research_tools.py`
- Updated local research service/web tests
- Updated plan/spec/task verification evidence

## Acceptance Criteria

- `AC-1`: Provider router supports `auto`, `minimax`, `minimax-highspeed`, `copilot`, and `fallback`.
- `AC-2`: MiniMax provider reads API key only from environment variables.
- `AC-3`: Health response returns MiniMax status and does not expose secrets.
- `AC-4`: Copilot standalone package is not modified.
- `AC-5`: Selected analysis sends only selected or tool-approved files to external AI.
- `AC-6`: Tool executor rejects unauthorized paths.
- `AC-7`: Specialist modes are selectable from dashboard and API.
- `AC-8`: Invoice audit structured output includes source evidence.
- `AC-9`: `save=false` creates no repo or vault writes.
- `AC-10`: Focused tests, regression tests, ruff check, and format check pass.

## Definition of Done

- Implementation changes stay within the planned files unless a documented reason is added.
- Existing Copilot standalone behavior still works.
- Mock and fallback tests pass without MiniMax credentials.
- Manual MiniMax smoke is documented when `MINIMAX_API_KEY` is available.
- No API key or token value appears in logs, docs, fixtures, or responses.
- `vault/wiki`, `vault/memory`, and `vault/mcp_raw` no-write evidence is recorded.
- Plan, spec, and task documents include final verification evidence.

## Task List

- [x] T1: Create `scripts/local_research_providers.py`.
- [x] T2: Define provider protocol, provider result shape, and provider error shape.
- [x] T3: Move existing Copilot request logic into `CopilotProvider`.
- [x] T4: Implement `FallbackProvider`.
- [x] T5: Implement `MiniMaxProvider` health and basic analysis.
- [x] T6: Connect provider router to the `provider` request field.
- [x] T7: Remove direct Copilot calls from `local_research_service.py` analysis flow.
- [ ] T8: Add provider-specific packet budgets.
- [ ] T9: Add long-context packet builder.
- [x] T10: Create `scripts/local_research_tools.py`.
- [x] T11: Define `everything_search`, `extract_file`, `extract_table_preview`, `compare_selected_files`, and `build_citation` tools.
- [x] T12: Implement tool path allowlist and denylist.
- [x] T13: Implement max rounds, max files, and max character limits.
- [ ] T14: Implement MiniMax tool-use loop.
- [x] T15: Add dashboard provider selector.
- [x] T16: Add dashboard specialist mode selector.
- [x] T17: Extend dashboard health and status panel.
- [ ] T18: Add `Extract Fields` output schema.
- [ ] T19: Add `Invoice Audit` output schema.
- [ ] T20: Add `Execution Package Audit` output schema.
- [ ] T21: Add `Compare Documents` output schema.
- [x] T22: Add provider routing unit tests.
- [x] T23: Add MiniMax response parsing tests.
- [x] T24: Add tool executor guard tests.
- [x] T25: Add web API provider validation tests.
- [x] T26: Add no-write tests for `save=false`.
- [x] T27: Run focused local research tests.
- [x] T28: Run focused local wiki regression tests.
- [x] T29: Run focused ruff check and format check.
- [x] T30: Document manual smoke evidence.

## Dependencies & Risks

### Dependencies

- Everything HTTP must be available for live candidate search.
- Copilot standalone may be available for fallback testing.
- MiniMax real smoke requires `MINIMAX_API_KEY`.
- Existing document extraction behavior must remain stable.

### Risks

- MiniMax API key may be missing or region-specific.
- External API calls may expose selected document content.
- Tool-use loops can become slow or costly without strict limits.
- Malformed MiniMax JSON may break result rendering.
- Provider routing may accidentally regress existing Copilot behavior.
- Long-context packets may become too large without shrink behavior.

### Mitigations

- Keep MiniMax optional and environment-gated.
- Use mock tests for normal verification.
- Enforce selected/tool-approved file boundaries.
- Enforce packet, file, round, and timeout limits.
- Keep deterministic fallback available.
- Keep Copilot standalone package untouched.

## Security & Privacy

- Do not commit or print `MINIMAX_API_KEY`.
- Do not print GitHub, bearer, Copilot, or MiniMax tokens.
- Do not include API key values in health responses.
- Do not send arbitrary local paths to external AI.
- Do not send files outside selected or tool-approved paths.
- Do not write outputs to Obsidian vault paths.
- Keep dashboard and provider control plane loopback-only.
- Treat external AI provider use as explicit because selected document content may leave the machine.

## Evidence

### Required Commands

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py -q
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_extract.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py -q
```

```powershell
.\.venv\Scripts\python.exe -m ruff check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py
```

```powershell
.\.venv\Scripts\python.exe -m ruff format --check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py
```

### Manual Smoke

Run only when `MINIMAX_API_KEY` is configured outside the repo.

```text
GET  /api/research/health
POST /api/research/candidates
POST /api/research/ask-selected provider=minimax save=false
POST /api/research/find-bundle-selected provider=minimax save=false
POST /api/research/ask-selected provider=copilot save=false
```

### Evidence To Record After Implementation

- Test command outputs and pass/fail status.
- Focused ruff and format outputs.
- Manual MiniMax smoke result, if API key is available.
- `vault/wiki`, `vault/memory`, and `vault/mcp_raw` before/after file counts.
- Confirmation that the Copilot standalone package was not modified.

### Implementation Evidence 2026-04-17

- `.\.venv\Scripts\python.exe -m pytest tests\test_local_research_providers.py tests\test_local_research_tools.py -q` -> pass, 17 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_local_research_service.py -q` -> pass, 18 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_local_research_web.py -q` -> pass, 15 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py -q` -> pass, 50 passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_local_wiki_everything.py tests\test_local_wiki_extract.py tests\test_local_wiki_copilot.py tests\test_local_wiki_ingest.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py -q` -> pass, 81 passed.
- `.\.venv\Scripts\python.exe -m ruff check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py` -> pass.
- `.\.venv\Scripts\python.exe -m ruff format --check scripts\local_research_service.py scripts\local_research_web.py scripts\local_research_providers.py scripts\local_research_tools.py tests\test_local_research_service.py tests\test_local_research_web.py tests\test_local_research_providers.py tests\test_local_research_tools.py` -> pass.
- `GET http://127.0.0.1:8091/api/research/health` -> pass. Everything ok, Copilot ok, MiniMax unavailable because `MINIMAX_API_KEY` is not set, active provider `copilot`.
- `POST http://127.0.0.1:8091/api/research/ask` with `provider=fallback`, `save=false` -> pass. Response had empty `saved_markdown` and `saved_json`.
- `vault/wiki`, `vault/memory`, and `vault/mcp_raw` were not written by this implementation run.
- Existing Copilot standalone package directory was not modified by this implementation run.

## Change Log

- v0.1.0 (2026-04-17): Initial execution task document from MiniMax M2.7 provider spec.
